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
from policy_engine_class import ConcreteBcEngine
from shared_types import *

print("Hello")

policy = "example_use_case/data"
policy_in_sql = "example_use_case_data"

# Delete old data
# if os.path.exists(os.path.join(policy, "data")):
#     for files in os.listdir(os.path.join(policy, "data")):
#         path = os.path.join(policy, "data", files)
#         os.remove(path)

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
for _ in range(10):
    print(f"{_} @ {time.monotonic()}")
    # TODO: A signature that doesn't require Url-type
    soup = bc.BeautifulCache(Url(tos_index), policy)
    links = list()
    for a in soup.find_all("a", {"rel": "bookmark"}):
        links.append(a.materialize()["href"])


def summary():
    print("Downloaded first page.")
    num_files = len(os.listdir(os.path.join(policy, "data")))
    print(f"{num_files} files with size {ConcreteBcEngine.file_system.size(policy)}")

    cursor = db.cursor()
    cursor.execute(f"SELECT id, url, ts FROM {policy_in_sql} ORDER BY ts LIMIT 100;")
    df_rows = list()
    for row in cursor.fetchall():
        df_rows.append({"url": row[1], "id": row[0], "ts": row[2]})
    db.commit()
    df = pd.DataFrame(df_rows)
    print(tabulate(df))


summary()

for _ in range(2):
    for link in links:
        print(f"Downloading {link}...")
        soup = bc.BeautifulCache(Url(link), policy)
        for p in soup.find_all("p"):
            if str(p.tag).find("Kirk") != -1:
                p.materialize()

summary()

print("Compacting...")
compact(policy, {"max_bytes": 4_600_000, "strategy": "thin"})

summary()

print("Good bye")
