import bs4  # type: ignore

import shared_logic
from shared_types import *


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


def isolate_id(html: Html, id: Id) -> Html:
    # TODO: Make a global id valid checker

    def _isolate(working_ingredient: str, id_split: List[str], ind: int) -> str:
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
