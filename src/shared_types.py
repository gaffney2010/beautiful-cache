import os
from typing import Any, List, NewType, Tuple, Union

import attr


Bytes = NewType("Bytes", int)
Filename = str
Html = NewType("Html", str)
Ingredient = Any  # Can be bs4.soup or bs4.tag.  Update later.
Policy = NewType("Policy", str)
Time = NewType("Time", int)  # TODO: What is this?  Ms since epoch?
Url = NewType("Url", str)


class Id(object):
    def __init__(self, id: str):
        self._id = id
        self._parts = id.split("/")

    def __str__(self) -> str:
        return self._id

    def __getitem__(self, ind: int) -> str:
        return self._parts[ind]

    def __len__(self) -> int:
        return len(self._parts)

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self._id == other
        if isinstance(other, Id):
            return self._id == other._id
        raise Exception(f"Unexpected type for id: {type(other)}")

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
        if isinstance(other, Id):
            if self._id == "":
                self._id = other._id
                self._parts = other._parts
            elif other._id == "":
                pass
            else:
                self._id = "/".join([self._id, other._id])
                self._parts += other._parts
        raise Exception(f"Unexpected type for id: {type(other)}")


@attr.s(frozen=True)
class Row(object):
    policy: Policy = attr.ib()
    url: Url = attr.ib()
    # We store as a string, because this is designed for database storage
    id: str = attr.ib()

    def match(self, other: "Row") -> bool:
        """Check matching with wildcards.  Can use == for non-wildcard matching"""
        policy_match = self.policy == other.policy
        if self.policy == "*" or other.policy == "*":
            policy_match = True

        url_match = self.url == other.url
        if self.url == "*" or other.url == "*":
            url_match = True

        id_match = self.id == other.id
        if self.id == "*" or other.id == "*":
            id_match = True

        return policy_match and url_match and id_match


def make_row(policy: Union[Policy, str], url: Union[Url, str], id: Union[Id, str]) -> Row:
    # Convenient wrapper, I sup'ose
    if isinstance(id, Id):
        id = str(id)
    return Row(policy=Policy(policy), url=Url(url), id=id)


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
    # TODO: Should these signatures should take policy separately for safety?
    #  TODO: Actually I could make Row into just Ui.  :/
    def _append(self, row: Row, ts: Time) -> None:
        raise NotImplementedError

    def query(self, row: Row) -> List[Row]:
        """Returns all the records in the database matching the passed row upto
        wildcard characters.

        A wildcard character is a "*".  When the entire record is a wildcard, then that
        matches any record.  '*' as part of a longer string is not treated as a
        wildcard.
        """
        raise NotImplementedError

    def pop(self, policy: Policy) -> List[Row]:
        """Remove the records with the smallest timestamp, and return."""
        raise NotImplementedError

    def pop_query(self, row: Row) -> List[Tuple[Row, Time]]:
        """Does the same as query, but removes the rows from the database.

        Also returns the timestamps with it.
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
        return os.path.join(policy, url.replace("/", "") + ".data")

    def read(self, policy: Policy, url: Url) -> str:
        raise NotImplementedError

    def write(self, policy: Policy, url: Url, content: str) -> None:
        raise NotImplementedError

    def exists(self, policy: Policy, url: Url) -> bool:
        raise NotImplementedError

    def delete(self, policy: Policy, url: Url) -> None:
        raise NotImplementedError


class Clock(object):
    def __init__(self):
        pass

    def now(self) -> Time:
        raise NotImplementedError


class BcException(Exception):
    pass
