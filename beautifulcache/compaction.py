import traceback
from typing import Any, Dict, Optional

import yaml  # type: ignore

from .policy_engine_class import BcEngine
from .shared_types import *
from . import tree_crawl


def compact_all(
    policy: Policy, url: Url, engine: BcEngine, record: CompactionRecord
) -> None:
    if not engine.database.exists(policy, url):
        # Safe to delete file.
        engine.file_system.delete(policy, url)


# TODO: Add test for entire file compacted away.
def compact_fat(
    policy: Policy, url: Url, engine: BcEngine, record: CompactionRecord
) -> None:
    if not engine.database.exists(policy, url):
        # Safe to delete file.
        engine.file_system.delete(policy, url)
        return

    row_by_id = engine.database.pop_query(policy, url)
    ids = list(row_by_id.keys())
    ca = tree_crawl.common_ancestor(ids)

    # Update the cache file
    html = engine.file_system.read(policy, url)
    # TODO: Save and load soups instead of HTML to save time on processing...
    engine.file_system.write(policy, url, tree_crawl.isolate_id(html, ca))

    # Update the Requests to contain new addresses
    new_ids = [tree_crawl.mask_id(id, ca) for id in ids]
    new_rows = list()
    for old, new in zip(ids, new_ids):
        new_row = make_row(policy, url, new)
        record.records_added.append(new_row)
        new_rows.append((new_row, row_by_id[old]))
    engine.database.batch_load(new_rows)


def compact_thin(
    policy: Policy, url: Url, engine: BcEngine, record: CompactionRecord
) -> None:
    if not engine.database.exists(policy, url):
        # Safe to delete file.
        engine.file_system.delete(policy, url)
        return

    row_by_id = engine.database.pop_query(policy, url)
    ids = list(row_by_id.keys())

    # Update the cache file
    html = engine.file_system.read(policy, url)
    id_mapper: Dict[Id, Id] = dict()
    engine.file_system.write(policy, url, tree_crawl.combine_ids(html, ids, id_mapper))

    # Update the Requests to contain new addresses
    new_rows = list()
    for old in ids:
        new = id_mapper[old]
        new_row = make_row(policy, url, new)
        record.records_added.append(new_row)
        new_rows.append((new_row, row_by_id[old]))
    engine.database.batch_load(new_rows)


# TODO: Default engine.
def compact(
    policy: Policy,
    engine: BcEngine,
    settings: Optional[Dict[str, Any]] = None,
    continue_on_error: bool = False,
) -> CompactionRecord:
    if settings is None:
        settings = {}

    if engine.file_system.exists(policy, "settings.yaml"):
        y = yaml.safe_load(engine.file_system.read(policy, "settings.yaml"))
        for field in ("max_bytes", "strategy"):
            # Don't overwrite, only fill-in
            if field in y and field not in settings:
                settings[field] = y[field]

    if "priority" not in settings:
        settings["priority"] = "fifo"

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

    record = CompactionRecord()

    size_before = engine.file_system.size(policy)

    max_bytes = settings["max_bytes"]
    while engine.file_system.size(policy) > max_bytes:
        affected_urls = engine.database.pop(policy, settings["priority"], record)
        if len(affected_urls) == 0:
            # We've popped all we could.
            break
        record.affected_urls = affected_urls
        for url in affected_urls:
            print(f"Compacting {url}")
            try:
                file_compaction(policy, url, engine, record)
            except Exception as err:
                traceback.print_exc()
                if not continue_on_error:
                    raise BcException(f"Error compacting {url}: {err}")

    size_after = engine.file_system.size(policy)
    record.size_delta = size_before - size_after

    return record
