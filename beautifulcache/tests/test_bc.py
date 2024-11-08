import sys
import os

# Add the parent directory to the sys.path
current_dir = os.path.dirname(__file__)  # Get the current script's directory
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

import unittest

import bc
import mock_objects

# Example from beautiful soup doc
html_doc = """<html><head><title>The Dormouse's story</title></head>
<body>
<p class="title"><b>The Dormouse's story</b></p>

<p class="story">Once upon a time there were three little sisters; and their names were
<a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
<a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
<a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
and they lived at the bottom of a well.</p>

<p class="story">...</p>
"""


class TestBeautifulCache(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        pass

    async def test_happy_path(self):
        cacher = mock_objects.MockCacher()
        # Fill in with default namespace a, and empty parse_only
        cacher.set("+".join(["a", "abc.com", "_"]), html_doc, 1)
        scraper = mock_objects.mock_scraper_fn(dict())
        soup = await bc.BeautifulCache("abc.com", scraper, cacher)

        self.assertEqual(str(soup.title), "<title>The Dormouse's story</title>")
        self.assertEqual(soup.title.name, "title")
        self.assertEqual(soup.title.string, "The Dormouse's story")
        self.assertEqual(soup.title.parent.name, "head")
        self.assertEqual(
            str(soup.p), '<p class="title"><b>The Dormouse\'s story</b></p>'
        )
        self.assertEqual(soup.p["class"], ["title"])
        self.assertEqual(
            str(soup.a),
            '<a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>',
        )
        self.assertEqual(
            list(map(str, soup.find_all("a"))),
            [
                '<a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>',
                '<a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>',
                '<a class="sister" href="http://example.com/tillie" id="link3">Tillie</a>',
            ],
        )
        self.assertEqual(
            str(soup.find(id="link3")),
            '<a class="sister" href="http://example.com/tillie" id="link3">Tillie</a>',
        )

