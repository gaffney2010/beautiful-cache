import unittest

import compaction
import policy_engine_class
from shared_types import *
import tree_crawl
from tests.mock_objects import *


class TestCompaction(unittest.TestCase):
    def _setup_happy_paths(self) -> policy_engine_class.BcEngine:
        """For the first three tests, create the same HTML"""
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

        beg = BcEngineGenerator()

        # TODO: Consistent typing in tests...
        beg.add_file("test_policy/f1.data", tree_crawl.trim_html(html))
        beg.add_file(
            "test_policy/f2.data", "..."
        )  # Something to check existence if everything else deleted.

        beg.add_request("test_policy", "f1", "", 0)
        beg.add_request("test_policy", "f1", "html:0/body:0/div:0/p:0/a:1", 1)
        beg.add_request("test_policy", "f1", "html:0/body:0/div:0/p:2", 2)
        beg.add_request("test_policy", "f2", "", 3)

        return beg.build()

    def test_all_happy_path(self):
        engine = self._setup_happy_paths()
        # Engine has size = 179 at this point.

        # Even a small trim will result in dropping the entire first file with the
        #  "all" strategy.
        target_size = 150

        compaction.compact(
            "test_policy",
            settings={"max_bytes": target_size, "strategy": "all"},
            engine=engine,
        )

        self.assertDictEqual(
            engine.file_system.files,
            {
                Filename("test_policy/f2.data"): "...",
            },
        )
        self.assertDictEqual(
            engine.database.db,
            {
                pui("test_policy", "f2", ""): Time(3),
            },
        )

    def test_fat_happy_path(self):
        engine = self._setup_happy_paths()
        # Engine has size = 179 at this point.

        # Small trim will remove only the first access record.
        compaction.compact(
            "test_policy",
            settings={"max_bytes": 150, "strategy": "fat"},
            engine=engine,
        )

        self.assertDictEqual(
            engine.file_system.files,
            {
                Filename("test_policy/f1.data"): (
                    "<html><body><div> <p><a>1</a><a>2</a></p> <p><a>3</a><a>4</a></p>"
                    " <p>5 <span>my_span</span></p> </div></body></html>"
                ),
                Filename("test_policy/f2.data"): "...",
            },
        )
        self.assertDictEqual(
            engine.database.db,
            {
                pui("test_policy", "f1", "html:0/body:0/div:0/p:0/a:1"): 1,
                pui("test_policy", "f1", "html:0/body:0/div:0/p:2"): 2,
                pui("test_policy", "f2", ""): Time(3),
            },
        )

        # Slightly larger trim will remove second access record, leaving only p:2
        compaction.compact(
            "test_policy",
            settings={"max_bytes": 100, "strategy": "fat"},
            engine=engine,
        )

        self.assertDictEqual(
            engine.file_system.files,
            {
                Filename("test_policy/f1.data"): (
                    "<html><body><div><p>5 <span>my_span</span></p></div></body>"
                    "</html>"
                ),
                Filename("test_policy/f2.data"): "...",
            },
        )
        self.assertDictEqual(
            engine.database.db,
            {
                pui("test_policy", "f1", "html:0/body:0/div:0/p:0"): 2,
                pui("test_policy", "f2", ""): Time(3),
            },
        )

    def test_thin_happy_path(self):
        engine = self._setup_happy_paths()
        # Engine has size = 179 at this point.

        # Small trim will remove only the first access record.
        compaction.compact(
            "test_policy",
            settings={"max_bytes": 150, "strategy": "thin"},
            engine=engine,
        )

        self.assertDictEqual(
            engine.file_system.files,
            {
                # TODO: Why do I have div twice and body once?
                Filename("test_policy/f1.data"): (
                    "<html><body><div><p><a>2</a></p><p>5 <span>my_span</span></p>"
                    "</div></body></html>"
                ),
                Filename("test_policy/f2.data"): "...",
            },
        )
        # Notice that all the tags got remapped for the new doc.
        self.assertDictEqual(
            engine.database.db,
            {
                pui("test_policy", "f1", "html:0/body:0/div:0/p:0/a:0"): 1,
                pui("test_policy", "f1", "html:0/body:0/div:0/p:0"): 2,
                pui("test_policy", "f2", ""): Time(3),
            },
        )

        # Slightly larger trim will remove second access record, leaving only p:2
        compaction.compact(
            "test_policy",
            settings={"max_bytes": 75, "strategy": "thin"},
            engine=engine,
        )

        self.assertDictEqual(
            engine.file_system.files,
            {
                Filename(
                    "test_policy/f1.data"
                ): "<html><body><div><p><a>2</a></p></div></body></html>",
                Filename("test_policy/f2.data"): "...",
            },
        )
        self.assertDictEqual(
            engine.database.db,
            {
                pui("test_policy", "f1", "html:0/body:0/div:0/p:0"): 2,
                pui("test_policy", "f2", ""): Time(3),
            },
        )

    def test_fat_will_trim_multiple_rows(self):
        # Same as test_fat_happy_path, except we trim both at once.

        engine = self._setup_happy_paths()
        # Engine has size = 179 at this point.

        # Slightly larger trim will remove second access record, leaving only p:2
        compaction.compact(
            "test_policy",
            settings={"max_bytes": 100, "strategy": "fat"},
            engine=engine,
        )

        self.assertDictEqual(
            engine.file_system.files,
            {
                Filename("test_policy/f1.data"): (
                    "<html><body><div><p>5 <span>my_span</span></p></div></body>"
                    "</html>"
                ),
                Filename("test_policy/f2.data"): "...",
            },
        )
        self.assertDictEqual(
            engine.database.db,
            {
                pui("test_policy", "f1", "html:0/body:0/div:0/p:0"): 2,
                # TODO: More consistently type on these tests, plz.
                pui("test_policy", "f2", ""): Time(3),
            },
        )

    def test_no_compaction_if_max_bytes_is_large_enough(self):
        engine = self._setup_happy_paths()
        # Engine has size = 179 at this point.

        # Shouldn't trim anything.
        compaction.compact(
            "test_policy",
            settings={"max_bytes": 200, "strategy": "thin"},
            engine=engine,
        )

        self.assertDictEqual(
            engine.file_system.files,
            {
                Filename("test_policy/f1.data"): (
                    "<html> <head></head> <body> <div> "
                    "<p><a>1</a><a>2</a></p> <p><a>3</a><a>4</a></p> <p>5 "
                    "<span>my_span</span></p> </div> <div> <p><a>6</a> 7 "
                    "and beyond</p> </div> </body> </html>"
                ),
                Filename("test_policy/f2.data"): "...",
            },
        )
        # Notice that all the tags got remapped for the new doc.
        self.assertDictEqual(
            engine.database.db,
            {
                pui("test_policy", "f1", ""): Time(0),
                pui("test_policy", "f1", "html:0/body:0/div:0/p:0/a:1"): 1,
                pui("test_policy", "f1", "html:0/body:0/div:0/p:2"): 2,
                pui("test_policy", "f2", ""): Time(3),
            },
        )

    def test_use_yaml(self):
        # TODO:
        pass

    def test_ts_ties(self):
        # 54 bytes after trimming.
        html = """
            <html>
            <body>
            <a>A</a><b>B</b><c>C</c>
            </body>
            </html>"""

        beg = BcEngineGenerator()

        # TODO: Consistent typing in tests...
        beg.add_file("test_policy/f1.data", tree_crawl.trim_html(html))

        beg.add_request("test_policy", "f1", "", 0)
        beg.add_request("test_policy", "f1", "html:0/body:0/a:0", 0)
        beg.add_request("test_policy", "f1", "html:0/body:0/b:0", 0)
        beg.add_request("test_policy", "f1", "html:0/body:0/c:0", 1)

        engine = beg.build()

        # Even though we only want to trim 1 character, a and b will both get deleted
        compaction.compact(
            "test_policy",
            settings={"max_bytes": 53, "strategy": "thin"},
            engine=engine,
        )

        self.assertDictEqual(
            engine.file_system.files,
            {
                Filename("test_policy/f1.data"): (
                    "<html><body><c>C</c></body></html>"
                ),
            },
        )
        # Notice that all the tags got remapped for the new doc.
        self.assertDictEqual(
            engine.database.db,
            {
                pui("test_policy", "f1", "html:0/body:0/c:0"): 1,
            },
        )

    def test_transaction(self):
        # TODO:
        pass

    def test_multiple_policies(self):
        # TODO:
        pass

    def test_erase_entire_old_before_any_new(self):
        # TODO:
        pass
