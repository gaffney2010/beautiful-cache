from typing import Any, Dict

from shared_types import *


def compact_all(policy: Policy, settings: Dict[str: Any]) -> None:
    raise NotImplementedError


def compact_fat(policy: Policy, settings: Dict[str: Any]) -> None:
    raise NotImplementedError


def compact_thin(policy: Policy, settings: Dict[str: Any]) -> None:
    raise NotImplementedError


# TODO: Return some kind of message.
def compact(policy: Policy, settings: Dict[str: Any]) -> None:
    # TODO: Fill in settings blanks from yaml.

    for required_field in ("max_bytes", "strategy"):
        if required_field not in settings:
            raise BcException(f"Missing required arg {required_field} in call to compact.")

    strategy = settings["strategy"]
    if strategy == "all":
        return compact_all(policy, settings)
    elif strategy == "fat":
        return compact_fat(policy, settings)
    elif strategy == "thin":
        return compact_thin(policy, settings)
    else:
        raise BcException(f"Unknown compaction strategy: {strategy}")
