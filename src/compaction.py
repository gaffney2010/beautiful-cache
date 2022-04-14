from typing import Any, Dict

from shared_types import *
from src.policy_engine_class import BcEngine
import tree_crawl


# TODO: Can I just set BcEngine globally with a singleton or something?
def compact_all(policy: Policy, url: Url, engine: BcEngine) -> None:
    if len(engine.database.query(pui(policy, url, "*"))) == 0:
        # Safe to delete file.
        engine.file_system.delete(policy, url)


def compact_fat(policy: Policy, url: Url, engine: BcEngine) -> None:
    ids = [row.id for row in engine.database.query(pui(policy, url, "*"))]
    id = tree_crawl.common_ancestor(ids)
    html = engine.file_system.read(policy, url)
    # TODO: Make it clear in documentation that write overwrites.
    engine.file_system.write(policy, url, tree_crawl.isolate_id(html, id))


def compact_thin(policy: Policy, url: Url, engine: BcEngine) -> None:
    ids = [row.id for row in engine.database.query(pui(policy, url, "*"))]
    html = engine.file_system.read(policy, url)
    engine.file_system.write(policy, url, tree_crawl.combine_ids(html, ids))


# TODO: Return some kind of message.
# TODO: Default arguments.
def compact(policy: Policy, settings: Dict[str, Any], engine: BcEngine) -> None:
    # TODO: Fill in settings blanks from yaml.

    for required_field in ("max_bytes", "strategy"):
        if required_field not in settings:
            raise BcException(
                f"Missing required arg {required_field} in call to compact."
            )

    strategy = settings["strategy"]
    if strategy == "all":
        file_compaction = compact_all
    elif strategy == "fat":
        file_compaction = compact_fat
    elif strategy == "thin":
        file_compaction = compact_thin
    else:
        raise BcException(f"Unknown compaction strategy: {strategy}")

    max_bytes = settings["max_bytes"]
    while engine.file_system.size(policy) > max_bytes:
        newly_deleted = engine.database.pop(policy)
        affected_urls = {pui.url for pui in newly_deleted}
        for url in affected_urls:
            file_compaction(policy, url, engine)
