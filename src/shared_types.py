from typing import NewType

import attr


Filename = NewType("Filename", str)
Html = NewType("Html", str)
Id = NewType("Id", str)
Policy = NewType("Policy", str)
Time = NewType("Time", int)  # TODO: What is this?  Ms since epoch?
Url = NewType("Url", str)


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


class BcException(Exception):
    pass
