import logging
import os
import time

import attr
import retrying  # type: ignore
from selenium import webdriver

from .constants import *
from .shared_types import *
from . import tree_crawl

DRIVER_DELAY_SEC = 3


@attr.s()
class BcEngine(object):
    url_reader: UrlReader = attr.ib()
    database: Database = attr.ib()
    file_system: FileSystem = attr.ib()
    clock: Clock = attr.ib()

    def append_row(self, row: Row) -> None:
        """Append to database with current time."""
        self.database._append(row, self.clock.now())

    def append(self, policy: Policy, url: Url, id: Id) -> None:
        self.append_row(make_row(policy, url, id))

    def read_url(self, policy: Policy, url: Url) -> Html:
        """Reads url, saving an access record to the database at the same time."""
        if self.file_system.exists(policy, url):
            return Html(self.file_system.read(policy, url))

        # Cast to soup then back, so as to erase whitespace
        untrimmed_html = self.url_reader._read(url)

        html = Html(tree_crawl.trim_html(untrimmed_html))

        self.append(policy, url, Id(""))  # Store the root in Requests db
        self.file_system.write(policy, url, html)  # Save

        return html


class WebDriver(object):
    """Used for convenient open and closing.
    This will handle closing for you, but will close as soon as the driver
    leaves scope.
    """

    def __init__(self):
        self._driver = None

    def __enter__(self):
        """We just need this, so that we can have the exit semantic."""
        return self

    def driver(self):
        """Get the main object, loading if necessary."""
        # Lazy load
        if self._driver is None:
            logging.debug("Initializing driver.")
            options = webdriver.FirefoxOptions()
            options.add_argument("--headless")
            self._driver = webdriver.Firefox(
                options=options,
                service_log_path="{}/geckodriver.log".format(LOGGING_DIR),
            )
            logging.debug("Finished initializing driver.")
        return self._driver

    def quit(self):
        """Clean-up on exit."""
        if self._driver:
            self._driver.quit()
        self._driver = None

    def __exit__(self, type, value, tb):
        """Clean-up on exit."""
        self.quit()


class ConcreteUrlReader(UrlReader):
    def __init__(self, driver):
        self.driver = driver
        super().__init__()

    @retrying.retry(wait_random_min=200, wait_random_max=400, stop_max_attempt_number=3)
    def _read_url_to_string_helper(self, help_url: Url, web_driver):
        web_driver.driver().get(str(help_url))
        time.sleep(DRIVER_DELAY_SEC)
        return web_driver.driver().page_source

    def _read(self, url: Url) -> Html:
        page_text = self._read_url_to_string_helper(url, self.driver)
        return Html(page_text)


class ConcreteDatabase(Database):
    """Must create database (`bc`) manually before using.  Assumes auto-commit or that
    users will commit."""

    def __init__(self, mysql_db):
        self.db = mysql_db
        self._policies = set()
        super().__init__()

    def _execute(self, cursor, query):
        logging.debug(query)
        cursor.execute(query)

    def _sanitize_policy(self, policy: Union[Policy, str]) -> str:
        """Should be idempotent"""
        return policy.replace("/", "_").replace("-", "_")

    def _make_table(self, policy: Union[Policy, str]) -> None:
        policy = self._sanitize_policy(policy)
        if policy in self._policies:
            return

        # TODO: Figure out how to make (url, id) a primary key.  (Too long.)
        cursor = self.db.cursor()
        self._execute(
            cursor,
            f"""
        CREATE TABLE IF NOT EXISTS {policy} (
            url TEXT NOT NULL,
            id TEXT NOT NULL,
            ts BIGINT NOT NULL
        );
        """,
        )

        self._policies.add(policy)

    # TODO: Should I return a success message or something?
    def __append(self, row: Row, ts: Time) -> None:
        """We can replace with REPLACE INTO after we get primary key working."""
        policy = self._sanitize_policy(row.policy)
        self._make_table(policy)

        cursor = self.db.cursor()
        self._execute(cursor, "BEGIN TRANSACTION;")
        self._execute(
            cursor,
            f"""
        DELETE FROM {policy} WHERE url='{str(row.url)}' and id='{str(row.id)}';
        """,
        )
        self._execute(
            cursor,
            f"""
        INSERT INTO {policy} (url, id, ts)
        VALUES ('{str(row.url)}', '{str(row.id)}', {ts});
        """,
        )
        self._execute(cursor, "COMMIT;")

    def _append(self, row: Row, ts: Time) -> None:
        self.__append(row, ts)

    def _pop_filter(
        self,
        policy: Union[Policy, str],
        priority: str,
        record: Optional[CompactionRecord] = None,
        other_filters: str = "",
    ) -> Set[Url]:
        policy = self._sanitize_policy(policy)
        self._make_table(policy)

        cursor = self.db.cursor()
        self._execute(cursor, "BEGIN TRANSACTION;")

        self._execute(
            cursor,
            f"""
        SELECT MIN(ts) my_min FROM {policy} WHERE 1=1{other_filters}
        """,
        )
        my_min = cursor.fetchone()[0]

        self._execute(
            cursor,
            f"""
        SELECT DISTINCT url FROM {policy} WHERE ts={my_min}{other_filters}
        """,
        )
        result = {Url(row[0]) for row in cursor.fetchall()}

        self._execute(
            cursor,
            f"""
        DELETE FROM {policy} WHERE ts={my_min}{other_filters}
        """,
        )
        self._execute(cursor, "COMMIT;")

        # Record, if record passed in.
        if record is not None:
            record.delete_through = my_min
            record.records_deleted += result

        return result

    def pop(
        self,
        policy: Union[Policy, str],
        priority: str,
        record: Optional[CompactionRecord] = None,
    ) -> Set[Url]:
        """Remove the records with the smallest timestamp and return.

        Additional recording to record if it's passed in.
        """
        if priority in ("root-first", "root-only"):
            if self.exists(policy, other_filters=f" AND id=''"):
                return self._pop_filter(
                    policy, priority, record, other_filters=f" AND id=''"
                )

        if priority in ("root-first", "fifo"):
            if self.exists(policy):
                return self._pop_filter(policy, priority, record)

        # Nothing left to pop
        return set()

    def exists(
        self,
        policy: Union[Policy, str],
        url: Optional[Url] = None,
        other_filters: str = "",
    ) -> bool:
        """Returns true if any records with the policy/url."""
        policy = self._sanitize_policy(policy)
        self._make_table(policy)

        url_filter = ""
        if url is not None:
            url_filter = f" AND url='{str(url)}'"

        cursor = self.db.cursor()
        self._execute(
            cursor,
            f"""
        SELECT * FROM {policy} WHERE 1=1{url_filter}{other_filters};
        """,
        )
        result = cursor.fetchone() is not None
        return result

    def pop_query(self, policy: Union[Policy, str], url: Url) -> Dict[Id, Time]:
        """Deletes all records with the given policy/url.  Returns the IDs/timestamps
        for the deleted rows.
        """
        policy = self._sanitize_policy(policy)
        self._make_table(policy)

        cursor = self.db.cursor()
        self._execute(cursor, "BEGIN TRANSACTION;")

        self._execute(
            cursor,
            f"""
        SELECT DISTINCT id, ts FROM {policy} WHERE url='{str(url)}'
        """,
        )
        result = {Id(row[0]): Time(row[1]) for row in cursor.fetchall()}

        self._execute(
            cursor,
            f"""
        DELETE FROM {policy} WHERE url='{str(url)}'
        """,
        )

        self._execute(cursor, "COMMIT;")

        return result

    # TODO: Even with current optimizations, this runs too slowly.
    def batch_load(self, rows: List[Tuple[Row, Time]]) -> None:
        """Put all these rows in the table with a timestamp"""
        for row, time in rows:
            self.__append(row, time)


class ConcreteFileSystem(FileSystem):
    def _make_dir(self, policy: Policy) -> None:
        # Make sure that the dirs exists
        if not os.path.exists(policy):
            os.makedirs(policy)
        if not os.path.exists(os.path.join(policy, "data")):
            os.makedirs(os.path.join(policy, "data"))

    def size(self, policy: Policy) -> Bytes:
        """Returns total size of all data files in policy."""
        self._make_dir(policy)

        size = 0
        data_folder = os.path.join(policy, "data")
        for fn in os.listdir(data_folder):
            full_fn = os.path.join(data_folder, fn)
            if not os.path.isfile(full_fn):
                raise BcException(f"data folder contains unexpected folder: {full_fn}")
            size += os.path.getsize(full_fn)
        return Bytes(size)

    def _read_fn(self, policy: Policy, fn: Filename) -> str:
        self._make_dir(policy)

        with open(os.path.join(policy, fn), "r") as f:
            return f.read()

    def _write_fn(self, policy: Policy, fn: Filename, content: str) -> None:
        self._make_dir(policy)

        with open(os.path.join(policy, fn), "w") as f:
            f.write(content)

    def _exists_fn(self, policy: Policy, fn: Filename) -> bool:
        self._make_dir(policy)

        return os.path.exists(os.path.join(policy, fn))

    def _delete_fn(self, policy: Policy, fn: Filename) -> None:
        self._make_dir(policy)

        os.remove(os.path.join(policy, fn))


class ConcreteClock(Clock):
    def now(self) -> Time:
        # Round to the nearest ms
        return Time(int(time.time() * 1000))


class LazyDatabase(ConcreteDatabase):
    """Append-only database that runs faster, but must manually commit.

    Must create database (`bc`) manually before using."""

    def __init__(self, mysql_db):
        self.buffer: List[Tuple[Row, Time]] = list()
        # TODO: Make a constant
        self.max_size = 100
        super().__init__(mysql_db)

    # TODO: Should I return a success message or something?
    def _append(self, row: Row, ts: Time) -> None:
        """We can replace with REPLACE INTO after we get primary key working."""
        self.buffer.append((row, ts))
        if len(self.buffer) >= self.max_size:
            self.batch_load(self.buffer)
            self.buffer = list()

    def commit(self) -> None:
        self.batch_load(self.buffer)
        self.buffer = list()


def bc_engine_factory(mysql_db, driver, lazy: bool) -> BcEngine:
    if lazy:
        raise NotImplementedError
        # TODO: Fix this cross-repo!!
        db = LazyDatabase(mysql_db)
    else:
        db = ConcreteDatabase(mysql_db)

    return BcEngine(
        url_reader=ConcreteUrlReader(driver),
        database=db,
        file_system=ConcreteFileSystem(),
        clock=ConcreteClock(),
    )
