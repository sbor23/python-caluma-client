import base64

from .parser import parse_document

ANSWER_TYPE_MAP = {
    "TextQuestion": "StringAnswer",
    "TextareaQuestion": "StringAnswer",
    "IntegerQuestion": "IntegerAnswer",
    "FloatQuestion": "FloatAnswer",
    "MultipleChoiceQuestion": "ListAnswer",
    "ChoiceQuestion": "StringAnswer",
    "DynamicMultipleChoiceQuestion": "ListAnswer",
    "DynamicChoiceQuestion": "StringAnswer",
    "TableQuestion": "TableAnswer",
    "FormQuestion": None,
    "FileQuestion": "FileAnswer",
    "StaticQuestion": None,
    "DateQuestion": "DateAnswer",
}


def decode_id(string):
    if not string:
        return None
    return base64.b64decode(string).decode("utf-8").split(":")[-1]


def answer_value_key(typename):
    return typename.split("Answer")[0].lower() + "Value"


def make_property(constructor, key):
    @property
    def getter(self):
        return constructor(self.raw.get(key))

    return getter


class Form:
    def __init__(self, raw):
        assert raw.get("__typename") == "Form", "raw must be a caluma `Form`"
        self.raw = raw

    uuid = make_property(decode_id, "id")


class Question:
    def __init__(self, raw):
        assert raw.get("__typename").endswith(
            "Question"
        ), "raw must be a caluma `Question`"
        self.raw = raw


class Answer:
    def __init__(self, raw):
        assert raw.get("__typename", "").endswith(
            "Answer"
        ), "raw must be a caluma `Answer`"
        self.raw = raw

    uuid = make_property(decode_id, "id")
    value_key = make_property(answer_value_key, "__typename")

    @property
    def value(self):
        value = self.raw.get(self.value_key)

        if self.raw["__typename"] == "TableAnswer" and value:
            return [Document(parse_document(raw)) for raw in value]
        else:
            return value


class Field:
    def __init__(self, fieldset, raw):
        assert "question" in raw, "Raw must contain Question"

        self.fieldset = fieldset
        self.raw = raw

        self.options = None  # TODO?

    question = make_property(Question, "question")

    @property
    def answer(self):
        if self.raw.get("answer"):
            return Answer(self.raw["answer"])

        question_type = self.raw["question"]["__typename"]
        answer_type = ANSWER_TYPE_MAP.get(question_type)
        if answer_type is None:
            return None

        value_key = answer_value_key(question_type)
        raw = dict(
            zip(
                ("__typename", "question", value_key),
                (answer_type, self.raw["question"].get("slug"), None),
            )
        )
        return Answer(raw)


class Document:
    def __init__(self, raw):
        assert raw.get("__typename") == "Document", "raw must be a caluma `Document`"
        self.raw = raw

    uuid = make_property(decode_id, "id")
    root_form = make_property(Form, "rootForm")

    @property
    def pk(self):
        return f"Document:{self.uuid}"

    @property
    def fieldsets(self):
        return [
            Fieldset(self, {"form": form, "answers": self.raw.get("answers", [])})
            for form in self.raw.get("forms", [])
        ]

    @property
    def fields(self):
        return [field for fields in self.fieldsets for field in fields]

    @property
    def jexl(self):
        raise NotImplementedError("JEXL is not supported by this library")

    def find_answer(self, question_slug):
        raise NotImplementedError

    def find_field(self, slug):
        raise NotImplementedError


class Fieldset:
    def __init__(self, document, raw):
        assert (
            "form" in raw and "answers" in raw
        ), "Raw must contain `form` and `answers`"

        self.raw = raw
        self.document = document

    form = make_property(Form, "form")

    @property
    def fields(self):
        def _find_answer(question):
            return next(
                (
                    answer
                    for answer in self.raw["answers"]
                    if answer.get("question", {}).get("slug") == question.get("slug")
                ),
                None,
            )

        return [
            Field(self, {"question": question, "answer": _find_answer(question)})
            for question in self.raw["form"]["questions"]
        ]

    @property
    def field(self):
        raise NotImplementedError
