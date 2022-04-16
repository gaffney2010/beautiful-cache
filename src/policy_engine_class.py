# type: ignore

import attr

# Omit this from mypy analysis because of the overload.
from overload import overload

from shared_types import *
import tree_crawl


@attr.s()
class BcEngine(object):
    url_reader: UrlReader = attr.ib()
    database: Database = attr.ib()
    file_system: FileSystem = attr.ib()
    clock: Clock = attr.ib()

    @overload
    def append(self, row: Row) -> None:
        """Append to database with current time."""
        self.database._append(row, self.clock.now())

    @append.add
    def append(self, policy: Policy, url: Url, id: Id) -> None:
        self.append(row(policy, url, id))

    def read_url(self, policy: Policy, url: Url) -> Html:
        """Reads url, saving an access record to the database at the same time."""
        if self.file_system.exists(policy, url):
            return Html(self.file_system.read(policy, url))

        # Cast to soup then back, so as to erase whitespace
        untrimmed_html = self.url_reader._read(url)

        html = Html(tree_crawl.trim_html(untrimmed_html))

        self.append(policy, url, Id(""))  # Store the root in Requests db
        self.file_system.write(policy, url, html)  # Save

        return html
