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
    result = str(ingredient).replace("\n", " ").replace("\t", " ")
    if result[0].isspace():
        result = f" {result.lstrip()}"
    if result[-1].isspace():
        result = f"{result.rstrip()} "
    return result


def trim_html(html: Html) -> Html:
    soup = bs4.BeautifulSoup(html, features="lxml")
    return Html(trim(soup))


def common_ancestor(ids: List[Id]) -> Id:
    ca = Id("")
    for i in range(len(ids[0])):
        # Check that all match
        for id in ids:
            if i >= len(id):
                return ca
            if id[i] != ids[0][i]:
                return ca
        ca += ids[0][i]
    return ca


def mask_id(id: Id, mask: Id) -> Id:
    """Given an Id, map everything up to the mask to tag:0.

    This unusual function is a critical piece of remapping after a fat compaction.

    For example
    -----------
    mask_id("a:1/b:2/c:3/d:7/e:8", "a:1/b:2/c:3") returns "a:0/b:0/c:0/d:7/e:8"
    """
    result = list()
    i = -1  # This value will stay if mask is empty.
    # TODO: mypy doesn't like this.
    for i, xi in enumerate(mask):
        if xi != id[i]:
            raise BcException("Mask error")
        tag, _ = shared_logic.split_id_part(xi)
        result.append(f"{tag}:0")
    # TODO: Add test where id==mask
    # TODO: mypy doesn't like this.
    result += id[i + 1 :]  # i = len(mask) here

    return Id("/".join(result))


def isolate_id(html: Html, id: Id) -> Html:
    if not shared_logic.validate_id(id, html):
        raise BcException(f"Id {id} not valid for HTML")

    def _isolate(working_ingredient: Ingredient, id: Id, ind: int) -> str:
        """Returns working_ingredient with its own tag on only the passed id as
        children."""
        # Base case
        if ind == len(id):
            return trim(working_ingredient)

        # Find the right ingredient
        tag, i = shared_logic.split_id_part(id[ind])
        child_ingredient = working_ingredient.findChildren(tag, recursive=False)[i]

        desc = _isolate(child_ingredient, id, ind + 1)
        return _st_tag(working_ingredient) + desc + _en_tag(working_ingredient)

    soup = bs4.BeautifulSoup(html, features="lxml")
    return Html(_isolate(soup, id, 0))


def _get_common_prefix(ids: List[Id], en: int) -> Id:
    """Asserts that the ids all have the first `en` elements in common, then returns
    these elements as an Id."""
    result = Id("")
    for i in range(en):
        # Check that we're in a valid state.  This can be removed if too slow.
        for id in ids:
            if i >= len(id) or id[i] != ids[0][i]:
                raise BcException(f"Invalid set of ids in combine_ids: {ids}")

        result += ids[0][i]

    return result


def _get_id_part(tag_name: str, counter: DefaultDict[str, int]) -> str:
    """Will return the tag_name with index while updating index in-place"""
    result = f"{tag_name}:{counter[tag_name]}"
    counter[tag_name] += 1
    return result


def combine_ids(html: Html, ids: List[Id], id_mapper: Dict[Id, Id]) -> Html:
    # TODO: This probably needs a docstring
    for id in ids:
        if not shared_logic.validate_id(id, html):
            raise BcException(f"Id {id} not valid for HTML")

    def _combine(
        working_prefix: Id, working_ingredient, ids: List[Id], ind: int
    ) -> str:
        nonlocal id_mapper

        # If this is end for id, then we don't have keep descending, return the whole
        #  node.
        for id in ids:
            if ind == len(id):
                return trim(working_ingredient)

        # Convert to look up easier in next step
        ids_by_ingred = collections.defaultdict(list)
        for id in ids:
            ids_by_ingred[id[ind]].append(id)

        result = [_st_tag(working_ingredient)]

        # Loop through all the children, descending when we have IDs that match that.
        tag_counter: DefaultDict[str, int] = collections.defaultdict(int)
        used_tag_counter: DefaultDict[str, int] = collections.defaultdict(int)
        for ingred in working_ingredient.children:
            if ingred.name is None:
                # Not a tag
                continue

            key = _get_id_part(ingred.name, tag_counter)
            if key in ids_by_ingred:
                old_id = _get_common_prefix(ids, ind) + key
                new_id = working_prefix + _get_id_part(ingred.name, used_tag_counter)
                id_mapper[old_id] = new_id
                result.append(_combine(new_id, ingred, ids_by_ingred[key], ind + 1))

        result.append(_en_tag(working_ingredient))

        return "".join(result)

    soup = bs4.BeautifulSoup(html, features="lxml")
    return Html(_combine(Id(""), soup, ids, 0))
