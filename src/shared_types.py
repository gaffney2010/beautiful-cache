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

    def size(self, policy: Policy) -> Bytes:
        """Returns total size of all data files in policy."""
        raise NotImplementedError

    def query_id(self, policy: Policy, file: Filename) -> List[Id]:
        """Returns the set of ids in the database for the given policy / filename."""
        raise NotImplementedError

    def pop(self, policy: Policy) -> List[Pfi]:
        """Remove the records with the smallest timestamp, and return."""
        raise NotImplementedError


# TODO: All these endpoints need to take policy somehow
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


class BcException(Exception):
    pass
