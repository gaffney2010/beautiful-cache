# TODO: Rename file (?) and set up testing make command.

from typing import Dict
import unittest

import bc
from shared_types import *


# Make functionless mocks.  This will all get replaced later.
class DeadDatabase(bc.Database):
    def append(self, row: Row) -> None:
        pass


class DeadFileSystem(bc.FileSystem):
    def read(self, fn: str) -> str:
        return ""

    def write(self, fn: str, content: str) -> None:
        pass


class DeadClock(bc.Clock):
    def __init__(self):
        pass

    def now(self) -> Time:
        """Even a broken clock is right exactly once in 1970."""
        return 0


# Takes a dict at init time.
class UrlReader(object):
    def __init__(self, internet: Dict[Url, Html]):
        self.internet = internet
        super().__init__()

    def read(self, url: Url) -> Html:
        return self.internet[url]


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
            url_reader=UrlReader(self.internet),
            database=DeadDatabase(),
            file_system=DeadFileSystem(),
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
            <td>row: 2, <a href="row1.png">cell:1</a></td>
            <td>row: 2, <a href="row1.png">cell:2</a></td>
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

        # TODO: Assert links are BS tag types
        self.assertEqual(link0.string, "cell:1")
        self.assertEqual(link3.string, "cell:2")
        # TODO: Assert links have expected hrefs

        # TODO: Assert that mock file has been written.
        # TODO: Assert DB records entered

