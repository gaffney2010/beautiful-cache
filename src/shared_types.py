import os
from typing import List, NewType, Tuple, Union

import attr


Bytes = NewType("Bytes", int)
Filename = str
Html = NewType("Html", str)
Id = NewType("Id", str)
Policy = NewType("Policy", str)
Time = NewType("Time", int)  # TODO: What is this?  Ms since epoch?
Url = NewType("Url", str)


# TODO: Pui isn't great, because this may evolve
@attr.s(frozen=True)
class Pui(object):
    policy: Policy = attr.ib()
    url: Url = attr.ib()
    id: Id = attr.ib()

    def match(self, other: "Pui") -> bool:
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


# TODO: Call make_pui or something
def pui(policy: Union[Policy, str], url: Union[Url, str], id: Union[Id, str]) -> Pui:
    # Convenient wrapper, I sup'ose
    return Pui(policy=Policy(policy), url=Url(url), id=Id(id))


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
    def _append(self, pui: Pui, ts: Time) -> None:
        raise NotImplementedError

    def query(self, pui: Pui) -> List[Pui]:
        """Returns all the records in the database matching the passed pui upto
        wildcard characters.

        A wildcard character is a "*".  When the entire record is a wildcard, then that
        matches any record.  '*' as part of a longer string is not treated as a
        wildcard.
        """
        raise NotImplementedError

    def pop(self, policy: Policy) -> List[Pui]:
        """Remove the records with the smallest timestamp, and return."""
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
