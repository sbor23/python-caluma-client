import json
from pathlib import Path

from caluma_client.models import Document
from caluma_client.parser import parse_document


def test_parse_full_document():
    response_file = Path(__file__).parent / "files/full_form_response.json"
    data = json.load(response_file.open())

    raw = parse_document(data, nesting="data.allDocuments.edges.0.node")
    Document(raw)
