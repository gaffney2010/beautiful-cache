import os
from typing import Any, Dict, List, NewType, Optional, Set, Tuple, Union

import attr


Bytes = NewType("Bytes", int)
Filename = str
Html = NewType("Html", str)
Ingredient = Any  # Can be bs4.soup or bs4.tag.  Update later.
Policy = NewType("Policy", str)
Time = NewType("Time", int)  # TODO: What is this?  Ms since epoch?


@attr.s(frozen=True)
class Url(object):
    """I do this so that I can isinstance in the filesystem.

    I may have to do this with other custom types."""

    _x: str = attr.ib()

    def __str__(self) -> str:
        return self._x


class Id(object):
    def __init__(self, id: str):
        # Validate ID
        for part in id.split("/"):
            if part == "":
                continue
            l = len(part.split(":"))
            if l != 2:
                raise BcException(f"Invalid id at creation {id}")

        self._id = id
        self._parts = id.split("/")
        if self._id == "":
            # Special case
            self._parts = list()

        self.valid_htmls = set()

    def __str__(self) -> str:
        return self._id

    def __repr__(self) -> str:
        return self.__str__()

    def __getitem__(self, ind: int) -> str:
        return self._parts[ind]

    def __iter__(self):
        yield from self._parts

    def __len__(self) -> int:
        return len(self._parts)

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self._id == other
        if isinstance(other, Id):
            return self._id == other._id
        raise Exception(f"Unexpected type for id: {type(other)}")

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._id)

    def __add__(self, other: Union["Id", str]) -> "Id":
        if isinstance(other, str):
            if self._id == "":
                return Id(other)
            if other == "":
                return self
            return Id("/".join([self._id, other]))
        if isinstance(other, Id):
            if self._id == "":
                return other
            if other._id == "":
                return self
            return Id("/".join([self._id, other._id]))
        raise Exception(f"Unexpected type for id: {type(other)}")

    def __iadd__(self, other: Union["Id", str]) -> "Id":
        if isinstance(other, str):
            if self._id == "":
                self._id = other
                self._parts = other.split("/")
            elif other == "":
                pass
            else:
                self._id = "/".join([self._id, other])
                self._parts += other.split("/")
            return self
        if isinstance(other, Id):
            if self._id == "":
                self._id = other._id
                self._parts = other._parts
            elif other._id == "":
                pass
            else:
                self._id = "/".join([self._id, other._id])
                self._parts += other._parts
            return self
        raise Exception(f"Unexpected type for id: {type(other)}")


@attr.s(frozen=True)
class Row(object):
    """Represents row keys in the database.

    A database row also has timestamps, but we've chosen to keep these separate, to
    emphasize the other fields' role as unique identifier.
    """

    policy: Policy = attr.ib()
    # We store as strings, because this is designed for database storage
    url: str = attr.ib()
    id: str = attr.ib()

    def get_url(self) -> Url:
        """Handles the cast to Url."""
        return Url(self.url)


def make_row(
    policy: Union[Policy, str], url: Union[Url, str], id: Union[Id, str]
) -> Row:
    # Convenient wrapper, I sup'ose
    if isinstance(id, Id):
        id = str(id)
    if isinstance(url, Url):
        url = str(url)
    if url.find("&url=") != -1:
        # This one weird hack.
        url = url.split("&url=")[1]
    return Row(policy=Policy(policy), url=url, id=id)


@attr.s()
class CompactionRecord(object):
    delete_through: Optional[Time] = attr.ib(default=None)
    records_deleted: List[Row] = attr.ib(default=attr.Factory(list))
    affected_urls: Set[Url] = attr.ib(default=attr.Factory(set))
    records_added: List[Row] = attr.ib(default=attr.Factory(list))
    size_delta: Optional[Bytes] = attr.ib(default=None)
    message: Optional[str] = attr.ib(default=None)


# Make a bunch of abstract base classes.
class UrlReader(object):
    def __init__(self):
        pass

    def _read(self, url: Url) -> Html:
        raise NotImplementedError


class Database(object):
    """The functions here are opinionated to the applications."""

    def __init__(self):
        pass

    # TODO: Should I return a success message or something?
    def _append(self, row: Row, ts: Time) -> None:
        raise NotImplementedError

    def pop(
        self, policy: Policy, priority: str, record: Optional[CompactionRecord] = None
    ) -> Set[Url]:
        """Remove the records with the smallest timestamp and return.

        Additional recording to record if it's passed in.
        """
        raise NotImplementedError

    def exists(self, policy: Policy, url: Url) -> bool:
        """Returns true if any records with the policy/url."""
        raise NotImplementedError

    def pop_query(self, policy: Policy, url: Url) -> Dict[Id, Time]:
        """Deletes all records with the given policy/url.  Returns the IDs/timestamps
        for the deleted rows.
        """
        raise NotImplementedError

    def batch_load(self, rows: List[Tuple[Row, Time]]) -> None:
        """Put all these rows in the table with a timestamp"""
        raise NotImplementedError


class FileSystem(object):
    def __init__(self):
        pass

    def size(self, policy: Policy) -> Bytes:
        """Returns total size of all data files in policy."""
        raise NotImplementedError

    def _key(self, policy: Policy, url: Url) -> Filename:
        """This is what maps a URL to a filename"""
        url_str = str(url)
        if url_str.find("url=") != -1:
            # Hack a special case, just for me.
            url_str = url_str.split("url=")[1]
        return os.path.join("data", url_str.replace("/", "") + ".html")

    def _read_fn(self, policy: Policy, fn: Filename) -> str:
        raise NotImplementedError

    def read(self, policy: Policy, fn: Union[Filename, Url]) -> str:
        if isinstance(fn, Url):
            fn = self._key(policy, fn)
        return self._read_fn(policy, fn)

    def _write_fn(self, policy: Policy, fn: Filename, content: str) -> None:
        raise NotImplementedError

    def write(self, policy: Policy, fn: Union[Filename, Url], content: str) -> None:
        """Write will always overwrite."""
        if isinstance(fn, Url):
            fn = self._key(policy, fn)
        self._write_fn(policy, fn, content)

    def _exists_fn(self, policy: Policy, fn: Filename) -> bool:
        raise NotImplementedError

    def exists(self, policy: Policy, fn: Union[Filename, Url]) -> bool:
        if isinstance(fn, Url):
            fn = self._key(policy, fn)
        return self._exists_fn(policy, fn)

    def _delete_fn(self, policy: Policy, fn: Filename) -> None:
        raise NotImplementedError

    def delete(self, policy: Policy, fn: Union[Filename, Url]) -> None:
        if isinstance(fn, Url):
            fn = self._key(policy, fn)
        self._delete_fn(policy, fn)


class Clock(object):
    def __init__(self):
        pass

    def now(self) -> Time:
        raise NotImplementedError


class BcException(Exception):
    pass
