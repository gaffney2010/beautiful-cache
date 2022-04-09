"""We start with all the code in one file, but this will evolve later."""

from typing import List, Optional

import attr
import bs4

from shared_types import *


# Make a bunch of abstract base classes.
class UrlReader(object):
    def __init__(self):
        pass

    def _read(self, url: Url) -> Html:
        raise NotImplementedError


class Database(object):
    def __init__(self):
        pass

    # TODO: Should I return a success message or something?
    def _append(self, policy: Policy, id: str, ts: Time) -> None:
        raise NotImplementedError

    # TODO: What other methods are needed?


class FileSystem(object):
    def __init__(self):
        pass

    def read(self, fn: str) -> str:
        raise NotImplementedError

    def write(self, fn: str, content: str) -> None:
        raise NotImplementedError

    def exists(self, fn: str) -> bool:
        raise NotImplementedError


class Clock(object):
    def __init__(self):
        pass

    def now(self) -> Time:
        raise NotImplementedError


@attr.s()
class PolicyEngine(object):
    url_reader: UrlReader = attr.ib()
    database: Database = attr.ib()
    file_system: FileSystem = attr.ib()
    clock: Clock = attr.ib()

    def append(self, policy: Policy, id: str) -> None:
        """Append to database with current time."""
        self.database._append(policy, id, self.clock.now())

    def read_url(self, url: Url, policy: Policy) -> Html:
        """Reads url, saving an access record to the database at the same time."""
        html = self.url_reader._read(url)
        self.append(policy, "")  # Store the root
        return html


class CacheTag(object):
    # TODO: `tag` may be soup
    def __init__(self, tag: bs4.element.Tag, policy: Policy, engine: PolicyEngine):
        self.tag = tag
        self.policy = policy
        self.engine = engine

        self.root = False

        self._id = None

    # TODO: Make a CacheTagList object that we allow to materialize all at once.
    def find_all(self, *args, **kwargs) -> List["CacheTag"]:
        return [
            CacheTag(t, self.policy, self.engine)
            for t in self.tag.find_all(args, kwargs)
        ]

    def find(self, *args, **kwargs) -> "CacheTag":
        return CacheTag(self.tag.find(args, kwargs), self.policy, self.engine)

    def materialize(self) -> bs4.element.Tag:
        if self.tag is None:
            raise BcException("No tag to materialize")

        # Add a new access record everytime we access.
        self.engine.append(self.policy, self.id())

        return self.tag

    # TODO: Make ID type
    def _calc_id(self) -> str:
        # TODO: Replace with full ID
        return self.tag.name

    def id(self) -> str:
        if self._id is not None:
            return self._id

        self._id = self._calc_id()
        return self._id


def cached_read(url: Url, policy: Policy, engine: PolicyEngine) -> Html:
    # TODO: Need to sanitize URLs into keys somehow.
    if engine.file_system.exists(url):
        return engine.file_system.read(url)

    result = engine.read_url(url, policy)
    engine.file_system.write(url, result)
    return result


class BeautifulCache(CacheTag):
    def __init__(self, url: Url, policy: Policy, engine: Optional[PolicyEngine] = None):
        self.url = url
        self.policy = policy
        # TODO: Default engine if not specified.
        self.engine = engine

        html = cached_read(self.url, self.policy, engine=engine)
        soup = bs4.BeautifulSoup(html, features="lxml")

        super().__init__(soup, self.policy, self.engine)
        self.root = True
