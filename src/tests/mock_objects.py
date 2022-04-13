from typing import Dict, Optional, Tuple

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
        return self.internet[url]


class MockDatabase(bc.Database):
    def __init__(self, db: Optional[Dict[Pui, Time]] = None):
        self.db = db
        if self.db is None:
            self.db = dict()
        super().__init__()

    def _append(self, pui: Pui, ts: Time) -> None:
        self.db[pui] = ts

    def _query(self, pui: Pui) -> Dict[Pui, Time]:
        result = dict()
        for k, v in self.db.items():
            if k.match(pui):
                result[k] = v
        return result

    def query(self, pui: Pui) -> List[Pui]:
        """Returns all the records in the database matching the passed pui upto
        wildcard characters.

        A wildcard character is a "*".  When the entire record is a wildcard, then that
        matches any record.  '*' as part of a longer string is not treated as a
        wildcard.
        """
        return list(self._query(pui).keys())

    def pop(self, policy: Policy) -> List[Pui]:
        """Remove the records with the smallest timestamp, and return."""
        if len(self.db) == 0:
            raise BcException("Trying to pop from an empty DB")

        match_policy = [(v, k) for k, v in self._query(pui(policy, "*", "*")).items()]
        min_time = sorted(match_policy)[0][0]
        result = [k for (v, k) in match_policy if v == min_time]

        # Removing motion
        for r in result:
            del self.db[r]

        return result


class MockFileSystem(bc.FileSystem):
    def __init__(self, files: Optional[Dict[Filename, str]] = None):
        self.files = files
        if self.files is None:
            self.files = dict()
        super().__init__()

    def read(self, policy: Policy, url: Url) -> str:
        try:
            result = self.files[self._key(policy, url)]
        except KeyError:
            raise BcException(f"Trying to read mock file that doesn't exist: {fn}")

        return result

    def write(self, policy: Policy, url: Url, content: str) -> None:
        self.files[self._key(policy, url)] = content

    def exists(self, policy: Policy, url: Url) -> bool:
        return self._key(policy, url) in self.files

    def size(self, policy: Policy) -> Bytes:
        # Just count characters for tests.
        return Bytes(sum(len(content) for content in self.files.values()))

    def delete(self, policy: Policy, url: Url) -> None:
        del self.files[self._key(policy, url)]


class MockClock(bc.Clock):
    def __init__(self):
        self.clock = Time(0)
        super().__init__()

    def tick(self, secs: Time = Time(1)) -> None:
        self.clock += secs

    def now(self) -> Time:
        return self.clock


class PolicyEngineGenerator(object):
    """Will create a new mock PolicyEngine on build()

    Should include a mock file system, a mock Requests database, a mock webdriver, and a mock clock.
    """

    def __init__(self):
        self.internet: Dict[Url, Html] = dict()
        self.files: Dict[Filename, str] = dict()
        self.db: Dict[Pui, Time] = dict()

    def add_website(self, url: Url, html: Html) -> "PolicyEngineGenerator":
        self.internet[url] = html
        return self

    def add_file(self, fn: Filename, text: str) -> "PolicyEngineGenerator":
        # Note that we could just have the mock file system key on URLs, but this is
        #  more realistic.
        self.files[fn] = text
        return self

    def add_request(
        self, policy: Policy, url: Url, id: Id, ts: Time
    ) -> "PolicyEngineGenerator":
        self.db[pui(policy, url, id)] = ts
        return self

    def build(self) -> policy_engine_class.PolicyEngine:
        return policy_engine_class.PolicyEngine(
            url_reader=MockUrlReader(self.internet),
            database=MockDatabase(self.db),
            file_system=MockFileSystem(self.files),
            clock=MockClock(),
        )
