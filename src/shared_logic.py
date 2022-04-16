import bs4  # type: ignore

from shared_types import *


def is_root(node: Ingredient) -> bool:
    return node.parent is None


# Note: This could be sped up by making ID an object that stores hashes for htmls it's
#  been found to work for.  For now this is a premature optimization.
def validate_id(id: Id, html: Html) -> bool:
    """Checks if the id correctly identifies an element in the html."""
    # TODO: Refactor - no exceptions and no recursion
    def _validate(id: Id, ingredient: Ingredient, ind: int) -> bool:
        if ind >= len(id):
            return True

        try:
            id_part = id[ind]
            id_part_parts = id_part.split(":")
            l = len(id_part_parts)
            if l != 2:
                raise BcException(f"ID component {id_part} has {l} parts, expected 2.")
            tag, i = id_part_parts

            # This is where errors are likely to occur.
            child_ingred = ingredient.find_all(tag)[i]

            return _validate(id, child_ingred, ind + 1)
        except:
            # Some error encountered
            return False

    soup = bs4.BeautifulSoup(html, features="lxml")
    return _validate(id, soup, 0)
