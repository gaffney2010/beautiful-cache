from typing import Dict
import unittest

import bs4

import bc
from shared_types import *


# Make functionless mocks.  This will all get replaced later.
class DeadDatabase(bc.Database):
    def _append(self, policy: Policy, id: str, ts: Time) -> None:
        pass


class DeadClock(bc.Clock):
    def __init__(self):
        pass

    def now(self) -> Time:
        """Even a broken clock is right exactly once in 1970."""
        return 0


# Takes a dict at init time.
class MockUrlReader(bc.UrlReader):
    def __init__(self, internet: Dict[Url, Html]):
        self.internet = internet
        super().__init__()

    def _read(self, url: Url) -> Html:
        return self.internet[url]


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
            database=DeadDatabase(),
            file_system=MockFileSystem(),
            clock=DeadClock(),
        )


class TestStringMethods(unittest.TestCase):

    # No compaction
    def test_happy_path(self):
        example_html = """
        <html><body>
        <table>
        <tr>
            <td>row: 1, <a href="row1.png">cell:1</a></td>
            <td>row: 1, <a href="row1.png">cell:2</a></td>
        </tr>
        <tr>
            <td>row: 2, <a href="row2.png">cell:1</a></td>
            <td>row: 2, <a href="row2.png">cell:2</a></td>
        </tr>
        </table>
        </body</html>
        """

        engine = PolicyEngineGenerator().add_website("test_url", example_html).build()

        # Should be able to inject engines like this
        soup = bc.BeautifulCache("test_url", "test_policy", engine=engine)
        cells = soup.find_all("td")
        # The materialize returns the usual BeautifulSoup objects.
        link0 = cells[0].find("a").materialize()
        link3 = cells[3].find("a").materialize()

        self.assertTrue(isinstance(link0, bs4.element.Tag))
        self.assertTrue(isinstance(link3, bs4.element.Tag))
        self.assertEqual(link0.string, "cell:1")
        self.assertEqual(link3.string, "cell:2")
        self.assertEqual(link0["href"], "row1.png")
        self.assertEqual(link3["href"], "row2.png")

        # Check that a cached version of the library has been saved.
        self.assertDictEqual(engine.file_system.files, {"test_url": example_html})

        # TODO: Assert DB records entered
