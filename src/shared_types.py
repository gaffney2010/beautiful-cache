from typing import List, NewType, Tuple, Union

import attr


Bytes = NewType("Bytes", int)
Filename = NewType("Filename", str)
Html = NewType("Html", str)
Id = NewType("Id", str)
Policy = NewType("Policy", str)
Time = NewType("Time", int)  # TODO: What is this?  Ms since epoch?
Url = NewType("Url", str)


@attr.s(frozen=True)
class Pfi(object):
    policy: Policy = attr.ib()
    filename: Filename = attr.ib()
    id: Id = attr.ib()

    def match(self, other: "Pfi") -> bool:
        """Check matching with wildcards.  Can use == for non-wildcard matching"""
        policy_match = self.policy == other.policy
        if self.policy == "*" or other.policy == "*":
            policy_match = True

        filename_match = self.filename == other.filename
        if self.filename == "*" or other.filename == "*":
            filename_match = True

        id_match = self.id == other.id
        if self.id == "*" or other.id == "*":
            id_match = True

        return policy_match and filename_match and id_match


# TODO: Call make_pfi or something
def pfi(
    policy: Union[Policy, str], filename: Union[Filename, str], id: Union[Id, str]
) -> Pfi:
    # Convenient wrapper, I sup'ose
    return Pfi(policy=Policy(policy), filename=Filename(filename), id=Id(id))


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
    def _append(self, pfi: Pfi, ts: Time) -> None:
        raise NotImplementedError

    def query(self, pfi: Pfi) -> List[Pfi]:
        """Returns all the records in the database matching the passed pfi upto
        wildcard characters.

        A wildcard character is a "*".  When the entire record is a wildcard, then that
        matches any record.  '*' as part of a longer string is not treated as a
        wildcard.
        """
        raise NotImplementedError

    def pop(self, policy: Policy) -> List[Pfi]:
        """Remove the records with the smallest timestamp, and return."""
        raise NotImplementedError


# TODO: All these endpoints need to take policy somehow
class FileSystem(object):
    def __init__(self):
        pass

    def size(self, policy: Policy) -> Bytes:
        """Returns total size of all data files in policy."""
        raise NotImplementedError

    def key(self, url: Url) -> Filename:
        return Filename(url.replace("/", "") + ".data")

    def read(self, fn: Filename) -> str:
        raise NotImplementedError

    def write(self, fn: Filename, content: str) -> None:
        raise NotImplementedError

    def exists(self, fn: Filename) -> bool:
        raise NotImplementedError

    def delete(self, policy: Policy, fn: Filename) -> None:
        raise NotImplementedError


class Clock(object):
    def __init__(self):
        pass

    def now(self) -> Time:
        raise NotImplementedError


class BcException(Exception):
    pass
