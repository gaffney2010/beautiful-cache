import unittest

import bs4  # type: ignore

import bc
from tests.mock_objects import *
from shared_types import *


class TestEndToEnd(unittest.TestCase):

    # No compaction
    def test_happy_path(self):
        example_html = Html(
            """
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
        )

        engine = (
            PolicyEngineGenerator().add_website(Url("test_url"), example_html).build()
        )

        # Should be able to inject engines like this
        soup = bc.BeautifulCache(Url("test_url"), Policy("test_policy"), engine=engine)
        cells = soup.find_all("td")
        # The materialize returns the usual BeautifulSoup objects.
        engine.clock.tick()
        link0 = cells[0].find("a").materialize()
        engine.clock.tick()
        link3 = cells[3].find("a").materialize()

        self.assertTrue(isinstance(link0, bs4.element.Tag))
        self.assertTrue(isinstance(link3, bs4.element.Tag))
        self.assertEqual(link0.string, "cell:1")
        self.assertEqual(link3.string, "cell:2")
        self.assertEqual(link0["href"], "row1.png")
        self.assertEqual(link3["href"], "row2.png")

        # Check that a cached version of the library has been saved.
        self.assertDictEqual(engine.file_system.files, {"test_url.data": example_html})

        # Check that three Request records have been added to the db.  One for the
        #  URL load, and one for each request record.
        self.assertDictEqual(
            engine.database.db,
            {
                (Policy("test_policy"), Id("")): 0,
                # Timestamps determined by the number of clicks that have passed.
                (Policy("test_policy"), Id("html:0/body:0/table:0/tr:0/td:0/a:0")): 1,
                (Policy("test_policy"), Id("html:0/body:0/table:0/tr:1/td:1/a:0")): 2,
            },
        )

    def test_uses_cache(self):
        pass

    def test_reloads_on_missing_component_with_success(self):
        pass

    def test_reloads_on_missing_component_with_failure(self):
        pass

    # TODO: This needs to be done with a real db
    # def test_upserts_overwrite(self):
    #     pass
