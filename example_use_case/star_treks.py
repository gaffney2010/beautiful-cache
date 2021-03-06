"""This will download a bunch of Captain Kirk fan fiction.  It only materializes paragraphs that mention Kirk.

Should be run from Beautiful-Cache top-level dir.
"""

import os
import sqlite3
import time

import pandas as pd
from tabulate import tabulate

import beautifulcache as bc

# Put these secrets in a file, don't upload.
from computer_constants import MYSQL_USER, MYSQL_PASSWORD


print("Hello")

policy = "example_use_case/data"
policy_in_sql = "example_use_case_data"


# Delete old data
if os.path.exists(os.path.join(policy, "data")):
    for files in os.listdir(os.path.join(policy, "data")):
        path = os.path.join(policy, "data", files)
        os.remove(path)

# Clear the db
db = sqlite3.connect(f"{policy}/requests.db", isolation_level=None)
cursor = db.cursor()
cursor.execute(f"DELETE FROM {policy_in_sql} WHERE 1=1;")
db.commit()


web_driver = bc.WebDriver()


# Make a cached URL reader
class CachedUrlReader(bc.policy_engine_class.ConcreteUrlReader):
    def _read(self, url: bc.Url) -> bc.Html:
        key = str(url).replace("/", "") + ".data"
        if os.path.exists(os.path.join("example_use_case/data/raw_html", key)):
            with open(os.path.join("example_use_case/data/raw_html", key), "r") as f:
                return bc.Html(f.read())

        page_text = self._read_url_to_string_helper(url, self.driver)

        with open(os.path.join("example_use_case/data/raw_html", key), "w") as f:
            f.write(page_text)

        return bc.Html(page_text)


tos_index = "https://trekfanfiction.net/category/the-original-series/#14"
# TODO: Change to lazy = True when that works.
engine = bc.bc_engine_factory(db, web_driver, lazy=False)
engine.url_reader = CachedUrlReader(web_driver)


# Should only download once, despite being asked 10 times.
for _ in range(10):
    print(f"{_} @ {time.time()}")
    # TODO: A signature that doesn't require Url-type
    soup = bc.BeautifulCache(tos_index, policy, engine=engine)
    links = list()
    for a in soup.find_all("a", {"rel": "bookmark"}):
        links.append(a.materialize()["href"])


def summary():
    print("Downloaded first page.")
    num_files = len(os.listdir(os.path.join(policy, "data")))
    print(f"{num_files} files with size {engine.file_system.size(policy)}")

    cursor = db.cursor()
    cursor.execute(f"SELECT id, url, ts FROM {policy_in_sql} ORDER BY ts LIMIT 100;")
    df_rows = list()
    for row in cursor.fetchall():
        df_rows.append({"url": row[1], "id": row[0], "ts": row[2]})
    db.commit()
    df = pd.DataFrame(df_rows)
    print(tabulate(df))


# engine.database.commit()  # Must be manually commited with lazy
summary()

for link in links:
    print(f"Downloading {link}...")
    soup = bc.BeautifulCache(link, policy, engine=engine)
    for p in soup.find_all("p"):
        if str(p.tag).find("Kirk") != -1:
            # Only materialize paragraphs with Kirk in them.
            p.materialize()

# engine.database.commit()
summary()

print("Compacting...")

compaction_engine = bc.bc_engine_factory(
    db, web_driver, lazy=False
)  # Non-lazy for compactions

# Should only compact roots, using thin strategy
bc.compact(
    policy,
    compaction_engine,
    settings={"max_bytes": 0, "strategy": "thin", "priority": "root-only"},
)

summary()

# Do not forget this!
web_driver.quit()

# You can look at the HTML files now.  Only Kirk-related paragraphs remain.

print("Good bye")
