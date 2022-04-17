from typing import Dict, Optional, Tuple
from wsgiref.headers import tspecials

import bc
import policy_engine_class
from shared_types import *


# Takes a dict at init time.
class MockUrlReader(bc.UrlReader):
    def __init__(self, internet: Optional[Dict[Url, Html]] = None):
        self.internet = internet
        if self.internet is None:
            self.interest = dict()
        super().__init__()

    def _read(self, url: Url) -> Html:
        return self.internet[str(url)]


class MockDatabase(bc.Database):
    def __init__(self, db: Optional[Dict[Row, Time]] = None):
        self.db = db
        if self.db is None:
            self.db = dict()
        super().__init__()

    def _append(self, row: Row, ts: Time) -> None:
        self.db[row] = ts

    def _query(self, policy: Policy, url: Optional[Url] = None) -> Dict[Row, Time]:
        result = dict()
        for k, v in self.db.items():
            if k.policy == policy and (url is None or k.get_url() == url):
                result[k] = v
        return result

    def exists(self, policy: Policy, url: Optional[Url] = None) -> bool:
        """Returns true if any records with the policy/url."""
        return len(self._query(policy, url)) > 0

    def pop(
        self, policy: Policy, record: Optional[CompactionRecord] = None
    ) -> Set[Url]:
        """Remove the records with the smallest timestamp and return the URLs.

        Additional recording to record if it's passed in.
        """
        if not self.exists(policy):
            raise BcException("Trying to pop from an empty DB")

        match_policy = [(v, k) for k, v in self._query(policy).items()]
        min_time = sorted(match_policy, key=lambda x: x[0])[0][0]
        result = [k for (v, k) in match_policy if v == min_time]

        # Removing motion
        for r in result:
            del self.db[r]

        # Record, if record passed in.
        if record is not None:
            record.delete_through = min_time
            record.records_deleted += result

        return {row.get_url() for row in result}

    def pop_query(self, policy: Policy, url: Url) -> Dict[Id, Time]:
        """Does the same as query, but removes the rows from the database.

        Also returns the timestamps with it.
        """
        result = self._query(policy, url)
        for k in result.keys():
            del self.db[k]
        return {Id(k.id): v for k, v in result.items()}

    def batch_load(self, rows: List[Tuple[Row, Time]]) -> None:
        """Put all these rows in the table with a timestamp"""
        for row in rows:
            row, ts = row
            self.db[row] = ts


class MockFileSystem(bc.FileSystem):
    def __init__(self, files: Optional[Dict[Filename, str]] = None):
        self.files = files
        if self.files is None:
            self.files = dict()
        super().__init__()

    def _read_fn(self, policy: Policy, fn: Filename) -> str:
        try:
            result = self.files[fn]
        except KeyError:
            raise BcException(f"Trying to read mock file that doesn't exist: {fn}")

        return result

    def _write_fn(self, policy: Policy, fn: Filename, content: str) -> None:
        self.files[fn] = content

    def _exists_fn(self, policy: Policy, fn: Filename) -> bool:
        return fn in self.files

    def size(self, policy: Policy) -> Bytes:
        # Just count characters for tests.
        return Bytes(
            sum(
                len(content)
                for fn, content in self.files.items()
                if fn.split("/")[0] == policy
            )
        )

    def _delete_fn(self, policy: Policy, fn: Filename) -> None:
        del self.files[fn]


class MockClock(bc.Clock):
    def __init__(self):
        self.clock = Time(0)
        super().__init__()

    def tick(self, secs: Time = Time(1)) -> None:
        self.clock += secs

    def now(self) -> Time:
        return self.clock


class BcEngineGenerator(object):
    """Will create a new mock BcEngine on build()

    Should include a mock file system, a mock Requests database, a mock webdriver, and a mock clock.
    """

    def __init__(self):
        self.internet: Dict[Url, Html] = dict()
        self.files: Dict[Filename, str] = dict()
        self.db: Dict[Row, Time] = dict()

    def add_website(self, url: Url, html: Html) -> "BcEngineGenerator":
        self.internet[str(url)] = html
        return self

    def add_file(self, fn: Filename, text: str) -> "BcEngineGenerator":
        # Note that we could just have the mock file system key on URLs, but this is
        #  more realistic.
        self.files[fn] = text
        return self

    def add_request(
        self, policy: Policy, url: Url, id: Id, ts: Time
    ) -> "BcEngineGenerator":
        self.db[make_row(policy, url, id)] = ts
        return self

    def build(self) -> policy_engine_class.BcEngine:
        return policy_engine_class.BcEngine(
            url_reader=MockUrlReader(self.internet),
            database=MockDatabase(self.db),
            file_system=MockFileSystem(self.files),
            clock=MockClock(),
        )
