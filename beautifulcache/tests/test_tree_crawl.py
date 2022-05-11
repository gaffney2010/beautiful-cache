import unittest

import bs4

from beautifulcache.shared_types import *
from beautifulcache import tree_crawl


class TestTreeCrawl(unittest.TestCase):
    def test_trim_happy_path(self):
        html = """
            <html>
            <head></head>
            <body>
                <div>
                    <p><a>1</a><a>2</a></p>
                    <p><a>3</a><a>4</a></p>
                    <p>5 <span>my_span</span></p>
                </div>
                <div>
                    <p><a>6</a> 7 and beyond</p>
                </div>
            </body>
            </html>"""

        soup = bs4.BeautifulSoup(html, features="lxml")

        expected_html = (
            "<html> <head></head> <body> <div> <p><a>1</a><a>2</a></p> <p><a>3</a>"
            "<a>4</a></p> <p>5 <span>my_span</span></p> </div> <div> <p><a>6</a> 7 "
            "and beyond</p> </div> </body> </html>"
        )

        self.assertEqual(tree_crawl.trim(soup), expected_html)

    def test_trim_several_spaces(self):
        html = "<html><body><p>    Hi    </p></body></html>"

        soup = bs4.BeautifulSoup(html, features="lxml")

        expected_html = "<html><body><p> Hi </p></body></html>"

        self.assertEqual(tree_crawl.trim(soup), expected_html)

    def test_trim_newlines(self):
        html = """<html><body><p>
        
        
        Hi
        
        
        </p></body></html>"""

        soup = bs4.BeautifulSoup(html, features="lxml")

        expected_html = "<html><body><p> Hi </p></body></html>"

        self.assertEqual(tree_crawl.trim(soup), expected_html)

    def test_trim_spaces_outside(self):
        html = "<html><body>     <p>Hi</p> </body></html>"

        soup = bs4.BeautifulSoup(html, features="lxml")

        expected_html = "<html><body> <p>Hi</p> </body></html>"

        self.assertEqual(tree_crawl.trim(soup), expected_html)

    def test_trim_asymmetric(self):
        html = "<html><body><p>Hi  </p>  </body>  </html>"

        soup = bs4.BeautifulSoup(html, features="lxml")

        expected_html = "<html><body><p>Hi </p> </body> </html>"

        self.assertEqual(tree_crawl.trim(soup), expected_html)

    def test_ca_happy_path(self):
        self.assertEqual(
            tree_crawl.common_ancestor([Id("a:0/b:1/c:0/d:1"), Id("a:0/b:1/e:2")]),
            Id("a:0/b:1"),
        )

    def test_ca_empty_id(self):
        self.assertEqual(
            tree_crawl.common_ancestor([Id("a:0/b:1/c:0/d:1"), Id("")]), Id(""),
        )

    def test_ca_nothing_in_common(self):
        self.assertEqual(
            tree_crawl.common_ancestor([Id("a:0/b:1/c:0/d:1"), Id("g:0/h:1/i:2")]),
            Id(""),
        )

    def test_ca_ignore_downstream(self):
        self.assertEqual(
            tree_crawl.common_ancestor([Id("a:0/b:0/c:0"), Id("a:0/x:0/c:0")]),
            Id("a:0"),
        )

    def test_ca_index(self):
        self.assertEqual(
            tree_crawl.common_ancestor([Id("a:0/b:0"), Id("a:0/b:1")]), Id("a:0"),
        )

    def test_ca_child_id(self):
        self.assertEqual(
            tree_crawl.common_ancestor([Id("a:0/b:1"), Id("a:0/b:1/c:2/d:4")]),
            Id("a:0/b:1"),
        )

    def test_ca_repeated_parts(self):
        self.assertEqual(
            tree_crawl.common_ancestor([Id("a:0/a:0"), Id("a:0/a:0/b:1")]),
            Id("a:0/a:0"),
        )

    def test_ca_identical(self):
        self.assertEqual(
            tree_crawl.common_ancestor([Id("a:0/b:1/c:0"), Id("a:0/b:1/c:0")]),
            Id("a:0/b:1/c:0"),
        )

    def test_ca_multi_input_happy_path(self):
        self.assertEqual(
            tree_crawl.common_ancestor(
                [
                    Id("a:0/b:1/c:0/d:1"),
                    Id("a:0/b:1/e:2"),
                    Id("a:0/b:1/h:0/g:1"),
                    Id("a:0/b:1/x:10"),
                ]
            ),
            Id("a:0/b:1"),
        )

    def test_ca_multi_intersection(self):
        # Only the first two are on EVERY one.
        self.assertEqual(
            tree_crawl.common_ancestor(
                [
                    Id("a:0/b:1/c:0/d:1"),
                    Id("a:0/b:1/c:0/e:4"),
                    Id("a:0/b:1/c:0/g:1"),
                    Id("a:0/b:1/x:10"),
                ]
            ),
            Id("a:0/b:1"),
        )

    def test_mask_id_happy_path(self):
        self.assertEqual(
            tree_crawl.mask_id(Id("a:1/b:2/c:3/d:7/e:8"), Id("a:1/b:2/c:3")),
            Id("a:0/b:0/c:0/d:7/e:8"),
        )

    def test_mask_id_empty_mask(self):
        self.assertEqual(
            tree_crawl.mask_id(Id("a:1/b:2/c:3/d:7/e:8"), Id("")),
            Id("a:1/b:2/c:3/d:7/e:8"),
        )

    def test_mask_id_empty_id(self):
        self.assertEqual(tree_crawl.mask_id(Id(""), Id("")), Id(""))

    def test_mask_id_invalid_mask(self):
        with self.assertRaises(BcException) as context:
            tree_crawl.mask_id(Id("a:1/b:2/c:3/d:7/e:8"), Id("a:1/c:5/e:7"))

    def test_isolate_id_happy_path(self):
        html = """
            <html>
            <head></head>
            <body>
                <div>
                    <p><a>1</a><a>2</a></p>
                    <p><a>3</a><a>4</a></p>
                    <p>5 <span>my_span</span></p>
                </div>
                <div>
                    <p><a>6</a> 7 and beyond</p>
                </div>
            </body>
            </html>"""

        self.assertEqual(
            tree_crawl.isolate_id(html, Id("html:0/body:0/div:0/p:1")),
            "<html><body><div><p><a>3</a><a>4</a></p></div></body></html>",
        )
        self.assertEqual(
            tree_crawl.isolate_id(html, Id("html:0/body:0/div:1")),
            "<html><body><div> <p><a>6</a> 7 and beyond</p> </div></body></html>",
        )
        self.assertEqual(
            tree_crawl.isolate_id(html, Id("html:0/body:0/div:1/p:0")),
            "<html><body><div><p><a>6</a> 7 and beyond</p></div></body></html>",
        )
        self.assertEqual(
            tree_crawl.isolate_id(html, Id("html:0/body:0/div:1/p:0/a:0")),
            "<html><body><div><p><a>6</a></p></div></body></html>",
        )

    def test_combine_ids_happy_path(self):
        html = """
            <html>
            <head></head>
            <body>
                <div>
                    <p><a>1</a><a>2</a></p>
                    <p><a>3</a><a>4</a></p>
                    <p>5 <span>my_span</span></p>
                </div>
                <div>
                    <p><a>6</a> 7 and beyond</p>
                </div>
            </body>
            </html>"""

        id_mapper = dict()
        result = tree_crawl.combine_ids(
            html,
            [Id("html:0/body:0/div:0/p:1/a:0"), Id("html:0/body:0/div:1")],
            id_mapper,
        )

        self.assertEqual(
            result,
            (
                "<html><body><div><p><a>3</a></p></div><div> <p><a>6</a> 7 and beyond</p>"
                " </div></body></html>"
            ),
        )

        # id_mapper also contains other, unneeded mappings.
        self.assertEqual(
            id_mapper[Id("html:0/body:0/div:0/p:1/a:0")],
            Id("html:0/body:0/div:0/p:0/a:0"),
        )
        self.assertEqual(
            id_mapper[Id("html:0/body:0/div:1")], Id("html:0/body:0/div:1")
        )

    def test_combine_ids_multiple_ids(self):
        html = """
            <html>
            <head></head>
            <body>
                <div>
                    <p><a>1</a><a>2</a></p>
                    <p><a>3</a><a>4</a></p>
                    <p>5 <span>my_span</span></p>
                </div>
                <div>
                    <p><a>6</a> 7 and beyond</p>
                </div>
            </body>
            </html>"""

        id_mapper = dict()
        result = tree_crawl.combine_ids(
            html,
            [
                Id("html:0/body:0/div:0/p:0/a:0"),
                Id("html:0/body:0/div:0/p:1/a:0"),
                Id("html:0/body:0/div:0/p:1/a:1"),
                Id("html:0/body:0/div:1"),
            ],
            id_mapper,
        )

        self.assertEqual(
            result,
            (
                "<html><body><div><p><a>1</a></p><p><a>3</a><a>4</a></p></div><div> <p>"
                "<a>6</a> 7 and beyond</p> </div></body></html>"
            ),
        )

    def test_combine_ids_child(self):
        html = """
            <html>
            <head></head>
            <body>
                <div>
                    <p><a>1</a><a>2</a></p>
                    <p><a>3</a><a>4</a></p>
                    <p>5 <span>my_span</span></p>
                </div>
                <div>
                    <p><a>6</a> 7 and beyond</p>
                </div>
            </body>
            </html>"""

        id_mapper = dict()
        result = tree_crawl.combine_ids(
            html,
            [Id("html:0/body:0/div:0/p:1"), Id("html:0/body:0/div:0/p:1/a:0"),],
            id_mapper,
        )

        self.assertEqual(
            result, "<html><body><div><p><a>3</a><a>4</a></p></div></body></html>",
        )
