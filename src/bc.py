"""We start with all the code in one file, but this will evolve later."""

from typing import List, Optional

import attr
import bs4

from shared_types import *


# Make a bunch of abstract base classes.
class UrlReader(object):
    def __init__(self):
        pass

    def read(self, url: Url) -> Html:
        raise NotImplementedError


class Database(object):
    def __init__(self):
        pass

    # TODO: Should I return a success message or something?
    def append(self, row: Row) -> None:
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


class CacheTag(object):
    # TODO: `tag` may be soup
    def __init__(self, tag: bs4.element.Tag):
        self.root = False
        self.tag = tag

    # TODO: Make a CacheTagList object that we allow to materialize all at once.
    def find_all(self, *args, **kwargs) -> List["CacheTag"]:
        return [CacheTag(t) for t in self.tag.find_all(args, kwargs)]

    def find(self, *args, **kwargs) -> "CacheTag":
        return CacheTag(self.tag.find(args, kwargs))

    def materialize(self) -> bs4.element.Tag:
        if self.tag is None:
            raise BcException("No tag to materialize")

        return self.tag


def cached_read(url: Url, engine: PolicyEngine) -> Html:
    # TODO: Need to sanitize URLs into keys somehow.
    if engine.file_system.exists(url):
        return engine.file_system.read(url)

    result = engine.url_reader.read(url)
    engine.file_system.write(url, result)
    return result


class BeautifulCache(CacheTag):
    def __init__(self, url: Url, policy: Policy, engine: Optional[PolicyEngine] = None):
        self.url = url
        self.policy = policy
        # TODO: Default engine if not specified.
        self.engine = engine

        html = cached_read(self.url, engine=engine)
        soup = bs4.BeautifulSoup(html, features="lxml")

        super().__init__(soup)
        self.root = True
