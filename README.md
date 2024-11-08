# beautiful-cache
Caching Wrapper for BeautifulSoup.

Principles guiding 2.0 rewrite:
- Inject scraper and cacher, allow for BeautifulSoup injection optionally.
- Lean on SoupStrainer for minimal footprint
- Support TTLs and cache invalidation
- Light-weight (thin)
- Async on scraper

## Sample code
```python
# Notice that isolation_level=None, to support parallelization.
db = sqlite3.connect(f"{policy}/requests.db", isolation_level=None)
web_driver = bc.WebDriver()
engine = bc.bc_engine_factory(db, web_driver, lazy=False)
soup = bc.BeautifulCache(url, policy)
schools = soup.find_all("td", {"data-stat": "school_name"})
# The materialize returns the usual BeautifulSoup objects.
link = schools[0].find("a").materialize()
```

Later to compact.  (Maybe be run manually or scheduled.)
```python
bc.Compact(policy, settings={"max_bytes": 1e9, "strategy": "fat"})
```

See sample use cases for more examples.

