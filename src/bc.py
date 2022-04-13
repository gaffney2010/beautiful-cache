"""We start with all the code in one file, but this will evolve later."""

from typing import List, Optional

import bs4  # type: ignore

import policy_engine_class
from shared_types import *


# TODO: Should I make a policy/filename variable?
class CacheTag(object):
    # TODO: `tag` may be soup
    def __init__(
        self,
        tag: bs4.element.Tag,
        policy: Policy,
        url: Url,
        engine: policy_engine_class.PolicyEngine,
    ):
        self.tag = tag
        self.policy = policy
        self.url = url
        self.engine = engine

        self._id: Optional[Id] = None

    # TODO: Make a CacheTagList object that we allow to materialize all at once.
    def find_all(self, *args, **kwargs) -> List["CacheTag"]:
        return [
            CacheTag(t, self.policy, self.url, self.engine)
            for t in self.tag.find_all(*args, **kwargs)
        ]

    def find(self, *args, **kwargs) -> "CacheTag":
        return CacheTag(
            self.tag.find(*args, **kwargs), self.policy, self.url, self.engine
        )

    def materialize(self) -> bs4.element.Tag:
        if self.tag is None:
            raise BcException("No tag to materialize")

        # Add a new access record everytime we access.
        self.engine.append(self.policy, self.url, self.id())

        return self.tag

    # TODO: Should this logic live in tree_crawl?
    def _calc_id(self) -> Id:
        # TODO: Handle self.tag is None throughout.
        result = list()

        vertical_cursor = self.tag
        # TODO: Make a short function called top-level, so that we have consistent logic throughout.
        while vertical_cursor.parent is not None:
            name = vertical_cursor.name
            i = 0

            horizontal_cursor = vertical_cursor
            while horizontal_cursor is not None:
                horizontal_cursor = horizontal_cursor.previous_sibling
                # Don't count the first time
                if horizontal_cursor and horizontal_cursor.name == name:
                    i += 1

            this_entry = f"{name}:{i}"
            result.append(this_entry)
            vertical_cursor = vertical_cursor.parent

        return Id("/".join(reversed(result)))

    def id(self) -> Id:
        if self._id is not None:
            return self._id

        self._id = self._calc_id()
        return self._id

    def __str__(self) -> str:
        return str(self.tag)


class BeautifulCache(CacheTag):
    def __init__(
        self, url: Url, policy: Policy, engine: policy_engine_class.PolicyEngine
    ):
        self.url = url
        self.policy = policy
        # TODO: Default engine if not specified.  Make input param Optional then.
        self.engine = engine

        html = engine.read_url(self.policy, self.url)
        soup = bs4.BeautifulSoup(html, features="lxml")

        super().__init__(soup, self.policy, url, self.engine)
