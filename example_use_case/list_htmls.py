"""This will download a bunch of Captain Kirk fan fiction.

Should be run from Beautiful-Cache top-level dir.
"""

import os
import time

import mysql.connector
import pandas as pd
from tabulate import tabulate

import bc
from compaction import compact
from constants import *
from policy_engine_class import *
from shared_types import *

# Make a cached URL reader
class CachedUrlReader(ConcreteUrlReader):
    def _read(self, url: Url) -> Html:
        key = str(url).replace("/", "") + ".html"
        if os.path.exists(os.path.join("example_use_case/data/raw_html", key)):
            with open(os.path.join("example_use_case/data/raw_html", key), "r") as f:
                return Html(f.read())

        with WebDriver() as driver:
            page_text = self._read_url_to_string_helper(url, self.driver)

        with open(os.path.join("example_use_case/data/raw_html", key), "w") as f:
            f.write(page_text)

        return Html(page_text)


engine = LazyBcEngine
engine.url_reader = CachedUrlReader()

print("Hello")

policy = "example_use_case/data"
policy_in_sql = "example_use_case_data"

# Delete old data
if os.path.exists(os.path.join(policy, "data")):
    for files in os.listdir(os.path.join(policy, "data")):
        path = os.path.join(policy, "data", files)
        os.remove(path)

# Clear the db
db = mysql.connector.connect(
    host="localhost",
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB,
)
cursor = db.cursor()
cursor.execute(f"DELETE FROM {policy_in_sql} WHERE 1=1;")
db.commit()

tos_index = "https://trekfanfiction.net/category/the-original-series/#14"

# Should only download once.
soup = bc.BeautifulCache(Url(tos_index), policy, engine=engine)
links = list()
for a in soup.find_all("a", {"rel": "bookmark"}):
    links.append(a.materialize()["href"])

for link in links:
    print(link)

print("by")
