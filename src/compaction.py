from typing import Any, Dict

from shared_types import *
from src.policy_engine_class import PolicyEngine


# TODO: Can I just set policyEngine globally with a singleton or something?
def compact_all(policy: Policy, settings: Dict[str, Any], engine: PolicyEngine) -> None:
    max_bytes = settings["max_bytes"]

    while engine.file_system.size(policy) > max_bytes:
        newly_deleted = engine.database.pop(policy)
        affected_files = {pfi.filename for pfi in newly_deleted}
        for fn in affected_files:
            if len(engine.database.query(pfi(policy, fn, "*"))) == 0:
                # Safe to delete file.
                engine.file_system.delete(policy, fn)


def compact_fat(policy: Policy, settings: Dict[str, Any], engine: PolicyEngine) -> None:
    raise NotImplementedError


def compact_thin(
    policy: Policy, settings: Dict[str, Any], engine: PolicyEngine
) -> None:
    raise NotImplementedError


# TODO: Return some kind of message.
# TODO: Default arguments.
def compact(policy: Policy, settings: Dict[str, Any], engine: PolicyEngine) -> None:
    # TODO: Fill in settings blanks from yaml.

    for required_field in ("max_bytes", "strategy"):
        if required_field not in settings:
            raise BcException(
                f"Missing required arg {required_field} in call to compact."
            )

    strategy = settings["strategy"]
    if strategy == "all":
        return compact_all(policy, settings, engine)
    elif strategy == "fat":
        return compact_fat(policy, settings, engine)
    elif strategy == "thin":
        return compact_thin(policy, settings, engine)
    else:
        raise BcException(f"Unknown compaction strategy: {strategy}")
