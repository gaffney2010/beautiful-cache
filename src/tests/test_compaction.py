import unittest

import compaction
import policy_engine_class
from shared_types import *
import tree_crawl
from tests.mock_objects import *


class TestCompaction(unittest.TestCase):
    def _setup_happy_paths(self) -> policy_engine_class.PolicyEngine:
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

        peg = PolicyEngineGenerator()

        peg.add_file("f1.data", tree_crawl.trim_html(html))
        peg.add_file(
            "f2.data", "..."
        )  # Something to check existence if everything else deleted.

        peg.add_request("test_policy", "f1.data", "", 0)
        peg.add_request("test_policy", "f1.data", "body:0/div:0/p:0/a:1", 1)
        peg.add_request("test_policy", "f1.data", "body:0/div:0/p:2", 2)
        peg.add_request("test_policy", "f2.data", "", 3)

        return peg.build()

    def test_all_happy_path(self):
        # TODO:
        engine = self._setup_happy_paths()
        # Engine has size = 179 at this point.

        # Even a small trim will result in dropping the entire first file with the "all" strategy.
        target_size = 150

        compaction.compact(
            "test_policy", settings={"max_bytes": target_size, "strategy": "all"}
        )

        self.assertDictEqual(
            engine.file_system,
            {
                Filename("f2.data"): "...",
            },
        )
        # TODO: Untype these in tests.
        self.assertDictEqual(
            engine.file_system,
            {
                (Policy("test_policy"), Filename("f2.data"), Id("")): Time(3),
            },
        )

    def test_fat_happy_path(self):
        # TODO:
        pass

    def test_thin_happy_path(self):
        # TODO:
        pass

    def test_use_yaml(self):
        # TODO:
        pass

    def test_ts_ties(self):
        # TODO:
        pass

    def test_transaction(self):
        # TODO:
        pass

    def test_multiple_policies(self):
        # TODO:
        pass

    def test_erase_entire_old_before_any_new(self):
        # TODO:
        pass

    def test_after_materialize_compact_all(self):
        # TODO:
        pass

    def test_bump_only_materialized_file(self):
        # TODO:
        pass
