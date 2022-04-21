# beautiful-cache
Caching Wrapper for BeautifulSoup.

The library includes some compaction logic, which is an operation you can run to delete unused parts of webpages.  See details below.

## Policy
A policy refers to a set of URLs that share a memory space.  They are named by the directory where the files are saved.

Within a directory, the file system would include data, a Requests database, and optionally a settings file (see below).

```
policy_name/
|-- data/
|-- settings.yaml (optional)
```

## Request database
Every time a tag in the soup is read, we add a message to the Request database.  The messages are formatted like this: "body:0/div:0/p:0/a:1", which means take the second `a` tag in the first `p` tag in the first `div` tag in the `body`.  Reading this request will return the entire `a` tag, even if it has subtags.  It will return this as a BeautifulSoup object.  We can access these with usual BeautifulSoup patterns:

```python
schools = soup.find_all("td", {"data-stat": "school_name"})
link = schools[0].find("a").materialize()
```

In the above example, we'd want to store a request "td:2/a:0".  (Notice that this became "td:2" because only this happened to be the first td with with data-stat equal to school_name - full HTML not shown.)  But we DON'T want to store "td:2", as this is only an intermediate calculation.  This is the purpose of the `materialize` functions.

The Request database stores the url and the request string "body:0/div:0/p:0/a:1" along with the timestamp.  The url and request string is the key, and each new request upserts, so that the value shows the last time that request was made.

Everytime a URL is freshly downloaded, we record a root request in the database `html`.

The database is a MySQL table.  MySQL is not optimal for frequent upsert, but it's the easiest to implement, so it suffices for V1.

## Policy settings
These describe how the compaction should work.  This can be passed in compaction time.  If not passed in, then the values will be read from `settings.yaml` in the policy directory.

### max_bytes
Compaction will delete old data until this many bytes remain in the cache (doesn't include Request database).

### strategy
If set to `all`, then it will include the entire HTML file so long as there's a single entry for the URL in the Request database.

If set to `fat`, then it will include everything in the lowest common parent of all the accessed tags in the Request database.  Because code often evolves to include small variants to use data in the same neighborhood; this is recommended for evolving code.

If set to `thin`, then it will only include data accessed in the Request database.

For example, if your HTML was:

```html
<html>
<head></head>
<body>
    <div>
        <p><a>1</a><a>2</a></p>
        <p><a>3</a><a>4</a></p>
        <p>5 <span>my_span</span></p>
    </div>
    <div>
        <p><a>6</a> 7 and beyond</p>
    </div>
</body>
</html>
```

And your Requests database includes "body:0/div:0/p:0/a:1" and "body:0/div:0/p:2".  The the `all` strategy would include the entire HTML.  The `fat` strategy would produce:

```html
<html>
<body>
    <div>
        <p><a>1</a><a>2</a></p>
        <p><a>3</a><a>4</a></p>
        <p>5 <span>my_span</span></p>
    </div>
</body>
</html>
```

The lowest common parent is the `div` tag.  Notice that the parent tags of the `div` are included, but not those parents' other children.  The `thin` strategy would produce:

```html
<html>
<head></head>
<body>
    <div>
        <p><a>2</a></p>
        <p>5 <span>my_span</span></p>
    </div>
</body>
</html>
```

Notice that subtags of "body:0/div:0/p:2" are included.

### priority

If set to `fifo` (defualt), then will delete the oldest rows in Requests first.

If set to `root-first`, then will delete root entries in Requests (id="") in order, then other rows in order.

If set to `root-only`, then will delete root entries in order, then stop.  May not be less than `max_bytes`.

## Compaction
Compaction works by repeatedly deleting the oldest records in the Requests database, then replacing the affected URL caches with an updated version, per the specified request strategy.  This is repeated until only `max_bytes` space is taken up by the files.

When a cache compacts a file by the strategy above, it saves the resulting small HTML as a flat file by saving the str cast of the BeautifulSoup file.

## Transactions.

TODO: Implement transactions.

Some queries could fail subtly if a partial compaction occurs.

```python
schools = soup.find_all("td", {"data-stat": "school_name"})
for school in schools:
    link = school.find("a")
```

For this we have transactions:

```python
t = bc.Transaction()
schools = soup.find_all("td", {"data-stat": "school_name"}, t=t)
for school in schools:
    link = school.find("a", t=t)
```

This simply tells these records to record with the same timestamp.  Whenever compaction deletes a record, it deletes ALL records with the same timestamp.

## Sample code
```python
soup = bc.BeautifulCache(url, policy)
schools = soup.find_all("td", {"data-stat": "school_name"})
# The materialize returns the usual BeautifulSoup objects.
link = schools[0].find("a").materialize()
```

Later to compact.  (Maybe be run manually or scheduled.)
```python
bc.Compact(policy, settings={"max_bytes": 1e9, "strategy": "fat"})
```

## Web-driver
For V1, we'll use the Selenium FireFox headless driver.  This requires special download (google Selenium).  We'll retry 3 times with no jitters.  Because the program may download at any time, it's not recommended that this is ever run in parallel.

Future versions may allow different drivers to be injected.  (Or at least document install process better.)

## Supported code
Our V1 will support only `find_all` and `find` with all the usual arguments.  From there additional functionality can be used by materializing the tag, then working with the BeautifulSoup objects.

In future versions, we could easily support other tag-returning functions.

## Over-compaction
Compaction may introduce subtle bugs to code.  For example, you may try to read a field that you think exists, but it is missing.  Or you may operate under the false assumption that you have all the fields of a type.  We call such bugs "over-compaction."  Rather than try to make BeautifulCache smart about these cases, we let the library be dumb, and caution clients to be wary of over-compaction.  BeautifulCache works best for happy paths that do consistent operations over expected data.  It may not be appropriate for every use case.  Note also that when using the 'all' strategy, BeautifulCache acts as simply an LRU cache.
