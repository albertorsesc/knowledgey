import json
import os
from pathlib import Path
from typing import Protocol

from knowledgey.document import Document


class DocumentStore(Protocol):
    """What the application needs from storage, regardless of where it lives."""

    def save(self, document: Document) -> bool:
        """Store a document. Returns False if one with the same id already exists."""
        ...

    def get(self, doc_id: str) -> Document | None: ...

    def list_all(self) -> list[Document]: ...


class JsonFileDocumentStore:
    """Stores documents as a single JSON file. Intended to be replaced by a database."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _read(self) -> dict[str, Document]:
        if not self._path.exists():
            return {}

        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return {key: Document.model_validate(value) for key, value in raw.items()}

    def _write(self, documents: dict[str, Document]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: value.model_dump(mode="json") for key, value in documents.items()}
        temporary = self._path.with_name(self._path.name + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(temporary, self._path)

    def save(self, document: Document) -> bool:
        documents = self._read()
        if document.doc_id in documents:
            return False

        documents[document.doc_id] = document
        self._write(documents)
        return True

    def get(self, doc_id: str) -> Document | None:
        return self._read().get(doc_id)

    def list_all(self) -> list[Document]:
        return sorted(self._read().values(), key=lambda d: d.added_at, reverse=True)
