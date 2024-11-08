from typing import Any, Callable, Dict, Optional

from bs4 import BeautifulSoup

# Abstraction because we allow the user to return other objects.
AbstractSoup = Any
Url = str

# Scraper may take additional parameters, but this contract must exist between client
#  and scraper function.
ScraperFn = Callable[[Url, Any], str]


class Cacher(object):
    """Your cache must implement these functions"""

    def __init__(self):
        pass

    def set(self, key: str, value: str, ttl: int) -> None:
        raise NotImplementedError

    def get(self, key: str) -> Optional[str]:
        """Returns None if the key doesn’t exist."""
        raise NotImplementedError


BeautifulSoupFactory = Callable[[str, Any], AbstractSoup]


def beautiful_soup_default_factory(
    html: str, parse_only: Optional[Dict[str, Any]] = None
) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser", parse_only=parse_only)


def cleanup(html: str) -> str:
    """Use this to strip a bunch of nonsense"""
    return html


async def BeautifulCache(
    url: Url,
    scraper: ScraperFn,
    cacher: Cacher,
    parse_only: Optional[Dict[str, Any]] = None,
    ttl_short: int = 86400,  # Given in seconds
    ttl_long: int = 86400 * 365,
    namespace: str = "a",
    beautiful_soup_factory: BeautifulSoupFactory = beautiful_soup_default_factory,
    **scraper_kwargs,
) -> AbstractSoup:
    parse_only_str = "_"
    if parse_only:
        parse_only_str = json.dumps(parse_only)

    result = cacher.get("+".join([namespace, url, parse_only_str]))
    if result:
        return beautiful_soup_factory(result)

    raw_result = None
    if parse_only:
        raw_result = cacher.get("+".join([namespace, url, "_"]))
    if not raw_result:
        raw_result = await scraper(url, **scraper_kwargs)
        raw_result = cleanup(raw_result)
        raw_ttl = ttl_short if parse_only else ttl_long
        cacher.set("+".join([namespace, url, "_"]), raw_result, raw_ttl)

    if not parse_only:
        return beautiful_soup_factory(raw_result)

    result = beautiful_soup_factory(raw_result)
    cacher.set("+".join([namespace, url, parse_only_str], str(result), ttl_long))
    return result
