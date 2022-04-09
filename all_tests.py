# TODO: Rename file (?) and set up testing make command.

import unittest

# TODO: Make package for bc
import bc


Html = str
Url = str


class PolicyEngineGenerator(object):
    """Will create a new mock PolicyEngine on build()
    
    Should include a mock file system, a mock Requests database, a mock webdriver, and a mock clock.
    """

    def __init__(self):
        pass

    def add_website(self, url: Url, html: Html) -> None:
        # TODO: Implement
        raise NotImplementedError

    # TODO: Make PolicyEngine
    def build(self) -> bc.PolicyEngine:
        # TODO: Implement
        raise NotImplementedError


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
        # TODO: Make BeautifulCache object
        soup = bc.BeautifulCache("test_url", "test_policy", engine=engine)
        cells = soup.find_all("td")
        # The materialize returns the usual BeautifulSoup objects.
        link0 = cells[0].find("a").materialize()
        link3 = cells[3].find("a").materialize()

        # TODO: Assert links are BS tag types
        # TODO: Assert links have expected content
        # TODO: Assert links have expected hrefs

        # TODO: Assert that mock file has been written.

