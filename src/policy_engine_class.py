import attr
# Omit this from mypy analysis because of the overload.
from overload import overload

from shared_types import *
import tree_crawl


# TODO: Rename PolicyEngine
# TODO: Should PolicyEngine hold the policy?
@attr.s()
class PolicyEngine(object):
    url_reader: UrlReader = attr.ib()
    database: Database = attr.ib()
    file_system: FileSystem = attr.ib()
    clock: Clock = attr.ib()

    @overload
    def append(self, pfi: Pfi) -> None:
        """Append to database with current time."""
        self.database._append(pfi, self.clock.now())

    @append.add
    def append(self, policy: Policy, filename: Filename, id: Id) -> None:
        self.append(pfi(policy, filename, id))

    # TODO: Put policy first.
    def read_url(self, url: Url, policy: Policy) -> Html:
        """Reads url, saving an access record to the database at the same time."""
        fn = self.file_system.key(url)

        if self.file_system.exists(fn):
            return Html(self.file_system.read(fn))

        # Cast to soup then back, so as to erase whitespace
        untrimmed_html = self.url_reader._read(url)

        html = Html(tree_crawl.trim_html(untrimmed_html))

        self.append(policy, fn, Id(""))  # Store the root in Requests db
        self.file_system.write(fn, html)  # Save

        return html
