# beautiful-cache
Caching Wrapper for BeautifulSoup.

TODO: Add some overview about compaction.

Work in progress - the below isn't implemented yet.

## Policy
A policy refers to a set of URLs that share a memory space.  They are named by the directory where the files are saved.

TODO: describe the file structure.

## Request database
Every time a tag in the soup is read, we add a message to the Request database.  The messages are formatted like this: "body/div/p:1/a:2", which means take the second `a` tag in the first `p` tag in the first `div` tag in the `body`.  (Note: The `:1` is optional.)  Reading this request will return the entire `a` tag, even if it has subtags.  It will return this as a BeautifulSoup object.  We can access these with usual BeautifulSoup patterns:

```python
schools = soup.find_all("td", {"data-stat": "school_name"})
link = schools[0].find("a").materialize()
```

In the above example, we'd want to store a request "td:3/a".  (Notice that this became "td:3" because only this happened to be the first td with with data-stat equal to school_name.)  But we DON'T want to store "td{data-stat: school_name}", as this is only an intermediate calculation.  This is the purpose of the 

The Request database stores the url and the request string "body/div/p:1/a:2" along with the timestamp.  The url and request string is the key, and each new request upserts, so that the value shows the last time that request was made.

Everytime a URL is freshly downloaded, we record a root request in the database `html`.

The database is a MySQL file called `Requests` saved in the policy directory.  MySQL is not optimal for frequent upsert, but it's the easiest to implement, so it suffices for V1.

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

And your Requests database includes "body/div/p:1/a:2" and "body/div/p:3".  The the `all` strategy would include the entire HTML.  The `fat` strategy would produce:

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

Notice that subtags of "body/div/p:3" are included.

## Compaction
Compaction works by repeatedly deleting the oldest records in the Requests database, then replacing the affected URL caches with an updated version, per the specified request strategy.  This is repeated until only `max_bytes` space is taken up by the files.

When a cache compacts a file by the strategy above, it saves the resulting small HTML as a flat file by saving the str cast of the BeautifulSoup file.

## Cache misses and Transactions.
Whenever tags are accessed, and these don't exist, we assume that they were erased by compaction.  We re-download the URL, and try to find the tag again before returning an error.

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
