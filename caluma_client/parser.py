def _unpack_dict(dictionary, levels):
    if not levels:
        return dictionary
    current = levels[0]
    try:
        current = int(current)
    except ValueError:
        pass
    return _unpack_dict(dictionary[current], levels[1:])


def parse_document(response, nesting=""):
    if nesting:
        levels = nesting.split(".")
        try:
            response = _unpack_dict(response, levels)
        except KeyError:
            raise ValueError("Nesting does not match the given response")

    return {
        **response,
        "rootForm": parse_form(response["form"]),
        "answers": [edge["node"] for edge in response["answers"]["edges"]],
        "forms": parse_form_tree(response["form"]),
    }


def parse_form(response):
    return {
        **response,
        "questions": [edge["node"] for edge in response["questions"]["edges"]],
    }


def parse_form_tree(response):
    form = parse_form(response)
    ret = [form]

    for question in form["questions"]:
        subform = question.get("subForm")
        if subform:
            ret.extend(parse_form_tree(subform))

    return ret
