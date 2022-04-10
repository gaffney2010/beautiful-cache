import unittest

import bc
from tests.mock_objects import *
from shared_types import *


class TestEndToEnd(unittest.TestCase):
    def test_happy_path(self):
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

        engine = (
            PolicyEngineGenerator().add_website(Url("test_url"), example_html).build()
        )

        soup = bc.BeautifulCache(Url("test_url"), Policy("test_policy"), engine=engine)
        x = soup.find("x")
        y1 = x.find_all("y")[0]
        y2 = x.find_all("y")[1]
        z = y2.find("z")

        self.assertEqual(x.id(), "html:0/body:0/x:0")
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

        engine = (
            PolicyEngineGenerator().add_website(Url("test_url"), example_html).build()
        )

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

        engine = (
            PolicyEngineGenerator().add_website(Url("test_url"), example_html).build()
        )

        soup = bc.BeautifulCache(Url("test_url"), Policy("test_policy"), engine=engine)
        x = soup.find("x")

        self.assertIsNone(x._id)
        self.assertEqual(x.id(), "html:0/body:0/x:0")
        self.assertEqual(x._id, "html:0/body:0/x:0")
