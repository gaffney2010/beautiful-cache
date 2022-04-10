"""We start with all the code in one file, but this will evolve later."""

from typing import List, Optional

import attr
import bs4  # type: ignore

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
    def _append(self, policy: Policy, id: Id, ts: Time) -> None:
        raise NotImplementedError

    # TODO: What other methods are needed?


class FileSystem(object):
    def __init__(self):
        pass

    def key(self, url: Url) -> Filename:
        return Filename(url.replace("/", "") + ".data")

    def read(self, fn: Filename) -> str:
        raise NotImplementedError

    def write(self, fn: Filename, content: str) -> None:
        raise NotImplementedError

    def exists(self, fn: Filename) -> bool:
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

    def append(self, policy: Policy, id: Id) -> None:
        """Append to database with current time."""
        self.database._append(policy, id, self.clock.now())

    def read_url(self, url: Url, policy: Policy) -> Html:
        """Reads url, saving an access record to the database at the same time."""
        fn = self.file_system.key(url)

        if self.file_system.exists(fn):
            return Html(self.file_system.read(fn))

        result = self.url_reader._read(url)
        self.append(policy, Id(""))  # Store the root in Requests db
        self.file_system.write(fn, result)  # Save

        return result


class CacheTag(object):
    # TODO: `tag` may be soup
    def __init__(self, tag: bs4.element.Tag, policy: Policy, engine: PolicyEngine):
        self.tag = tag
        self.policy = policy
        self.engine = engine

        self._id: Optional[Id] = None

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

    def _calc_id(self) -> Id:
        result = list()

        vertical_cursor = self.tag
        while vertical_cursor.name != "[document]":
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


class BeautifulCache(CacheTag):
    def __init__(self, url: Url, policy: Policy, engine: PolicyEngine):
        self.url = url
        self.policy = policy
        # TODO: Default engine if not specified.  Make input param Optional then.
        self.engine = engine

        html = engine.read_url(self.url, self.policy)
        soup = bs4.BeautifulSoup(html, features="lxml")

        super().__init__(soup, self.policy, self.engine)
