import unittest

import bs4

import tree_crawl


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
