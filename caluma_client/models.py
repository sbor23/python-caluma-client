import base64
from abc import ABC, abstractmethod

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
    def __init__(self, document, raw):
        assert raw.get("__typename") == "Form", "raw must be a caluma `Form`"
        self.root_document = document
        self.raw = raw
        self.fields = [Field(document, question) for question in self.raw["questions"]]

    uuid = make_property(decode_id, "id")


class Question:
    def __init__(self, document, raw):
        assert raw.get("__typename").endswith(
            "Question"
        ), "raw must be a caluma `Question`"
        self.question_type = raw["__typename"]
        self.root_document = document
        self.raw = raw
        self.child_form = None
        if self.question_type == "FormQuestion":
            self.child_form = Form(document, self.raw["subForm"])
        elif self.question_type == "TableQuestion":
            self.child_form = Form(document, self.raw["rowForm"])


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
    def __init__(self, document, raw):
        assert raw.get("__typename", "").endswith(
            "Question"
        ), "Raw must contain Question"
        # self.fieldset = fieldset
        self.root_document = document
        self.raw = raw
        self.options = None  # TODO?
        self.question = Question(document, self.raw)
        # TODO answer

    # question = make_property(Question, "question")
    def _find_answer(self):
        return next(
            (
                answer
                for answer in self.root_document.raw["answers"]
                if answer.get("question", {}).get("slug") == self.question.get("slug")
            ),
            None,
        )

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
        self.form = Form(self, raw.get("form"))

    uuid = make_property(decode_id, "id")
    # form = make_property(Form, "form")

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


class Visitor(ABC):
    def visit(self, node):
        cls_name = type(node).__name__.lower()
        method = getattr(self, "_visit_" + cls_name)
        return method(node)

    @abstractmethod
    def _visit_document(self, node):
        pass

    @abstractmethod
    def _visit_form(self, node):
        pass

    @abstractmethod
    def _visit_field(self, node):
        pass

    @abstractmethod
    def _visit_fieldset(self, node):
        pass

    @abstractmethod
    def _visit_question(self, node):
        pass

    @abstractmethod
    def _visit_answer(self, node):
        pass
