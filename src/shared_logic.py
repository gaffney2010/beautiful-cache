import bs4  # type: ignore

from shared_types import *


def is_root(node: Ingredient) -> bool:
    return node.parent is None


# Note: This could be sped up by making ID an object that stores hashes for htmls it's
#  been found to work for.  For now this is a premature optimization.
def validate_id(id: Id, html: Html) -> bool:
    """Checks if the id correctly identifies an element in the html."""
    ingredient = bs4.BeautifulSoup(html, features="lxml")

    for ind in range(len(id)):
        id_part = id[ind]
        id_part_parts = id_part.split(":")
        l = len(id_part_parts)
        if l != 2:
            return False
        tag, i = id_part_parts
        i = int(i)  # type: ignore

        try:
            ingredient = ingredient.find_all(tag)[i]
        except:
            return False

    return True
