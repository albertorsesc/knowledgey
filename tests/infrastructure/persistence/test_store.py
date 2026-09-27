from pathlib import Path

from knowledgey.application.ports import DocumentStore
from knowledgey.domain.document import Document, Origin
from knowledgey.infrastructure.persistence.json_store import JsonFileDocumentStore


def make(content: str = "hello world", title: str = "T") -> Document:
    return Document(title=title, content=content, origin=Origin.PASTE)


def test_construction_touches_no_disk(tmp_path: Path) -> None:
    JsonFileDocumentStore(tmp_path / "sub" / "documents.json")
    assert not (tmp_path / "sub").exists()


def test_empty_store_lists_nothing(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "documents.json")
    assert store.list_all() == []


def test_saved_document_can_be_read_back(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "documents.json")
    document = make(content="hello world")
    assert store.save(document) is True
    assert store.get(document.doc_id) == document


def test_duplicate_save_is_rejected(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "documents.json")
    store.save(make())
    assert store.save(make()) is False
    assert len(store.list_all()) == 1


def test_data_survives_a_new_store_instance(tmp_path: Path) -> None:
    path = tmp_path / "documents.json"
    JsonFileDocumentStore(path).save(make())
    assert len(JsonFileDocumentStore(path).list_all()) == 1


def test_missing_document_returns_none(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "documents.json")
    assert store.get("nope") is None


def test_json_store_satisfies_the_protocol(tmp_path: Path) -> None:
    store: DocumentStore = JsonFileDocumentStore(tmp_path / "documents.json")
    assert store.list_all() == []
