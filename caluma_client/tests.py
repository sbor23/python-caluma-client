import json
from pathlib import Path
import pytest

from .models import Document, Question
from .parser import parse_document


@pytest.mark.parametrize(
    "response",
    [
        (
            {
                "slug": "textq1",
                "label": "textq1",
                "isRequired": "false",
                "isHidden": "false",
                "meta": {},
                "infoText": "",
                "__typename": "TextQuestion",
                "textMaxLength": None,
                "placeholder": "",
            },
            {
                "slug": "textarea",
                "label": "textarea",
                "isRequired": "false",
                "isHidden": "false",
                "meta": {},
                "infoText": "",
                "__typename": "TextareaQuestion",
                "textareaMaxLength": None,
                "placeholder": "",
            },
        )
    ],
)
def test_parse_question(response):
    question = Question(response)


def test_parse_full_document():
    response_file = Path(__file__).parent / "files/full_form_response.json"
    data = json.load(response_file.open())
    # data = data["data"]["allDocuments"]["edges"][0]["node"]

    raw = parse_document(data, nesting="data.allDocuments.edges.0.node")
    root_doc = Document(raw)
