"""We start with all the code in one file, but this will evolve later."""

from typing import Callable, Dict

import attr


# TODO: Use shared_types paradigm.  Sooner would be great!
Html = str
Url = str
# TODO: What is this?  Ms since epoch?
Time = int
Row = Dict[str, str]


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