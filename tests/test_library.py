import os
from pathlib import Path

import pytest

from knowledgey.document import Document, Origin
from knowledgey.library import AmbiguousReferenceError, find_document, select_documents
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


def test_find_by_full_id(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    document = filed("A")
    store.save(document)

    assert find_document(store, document.doc_id) == document


def test_find_by_unique_prefix(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    document = filed("A")
    store.save(document)

    assert find_document(store, document.doc_id[:6]) == document


def test_find_unknown_reference_is_none(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    store.save(filed("A"))

    assert find_document(store, "zzzz") is None


def test_ambiguous_prefix_is_an_error(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    a, b = filed("A"), filed("B")
    store.save(a)
    store.save(b)
    shared = os.path.commonprefix([a.doc_id, b.doc_id])

    with pytest.raises(AmbiguousReferenceError, match="2 documents"):
        find_document(store, shared)
