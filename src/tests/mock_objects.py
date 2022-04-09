from typing import Dict, Tuple

import bc
from shared_types import *


# Takes a dict at init time.
class MockUrlReader(bc.UrlReader):
    def __init__(self, internet: Dict[Url, Html]):
        self.internet = internet
        super().__init__()

    def _read(self, url: Url) -> Html:
        return self.internet[url]


class MockDatabase(bc.Database):
    def __init__(self):
        self.db: Dict[Tuple[Policy, str], Time] = dict()
        super().__init__()

    def _append(self, policy: Policy, id: str, ts: Time) -> None:
        self.db[(policy, id)] = ts


class MockFileSystem(bc.FileSystem):
    def __init__(self):
        # TODO: Make type for file name
        self.files: Dict[str, str] = dict()

    def read(self, fn: str) -> str:
        try:
            result = self.files[fn]
        except KeyError:
            raise BcException(f"Trying to read mock file that doesn't exist: {fn}")

        return result

    def write(self, fn: str, content: str) -> None:
        self.files[fn] = content

    def exists(self, fn: str) -> bool:
        return fn in self.files


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

    def add_website(self, url: Url, html: Html) -> "PolicyEngineGenerator":
        self.internet[url] = html
        return self

    def build(self) -> bc.PolicyEngine:
        return bc.PolicyEngine(
            url_reader=MockUrlReader(self.internet),
            database=MockDatabase(),
            file_system=MockFileSystem(),
            clock=MockClock(),
        )
