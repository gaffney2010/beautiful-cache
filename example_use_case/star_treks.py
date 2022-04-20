"""This will download a bunch of Captain Kirk fan fiction.

Should be run from Beautiful-Cache top-level dir.
"""

import os
import shutil

import mysql.connector

import bc
from constants import *
from shared_types import *

print("Hello")

policy = "example_use_case/data"
policy_in_sql = "example_use_case_data"

# Ensure this folder exist, and is empty.
if not os.path.exists(policy):
    os.makedirs(policy)
for files in os.listdir(policy):
    # TODO: The function should make this folder if needed
    if files == "data":
        # Keep the folder.
        continue
    path = os.path.join(policy, files)
    try:
        shutil.rmtree(path)
    except OSError:
        os.remove(path)

# Clear the db
db = mysql.connector.connect(
            host="localhost",
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
        )
cursor = db.cursor()
cursor.execute(f"DELETE FROM {policy_in_sql} WHERE 1=1")
db.commit()

tos_index = "https://trekfanfiction.net/category/the-original-series/#14"

# TODO: A signature that doesn't require Url-type
soup = bc.BeautifulCache(Url(tos_index), policy)
links = list()
for a in soup.find_all("a", {"rel": "bookmark"}):
    links.append(a.materialize()["href"])
print(links)

print("Good bye")
