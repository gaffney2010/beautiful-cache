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
    def __init__(self, db: Optional[Dict[Tuple[Policy, Filename, Id], Time]] = None):
        self.db = db
        if self.db is None:
            self.db = dict()
        super().__init__()

    def _append(self, pfi: Pfi, ts: Time) -> None:
        self.db[pfi] = ts


class MockFileSystem(bc.FileSystem):
    def __init__(self, files: Optional[Dict[Filename, str]] = None):
        self.files = files
        if self.files is None:
            self.files = dict()
        super().__init__()

    def read(self, fn: Filename) -> str:
        try:
            result = self.files[fn]
        except KeyError:
            raise BcException(f"Trying to read mock file that doesn't exist: {fn}")

        return result

    def write(self, fn: Filename, content: str) -> None:
        self.files[fn] = content

    def exists(self, fn: Filename) -> bool:
        return fn in self.files

    def size(self, policy: Policy) -> Bytes:
        # Just count characters for tests.
        return Bytes(sum(len(content) for content in self.files.values()))


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
        self.db: Dict[Pfi, Time] = dict()

    def add_website(self, url: Url, html: Html) -> "PolicyEngineGenerator":
        self.internet[url] = html
        return self

    def add_file(self, fn: Filename, text: str) -> "PolicyEngineGenerator":
        self.files[fn] = text
        return self

    def add_request(
        self, policy: Policy, fn: Filename, id: Id, ts: Time
    ) -> "PolicyEngineGenerator":
        self.db[(policy, fn, id)] = ts
        return self

    def build(self) -> policy_engine_class.PolicyEngine:
        return policy_engine_class.PolicyEngine(
            url_reader=MockUrlReader(self.internet),
            database=MockDatabase(),
            file_system=MockFileSystem(self.files),
            clock=MockClock(),
        )
