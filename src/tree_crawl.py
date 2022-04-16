import collections
from typing import DefaultDict, Dict, List

import bs4  # type: ignore

import shared_logic
from shared_types import *

# TODO: Test these functions directly.


def _st_tag(ingredient: Ingredient) -> str:
    if shared_logic.is_root(ingredient):
        # Corner case for top level [document]
        return ""

    guts = [ingredient.name]
    for k, v in ingredient.attrs.items():
        attr_bits = [k]
        # TODO: Test tag like <p div="d1 d2">
        if v:
            if isinstance(v, str):
                # I don't know why this happens sometimes
                v = [v]
            attr_bits.append('"' + " ".join(v) + '"')
        guts.append("=".join(attr_bits))
    middle = " ".join(guts)
    return f"<{middle}>"


def _en_tag(ingredient: Ingredient) -> str:
    if ingredient.parent is None:
        # Corner case for top level [document]
        return ""

    return f"</{ingredient.name}>"


def trim(ingredient: Ingredient) -> str:
    has_children = False
    try:
        children = ingredient.children
        has_children = True
    except:
        pass

    if has_children:
        parts = [_st_tag(ingredient)]
        for child in children:
            parts.append(trim(child))
        parts.append(_en_tag(ingredient))
        return "".join(parts)

    # No children - replace many end spaces with a single space
    result = str(ingredient).replace("\n", " ")
    if result[0].isspace():
        result = f" {result.lstrip()}"
    if result[-1].isspace():
        result = f"{result.rstrip()} "
    return result


def trim_html(html: Html) -> Html:
    soup = bs4.BeautifulSoup(html, features="lxml")
    return Html(trim(soup))


def common_ancestor(ids: List[Id]) -> Id:
    # TODO: Id checks

    # TODO: This doesn't need to be a subfunction.  I don't know why this happened.
    def _common_ancestors(ids: List[Id]) -> List[str]:
        """Make a sub functions for those lovely return statements"""
        common_ancestors: List[str] = list()
        for i in range(len(ids[0])):
            # Check that all match
            for id in ids:
                if i >= len(id):
                    return common_ancestors
                if id[i] != ids[0][i]:
                    return common_ancestors
            common_ancestors.append(ids[0][i])
        return common_ancestors

    return Id("/".join(_common_ancestors(ids)))


def mask_id(id: Id, mask: Id) -> Id:
    """Given an Id, map everything up to the mask to tag:0.

    This unusual function is a critical piece of remapping after a fat compaction.

    For example
    -----------
    mask_id("a:1/b:2/c:3/d:7/e:8", "a:1/b:2/c:3") returns "a:0/b:0/c:0/d:7/e:8"
    """
    result = list()
    # TODO: mypy doesn't like this.
    for i, xi in enumerate(mask):
        assert xi == id[i]
        tag, _ = xi.split(":")
        result.append(f"{tag}:0")
    # TODO: Add test where id==mask
    # TODO: mypy doesn't like this.
    result += id[i + 1 :]  # i = len(mask) here

    return Id("/".join(result))


def isolate_id(html: Html, id: Id) -> Html:
    # TODO: Consider making this validity check also thing that converts.
    # TODO: Make a global id valid checker, lru cache it.

    def _isolate(working_ingredient, id: Id, ind: int) -> str:
        if ind == len(id):
            return trim(working_ingredient)

        # Find the right ingredient
        tag, i = id[ind].split(":")
        # Validity of id checked alredy
        i = int(i)  # type: ignore
        working_ingredient = working_ingredient.find_all(tag)[i]

        # TODO: I hate this.
        # Handle next to base case special
        desc = _isolate(working_ingredient, id, ind + 1)
        if ind + 1 == len(id):
            return desc
        return _st_tag(working_ingredient) + desc + _en_tag(working_ingredient)

    soup = bs4.BeautifulSoup(html, features="lxml")
    return Html(_isolate(soup, id, 0))


# TODO: This could probably be split.
def combine_ids(html: Html, ids: List[Id], id_mapper: Dict[Id, Id]) -> Html:
    # TODO: This probably needs a docstring
    # TODO: Id checks

    def _combine(new_prefix: Id, working_ingredient, ids: List[Id], ind: int) -> str:
        # TODO: This probably needs a docstring
        nonlocal id_mapper

        # Check that we're in a valid state.  This can be removed if too slow.
        for i in range(ind):
            for id in ids:
                if i >= len(id) or id[i] != ids[0][i]:
                    raise BcException(f"Invalid set of ids in combine_ids: {ids}")
        # TODO: mypy doesn't like this.
        old_prefix: List[str] = ids[0][:ind]  # Well-defined

        # If this is end for id, then we don't have keep descending, return the whole
        #  node.
        for id in ids:
            if ind == len(id):
                return trim(working_ingredient)

        # Convert to look up easier in next step
        id_by_ingred = collections.defaultdict(list)
        for id in ids:
            id_by_ingred[id[ind]].append(id)

        result = [_st_tag(working_ingredient)]

        # Loop through all the children, descending when we have IDs that match that.
        tag_counter: DefaultDict[str, int] = collections.defaultdict(int)
        used_tag_counter: DefaultDict[str, int] = collections.defaultdict(int)
        for ingred in working_ingredient.children:
            if ingred.name is None:
                # Not a tag
                continue

            key = f"{ingred.name}:{tag_counter[ingred.name]}"
            if key in id_by_ingred:
                old_id = Id("/".join(old_prefix + [key]))
                new_id = new_prefix + f"{ingred.name}:{used_tag_counter[ingred.name]}"
                id_mapper[old_id] = new_id
                result.append(_combine(new_id, ingred, id_by_ingred[key], ind + 1))
            tag_counter[ingred.name] += 1

        result.append(_en_tag(working_ingredient))

        return "".join(result)

    soup = bs4.BeautifulSoup(html, features="lxml")
    return Html(_combine(Id(""), soup, ids, 0))
