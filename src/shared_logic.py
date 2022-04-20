from typing import Tuple

import bs4  # type: ignore

from shared_types import *


def is_root(node: Ingredient) -> bool:
    return node.parent is None


def split_id_part(id_part: str) -> Tuple[str, int]:
    tag, i = id_part.split(":")
    return tag, int(i)


# Note: This could be sped up by making ID an object that stores hashes for htmls it's
#  been found to work for.  For now this is a premature optimization.
def validate_id(id: Id, html: Html) -> bool:
    """Checks if the id correctly identifies an element in the html."""
    ingredient = bs4.BeautifulSoup(html, features="lxml")

    print("=================")
    for part in id:
        tag, i = split_id_part(part)
        print(str(ingredient))
        print(tag)
        print(i)

        # try:
        ingredient = ingredient.find_all(tag)[i]
        # except:
        #     return False

    return True
