from pathlib import Path

from knowledgey.document import Document, Origin
from knowledgey.library import select_documents
from knowledgey.store import JsonFileDocumentStore


def filed(title: str, *categories: str) -> Document:
    return Document(title=title, content=title, origin=Origin.PASTE, categories=categories)


def test_all_documents_by_default(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    store.save(filed("A", "mlops"))
    store.save(filed("B"))

    assert {d.title for d in select_documents(store)} == {"A", "B"}


def test_narrowed_to_a_category_across_spellings(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    store.save(filed("A", "mlops"))
    store.save(filed("B", "rag"))

    assert [d.title for d in select_documents(store, category="ML Ops")] == ["A"]


def test_unknown_category_is_empty(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    store.save(filed("A", "mlops"))

    assert select_documents(store, category="nope") == []
