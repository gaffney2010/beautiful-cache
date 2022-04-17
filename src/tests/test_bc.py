import unittest

import bs4  # type: ignore

import bc
from shared_types import *
from tests.mock_objects import *
import tree_crawl


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

        engine = BcEngineGenerator().add_website(Url("test_url"), example_html).build()

        # Should be able to inject engines like this
        soup = bc.BeautifulCache(Url("test_url"), Policy("test_policy"), engine=engine)
        cells = soup.find_all("td")
        # The materialize returns the usual BeautifulSoup objects.
        engine.clock.tick()
        link0 = cells[0].find("a").materialize()
        engine.clock.tick()
        link3 = cells[3].find("a").materialize()

        # TODO: Uncomment after we fix Ingredient
        # self.assertTrue(isinstance(link0, Ingredient))
        # self.assertTrue(isinstance(link3, Ingredient))
        self.assertEqual(link0.string, "cell:1")
        self.assertEqual(link3.string, "cell:2")
        self.assertEqual(link0["href"], "row1.png")
        self.assertEqual(link3["href"], "row2.png")

        # Check that a cached version of the html (after trimming) has been saved.
        self.assertDictEqual(
            engine.file_system.files,
            {"test_policy/test_url.data": tree_crawl.trim_html(example_html)},
        )

        # Check that three Request records have been added to the db.  One for the
        #  URL load, and one for each request record.
        self.assertDictEqual(
            engine.database.db,
            {
                make_row("test_policy", "test_url", ""): 0,
                # Timestamps determined by the number of clicks that have passed.
                make_row(
                    "test_policy",
                    "test_url",
                    "html:0/body:0/table:0/tr:0/td:0/a:0",
                ): 1,
                make_row(
                    "test_policy",
                    "test_url",
                    "html:0/body:0/table:0/tr:1/td:1/a:0",
                ): 2,
            },
        )

    def test_uses_cache(self):
        old_html = "<html><body><tag>OLD</tag></body></html>"
        new_html = Html("<html><body><tag>NEW</tag></body></html>")

        engine = (
            BcEngineGenerator()
            .add_file("test_policy/test_url.data", old_html)
            .add_website("test_url", new_html)
            .build()
        )

        soup = bc.BeautifulCache(Url("test_url"), Policy("test_policy"), engine=engine)
        self.assertEqual(soup.find("tag").materialize().string, "OLD")

        # Shouldn't have a request for the root, because I didn't reload.
        self.assertDictEqual(
            engine.database.db,
            {make_row("test_policy", "test_url", "html:0/body:0/tag:0"): 0},
        )

    def test_multiple_policies_happy_path(self):
        example_html_1 = Html("<html><body>Page 1</body</html>")
        example_html_2 = Html("<html><body>Page 2</body</html>")

        engine = (
            BcEngineGenerator()
            .add_website(Url("test_url_1"), example_html_1)
            .add_website(Url("test_url_2"), example_html_2)
            .build()
        )

        _ = bc.BeautifulCache(Url("test_url_1"), Policy("test_policy_1"), engine=engine)
        _ = bc.BeautifulCache(Url("test_url_2"), Policy("test_policy_2"), engine=engine)

        # These live in different directories.
        self.assertDictEqual(
            engine.file_system.files,
            {
                "test_policy_1/test_url_1.data": tree_crawl.trim_html(example_html_1),
                "test_policy_2/test_url_2.data": tree_crawl.trim_html(example_html_2),
            },
        )

        # In practice, these will live in separate databases.
        self.assertDictEqual(
            engine.database.db,
            {
                make_row("test_policy_1", "test_url_1", ""): 0,
                make_row("test_policy_2", "test_url_2", ""): 0,
            },
        )

    def test_multiple_policies_download_same_page(self):
        example_html_1 = Html("<html><body>Page 1</body</html>")

        engine = (
            BcEngineGenerator().add_website(Url("test_url_1"), example_html_1).build()
        )

        # Download to both policies
        _ = bc.BeautifulCache(Url("test_url_1"), Policy("test_policy_1"), engine=engine)
        _ = bc.BeautifulCache(Url("test_url_1"), Policy("test_policy_2"), engine=engine)

        # Saves to both directories
        self.assertDictEqual(
            engine.file_system.files,
            {
                "test_policy_1/test_url_1.data": tree_crawl.trim_html(example_html_1),
                "test_policy_2/test_url_1.data": tree_crawl.trim_html(example_html_1),
            },
        )

        # Makes two records
        self.assertDictEqual(
            engine.database.db,
            {
                make_row("test_policy_1", "test_url_1", ""): 0,
                make_row("test_policy_2", "test_url_1", ""): 0,
            },
        )


#     # TODO: This needs to be done with a real db
#     # def test_upserts_overwrite(self):
#     #     pass


class TestIdEndToEnd(unittest.TestCase):
    def test_id_happy_path(self):
        example_html = Html(
            """
        <html><body>
        <x>
            <y>First y</y>
            <y>Second y <z>z</z></y>
        </x>
        </body</html>
        """
        )

        engine = BcEngineGenerator().add_website(Url("test_url"), example_html).build()

        soup = bc.BeautifulCache(Url("test_url"), Policy("test_policy"), engine=engine)
        x = soup.find("x")
        y1 = x.find_all("y")[0]
        y2 = x.find_all("y")[1]
        z = y2.find("z")

        self.assertEqual(str(x.id()), "html:0/body:0/x:0")
        self.assertEqual(y1.id(), "html:0/body:0/x:0/y:0")
        self.assertEqual(y2.id(), "html:0/body:0/x:0/y:1")
        self.assertEqual(z.id(), "html:0/body:0/x:0/y:1/z:0")

    def test_find_params(self):
        example_html = Html(
            """
        <html><body>
        <x>
            <y>First y</y>
            <y class="second">Second y <z>z</z></y>
        </x>
        </body</html>
        """
        )

        engine = BcEngineGenerator().add_website(Url("test_url"), example_html).build()

        soup = bc.BeautifulCache(Url("test_url"), Policy("test_policy"), engine=engine)
        y2 = soup.find("y", {"class": "second"})

        self.assertEqual(y2.id(), "html:0/body:0/x:0/y:1")

    def test_cache(self):
        example_html = Html(
            """
        <html><body>
        <x>X</x>
        </body</html>
        """
        )

        engine = BcEngineGenerator().add_website(Url("test_url"), example_html).build()

        soup = bc.BeautifulCache(Url("test_url"), Policy("test_policy"), engine=engine)
        x = soup.find("x")

        self.assertIsNone(x._id)
        self.assertEqual(x.id(), "html:0/body:0/x:0")
        self.assertEqual(x._id, "html:0/body:0/x:0")
