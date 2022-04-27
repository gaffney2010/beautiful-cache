from typing import Tuple

import bs4  # type: ignore

from .shared_types import *


def is_root(node: Ingredient) -> bool:
    return node.parent is None


def split_id_part(id_part: str) -> Tuple[str, int]:
    tag, i = id_part.split(":")
    return tag, int(i)


# TODO: Add test for <div> child of <div>
def validate_id(id: Id, html: Html) -> bool:
    """Checks if the id correctly identifies an element in the html."""
    h = hash(html)
    if h in id.valid_htmls:
        return True

    ingredient = bs4.BeautifulSoup(html, features="lxml")

    for part in id:
        tag, i = split_id_part(part)

        try:
            ingredient = ingredient.findChildren(tag, recursive=False)[i]
        except:
            return False

    id.valid_htmls.add(h)
    return True
