import sys
import os

# Add the parent directory to the sys.path
current_dir = os.path.dirname(__file__)  # Get the current script's directory
sys.path.append(current_dir)

from dataclasses import dataclass
from typing import Dict, Optional

import bc


@dataclass
class Value(object):
    expiry: int
    value: str


class MockCacher(bc.Cacher):
    def __init__(self):
        self.c: Dict[str, Value] = dict()
        self.time = 0
        super().__init__()

    def clock(self) -> int:
        return self.time

    def set_clock(self, time: int) -> None:
        self.time = time

    def set(self, key: str, value: str, ttl: int) -> None:
        self.c[key] = Value(self.clock() + ttl, value)

    def get(self, key: str) -> Optional[str]:
        result = self.c.get(key)
        if result is None:
            return None
        if result.expiry < self.time:
            return None
        return result.value


def mock_scraper_fn(internet: Dict[bc.Url, str]) -> bc.ScraperFn:
    async def mock_internet(url: bc.Url, **kwargs) -> str:
        result = internet.get(url)
        if not result:
            raise ValueError("No mock for url")
        return result

    return mock_internet
