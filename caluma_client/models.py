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
    "FormQuestion": "FormAnswer",
    "FileQuestion": "FileAnswer",
    "StaticQuestion": None,
    "DateQuestion": "DateAnswer",
}


def decode_id(string):
    return base64.b64decode(string).decode("utf-8").split(":")[-1]


def answer_value_key(typename):
    return typename.split("Answer")[0].lower() + "Value"


class Document:
    def __init__(self, raw):
        assert raw.get("__typename") == "Document", "raw must be a caluma `Document`"

        self.raw = raw
        self.uuid = decode_id(self.raw["id"])
        self.pk = f"Document:{self.uuid}"
        self.root_form = None
        self.fieldsets = []

        self._create_root_form()
        self._create_fieldsets()

    def _create_root_form(self):
        self.root_form = Form(self.raw["rootForm"])

    def _create_fieldsets(self):
        self.fieldsets = [
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
        # TODO
        raise NotImplementedError

    def find_field(self, slug):
        # TODO
        raise NotImplementedError


class Fieldset:
    def __init__(self, document, raw):
        assert (
            "form" in raw and "answers" in raw
        ), "Raw must contain `form` and `answers`"

        self.document = document
        self.raw = raw
        self.form = None
        self.fields = []

        self._create_form()
        self._create_fields()

    def _create_form(self):
        self.form = Form(self.raw.get("form"))

    def _create_fields(self):
        def _find_answer(question):
            return next(
                (
                    answer
                    for answer in self.raw["answers"]
                    if answer.get("question", {}).get("slug") == question.get("slug")
                ),
                None,
            )

        self.fields = [
            Field(self, {"question": question, "answer": _find_answer(question)})
            for question in self.raw["form"]["questions"]
        ]

    @property
    def field(self):
        raise NotImplementedError


class Field:
    def __init__(self, fieldset, raw):
        assert "question" in raw, "Raw must contain Question"

        self.fieldset = fieldset
        self.raw = raw

        self.question = Question(self.raw["question"])
        self.answer = None
        self.options = None  # TODO?
        self._create_answer()

    def _create_answer(self):
        if self.raw.get("answer"):
            self.answer = Answer(self.raw["answer"])
            return

        question_type = self.raw["question"]["__typename"]
        answer_type = ANSWER_TYPE_MAP.get(question_type)
        if answer_type is None:
            return

        value_key = answer_value_key(question_type)
        raw = dict(
            zip(
                ("__typename", "question", value_key),
                (answer_type, self.raw["question"].get("slug"), None),
            )
        )
        self.answer = Answer(raw)


class Form:
    def __init__(self, raw):
        assert raw.get("__typename") == "Form", "raw must be a caluma `Form`"

        self.raw = raw

    @property
    def uuid(self):
        return decode_id(self.raw["id"]) if "id" in self.raw else None


class Question:
    def __init__(self, raw):
        assert raw.get("__typename").endswith(
            "Question"
        ), "raw must be a caluma `Question`"
        self.raw = raw
        # self.is_choice = raw["__typename"].


class Answer:
    def __init__(self, raw):
        assert raw.get("__typename", "").endswith(
            "Answer"
        ), "raw must be a caluma `Answer`"
        self.raw = raw
        self.__typename = raw["__typename"]
        self.value_key = answer_value_key(self.raw["__typename"])
        self._create_value()

    def _create_value(self):
        value = self.raw.get(self.value_key)

        if self.__typename == "TableAnswer" and value:
            self.value = [Document(parse_document(raw)) for raw in value]
        else:
            self.value = value

    @property
    def uuid(self):
        return decode_id(self.raw["id"]) if "id" in self.raw else None
