def _unpack_dict(dictionary, levels):
    if not levels:
        return dictionary
    current = levels[0]
    try:
        current = int(current)
    except ValueError:
        pass
    return _unpack_dict(dictionary[current], levels[1:])


def _flatten(dictionary, key, func=lambda x: x):
    return [func(edge["node"]) for edge in dictionary[key]["edges"]]


def parse_document(response, nesting=""):
    if nesting:
        levels = nesting.split(".")
        try:
            response = _unpack_dict(response, levels)
        except KeyError:
            raise ValueError("Nesting does not match the given response")

    return {
        **response,
        "form": parse_form(response["form"]),
        "answers": _flatten(response, "answers", parse_answer),
    }


def parse_form(response):
    return {**response, "questions": _flatten(response, "questions", parse_question)}


def parse_question(response):
    ret = {**response}

    if "subForm" in response:
        ret["subForm"] = parse_form(response["subForm"])
    elif "rowForm" in response:
        ret["rowForm"] = parse_form(response["rowForm"])
    elif "choiceOptions" in response:
        ret["choiceOptions"] = _flatten(response, "choiceOptions")
    elif "multipleChoiceQuestion" in response:
        ret["multipleChoiceQuestion"] = _flatten(response, "multipleChoiceQuestion")

    return ret


def parse_answer(response):
    ret = {**response}
    ret["question"] = parse_question(response["question"])
    if "tableValue" in response:
        ret["tableValue"] = [parse_document(doc) for doc in response["tableValue"]]
    return ret
