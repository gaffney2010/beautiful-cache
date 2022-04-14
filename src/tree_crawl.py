import collections
from posixpath import split

import bs4  # type: ignore

import shared_logic
from shared_types import *

# TODO: Test these functions directly.


def _st_tag(ingredient) -> str:
    if shared_logic.is_root(ingredient.parent):
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


def _en_tag(ingredient) -> str:
    if ingredient.parent is None:
        # Corner case for top level [document]
        return ""

    return f"</{ingredient.name}>"


def trim(ingredient) -> str:
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
    id_splits = [id.split("/") for id in ids]

    common_ancestors = list()
    for i in range(len(id_splits[0])):
        # Check that all match
        for id_split in id_splits:
            if i >= len(id_split):
                break
            if id_split[0] != id_splits[0][0]:
                break
        common_ancestors.append(id_splits[i])

    return Id("/".join(common_ancestors))


def isolate_id(html: Html, id: Id) -> Html:
    # TODO: Make a global id valid checker, lru cache it.

    def _isolate(working_ingredient, id_split: List[str], ind: int) -> str:
        if ind == len(id_split):
            return trim(working_ingredient)

        # Find the right ingredient
        tag, i = id_split[ind].split(":")
        working_ingredient = working_ingredient.find_all(tag)[i]
        return (
            _st_tag(working_ingredient)
            + _isolate(working_ingredient, id_split, ind + 1)
            + _en_tag(working_ingredient)
        )

    soup = bs4.BeautifulSoup(html, features="lxml")
    return Html(_isolate(soup, id.split("/"), 0))


def combine_ids(html: Html, ids: List[Id]) -> Html:
    # TODO: Id checks

    # TODO: Make type for IdSplits = List[str]
    def _combine(working_ingredient, id_splits: List[List[str]], ind: int) -> str:
        # Check that we're in a valid state.  This can be removed if too slow.
        for i in range(ind):
            for id_split in id_splits:
                if i >= len(id_split) or id_split[i] != id_splits[0][i]:
                    raise BcException(f"Invalid set of ids in combine_ids: {id_splits}")

        # If this is end for id_split, then we don't have keep descending, return the
        #  whole node.
        for id_split in id_splits:
            if ind == len(id_split):
                return trim(working_ingredient)

        # Convert to look up easier in next step
        split_by_ingred = collections.defaultdict(list)
        for id_split in id_splits:
            split_by_ingred[id_split[ind]].append(id_split)

        result = [_st_tag(working_ingredient)]

        # Loop through all the children, descending when we have IDs that match that.
        tag_counter = collections.defaultdict(int)
        for ingred in working_ingredient.children:
            if ingred.name is None:
                # Not a tag
                continue

            key = f"{ingred.name}:{tag_counter[ingred.name]}"
            if key in split_by_ingred:
                result.append(_combine(ingred, split_by_ingred[key], ind + 1))
            tag_counter[ingred.name] += 1

        result.append(_en_tag(working_ingredient))

        return "".join(result)

    soup = bs4.BeautifulSoup(html, features="lxml")
    id_splits = [id.split("/") for id in ids]
    return Html(soup, id_splits, 0)
