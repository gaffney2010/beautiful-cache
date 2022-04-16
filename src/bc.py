"""We start with all the code in one file, but this will evolve later."""

from typing import List, Optional

import bs4  # type: ignore

from policy_engine_class import BcEngine  # type: ignore
import shared_logic
from shared_types import *


# TODO(#3): Should I make a policy/filename variable?
class CacheTag(object):
    def __init__(
        self,
        tag: Ingredient,
        policy: Policy,
        url: Url,
        engine: BcEngine,
    ):
        self.tag = tag
        self.policy = policy
        self.url = url
        self.engine = engine

        self._id: Optional[Id] = None

    # TODO(#5): Make a CacheTagList object that we allow to materialize all at once.
    def find_all(self, *args, **kwargs) -> List["CacheTag"]:
        if self.tag is None:
            raise BcException("No tag to search")

        return [
            CacheTag(t, self.policy, self.url, self.engine)
            for t in self.tag.find_all(*args, **kwargs)
        ]

    def find(self, *args, **kwargs) -> "CacheTag":
        if self.tag is None:
            raise BcException("No tag to search")

        return CacheTag(
            self.tag.find(*args, **kwargs), self.policy, self.url, self.engine
        )

    def materialize(self) -> Ingredient:
        if self.tag is None:
            raise BcException("No tag to materialize")

        # Add a new access record everytime we access.
        self.engine.append(self.policy, self.url, self.id())

        return self.tag

    def _calc_id(self) -> Id:
        if self.tag is None:
            raise BcException("No tag to get ID for")

        result = list()

        vertical_cursor = self.tag
        while not shared_logic.is_root(vertical_cursor.parent):
            # Name is this tag's name
            name = vertical_cursor.name

            # Index = # of previous_siblings have same name
            i = 0
            horizontal_cursor = vertical_cursor
            while horizontal_cursor is not None:
                horizontal_cursor = horizontal_cursor.previous_sibling
                if horizontal_cursor and horizontal_cursor.name == name:
                    i += 1

            # Put them together for this layer's tag part
            this_entry = f"{name}:{i}"
            result.append(this_entry)
            vertical_cursor = vertical_cursor.parent

        # TODO: I don't like this, I don't even really understand it.
        result.append("html:0")

        return Id("/".join(reversed(result)))

    def id(self) -> Id:
        if self._id is not None:
            return self._id

        self._id = self._calc_id()
        return self._id

    def __str__(self) -> str:
        if not self.tag:
            return "tagless-node"

        return str(self.tag)


class BeautifulCache(CacheTag):
    def __init__(self, url: Url, policy: Policy, engine: BcEngine):
        self.url = url
        self.policy = policy
        # TODO: Default engine if not specified.  Make input param Optional then.
        self.engine = engine

        html = engine.read_url(self.policy, self.url)
        soup = bs4.BeautifulSoup(html, features="lxml")

        super().__init__(soup, self.policy, url, self.engine)
