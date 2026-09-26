import pytest
from pydantic import ValidationError

from knowledgey.document import Document, Origin


def make(
    title: str = "T",
    content: str = "hello world",
    url: str | None = None,
) -> Document:
    return Document(title=title, content=content, origin=Origin.PASTE, url=url)


def test_identity_is_stable_for_same_content() -> None:
    assert make().doc_id == make().doc_id


def test_identity_differs_for_different_content() -> None:
    assert make().doc_id != make(content="something else").doc_id


def test_url_wins_over_content_for_identity() -> None:
    a = make(url="https://example.com/a")
    b = make(url="https://example.com/a", content="totally different text")
    assert a.doc_id == b.doc_id


def test_blank_title_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make(title="   ")


def test_document_is_immutable() -> None:
    document = make()
    with pytest.raises(ValidationError):
        document.title = "new"


def test_as_dict_summarises_without_full_content() -> None:
    data = make(content="one two three").as_dict()
    assert data["words"] == "3"
    assert "content" not in data


def test_documents_carry_no_source_by_default() -> None:
    document = make()
    assert document.source is None
    assert document.categories == ()


def test_categories_are_normalised() -> None:
    document = Document(
        title="T", content="c", origin=Origin.PASTE, categories=("ML Ops", "mlops", "RAG")
    )
    assert document.categories == ("ml-ops", "mlops", "rag")


def test_as_dict_shows_source_and_categories() -> None:
    document = Document(
        title="T", content="c", origin=Origin.RSS, source="tnm", categories=("mlops",)
    )
    data = document.as_dict()
    assert (data["source"], data["categories"]) == ("tnm", "mlops")


def test_as_detail_includes_content_and_timestamps() -> None:
    data = make(content="one two three").as_detail()
    assert data["content"] == "one two three"
    assert data["published"] == "-"
    assert data["added"]
