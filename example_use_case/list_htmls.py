"""This is for some other use.  Pls don't read.
"""

import os
import time

import mysql.connector
import pandas as pd
from tabulate import tabulate

import beautifulcache as bc

# Put these secrets in a file, don't upload.
from computer_constants import MYSQL_USER, MYSQL_PASSWORD


db = mysql.connector.connect(
    host="localhost",
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database="bc",
)
engine = bc.bc_engine_factory(db, lazy=True)

tos_index = "https://trekfanfiction.net/category/the-original-series/#14"
policy = "example_use_case/links-data"

soup = bc.BeautifulCache(tos_index, policy, engine)
links = list()
for a in soup.find_all("a", {"rel": "bookmark"}):
    links.append(a.materialize()["href"])

for link in links:
    print(link)
