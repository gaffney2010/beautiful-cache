# type: ignore
import os
import time

import attr

import mysql.connector

# Omit this from mypy analysis because of the overload.
from overload import overload
import retrying
from selenium import webdriver

from constants import *
from shared_types import *
import tree_crawl


@attr.s()
class BcEngine(object):
    url_reader: UrlReader = attr.ib()
    database: Database = attr.ib()
    file_system: FileSystem = attr.ib()
    clock: Clock = attr.ib()

    @overload
    def append(self, row: Row) -> None:
        """Append to database with current time."""
        self.database._append(row, self.clock.now())

    @append.add
    def append(self, policy: Policy, url: Url, id: Id) -> None:
        self.append(make_row(policy, url, id))

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

    def __exit__(self, type, value, tb):
        """Clean-up on exit."""
        if self._driver:
            self._driver.quit()
        self._driver = None


class ConcreteUrlReader(UrlReader):
    def __init__(self):
        self.driver = WebDriver()
        super().__init__()

    @retrying.retry(wait_random_min=200, wait_random_max=400, stop_max_attempt_number=3)
    def _read_url_to_string_helper(help_url: Url, web_driver):
        web_driver.driver().get(str(help_url))
        time.sleep(DRIVER_DELAY_SEC)
        return web_driver.driver().page_source

    def _read(self, url: Url) -> Html:
        with WebDriver() as driver:
            page_text = _read_url_to_string_helper(url, self.driver)

        return Html(page_text)


class ConcreteDatabase(Database):
    """Must create database (`bc`) manually before using."""

    def __init__(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
        )
        super().__init__()

    def _make_table(self, policy: Policy) -> None:
        # If the table exists, do nothing.
        mycursor = self.db.cursor()
        mycursor.execute("SHOW TABLES;")
        for x in mycursor:
            if x == policy:
                return

        mycursor.execute(
            f"""
        CREATE TABLE {policy} (
            url TEXT NOT NULL,
            id TEXT NOT NULL,
            ts BIGINT NOT NULL,
            PRIMARY KEY(url, id)
        )
        """
        )

    # TODO: Should I return a success message or something?
    def _append(self, row: Row, ts: Time) -> None:
        self._make_table(row.policy)

        mycursor = self.db.cursor()
        mycursor.execute(
            f"""
        REPLACE INTO {policy} (url, id, ts)
        VALUES ({str(row.url)}, {str(row.id)}, {ts})
        """
        )
        self.db.commit()

    def pop(
        self, policy: Policy, record: Optional[CompactionRecord] = None
    ) -> Set[Url]:
        """Remove the records with the smallest timestamp and return.

        Additional recording to record if it's passed in.
        """
        self._make_table(policy)

        mycursor = self.db.cursor()
        mycursor.execute(
            f"""
        SELECT MIN(ts) my_min FROM {policy}
        """
        )
        my_min = mycursor.fetchone()[0]

        mycursor.execute(
            f"""
        SELECT DISTINCT url FROM {policy} WHERE ts={my_min}
        """
        )
        result = {Url(row[0]) for row in mycursor.fetchall()}

        mycursor.execute(
            f"""
        DELETE FROM {policy} WHERE ts={my_min}
        """
        )
        self.db.commit()

        return result

    def exists(self, policy: Policy, url: Url) -> bool:
        """Returns true if any records with the policy/url."""
        self._make_table(policy)

        mycursor = self.db.cursor()
        mycursor.execute(
            f"""
        SELECT * FROM {policy} WHERE url='{str(url)}';
        """
        )
        return mycursor.fetchone() is not None

    def pop_query(self, policy: Policy, url: Url) -> Dict[Id, Time]:
        """Deletes all records with the given policy/url.  Returns the IDs/timestamps
        for the deleted rows.
        """
        self._make_table(policy)

        mycursor.execute(
            f"""
        SELECT DISTINCT id, ts FROM {policy} WHERE url={str(url)}
        """
        )
        result = {Id(row[0]): Time(row[1]) for row in mycursor.fetchall()}

        mycursor.execute(
            f"""
        DELETE FROM {policy} WHERE url={str(url)}
        """
        )
        self.db.commit()

        return result

    def batch_load(self, rows: List[Tuple[Row, Time]]) -> None:
        """Put all these rows in the table with a timestamp"""
        for row, time in rows:
            self._append(row, time)


class ConcreteFileSystem(FileSystem):
    def size(self, policy: Policy) -> Bytes:
        """Returns total size of all data files in policy."""
        size = 0
        data_folder = os.path.join(policy, "data")
        for fn in os.listdir(data_folder):
            full_fn = os.path.join(data_folder, fn)
            if not os.path.isfile(full_fn):
                raise BcException(f"data folder contains unexpected folder: {full_fn}")
            size += os.path.getsize(full_fn)
        return Bytes(size)

    def _read_fn(self, policy: Policy, fn: Filename) -> str:
        with open(os.path.join(policy, fn), "r") as f:
            return f.read()

    def _write_fn(self, policy: Policy, fn: Filename, content: str) -> None:
        with open(os.path.join(policy, fn), "w") as f:
            f.write(content)

    def _exists_fn(self, policy: Policy, fn: Filename) -> bool:
        return os.path.exists(os.path.join(policy, fn))

    def _delete_fn(self, policy: Policy, fn: Filename) -> None:
        os.remove(os.path.join(policy, fn))


class ConcreteClock(Clock):
    def now(self) -> Time:
        # Round to the nearest ms
        return Time(int(time.monotonic * 1000))


ConcreteBcEngine = BcEngine(
    url_reader=ConcreteUrlReader(),
    database=ConcreteDatabase(),
    file_system=ConcreteFileSystem(),
    clock=ConcreteClock(),
)
