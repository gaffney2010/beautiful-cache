
def _st_tag(ingredient) -> str:
    if ingredient.parent is None:
        # Corner case for top level [document]
        return ""

    guts = [ingredient.name]
    for k, v in ingredient.attrs.items():
        attr_bits = [k]
        if v:
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