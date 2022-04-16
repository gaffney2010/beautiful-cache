from typing import Any, Dict

from policy_engine_class import BcEngine  # type: ignore
from shared_types import *
import tree_crawl


# TODO(#3): Can I just set BcEngine globally with a singleton or something?
def compact_all(policy: Policy, url: Url, engine: BcEngine) -> None:
    if len(engine.database.query(make_row(policy, url, "*"))) == 0:
        # Safe to delete file.
        engine.file_system.delete(policy, url)


def compact_fat(policy: Policy, url: Url, engine: BcEngine) -> None:
    # TODO(#2.5): I should probably just make pop_query return a dict.  Ditto
    #  batch_write.
    rows = engine.database.pop_query(make_row(policy, url, "*"))
    # TODO(#1): Replace with a function so that we're less like to make a conversion error.
    #  TODO(#1): Find other conversions to Id or to str
    row_by_id = {Id(k.id): v for k, v in rows}
    ids = list(row_by_id.keys())
    ca = tree_crawl.common_ancestor(ids)

    # Update the cache file
    html = engine.file_system.read(policy, url)
    # TODO(#1): Make it clear in documentation that write overwrites.
    engine.file_system.write(policy, url, tree_crawl.isolate_id(html, ca))

    # Update the Requests to contain new addresses
    new_ids = [tree_crawl.mask_id(id, ca) for id in ids]
    new_rows = list()
    for old, new in zip(ids, new_ids):
        new_rows.append((make_row(policy, url, new), row_by_id[old]))
    engine.database.batch_load(new_rows)


def compact_thin(policy: Policy, url: Url, engine: BcEngine) -> None:
    rows = engine.database.pop_query(make_row(policy, url, "*"))
    row_by_id = {Id(k.id): v for k, v in rows}
    ids = list(row_by_id.keys())

    # Update the cache file
    html = engine.file_system.read(policy, url)
    id_mapper: Dict[Id, Id] = dict()
    engine.file_system.write(policy, url, tree_crawl.combine_ids(html, ids, id_mapper))

    # Update the Requests to contain new addresses
    new_rows = list()
    for old in ids:
        new = id_mapper[old]
        new_rows.append((make_row(policy, url, new), row_by_id[old]))
    engine.database.batch_load(new_rows)


# TODO(#2): Return some kind of message.
# TODO: Default arguments.
def compact(policy: Policy, settings: Dict[str, Any], engine: BcEngine) -> None:
    # TODO(#4): Fill in settings blanks from yaml.

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
        affected_urls = {row.url for row in newly_deleted}
        for url in affected_urls:
            file_compaction(policy, url, engine)
