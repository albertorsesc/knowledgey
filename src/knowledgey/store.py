import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel

from knowledgey.category import Category
from knowledgey.document import Document
from knowledgey.source import Source


class Repository[T](Protocol):
    """What the application needs from storage, regardless of where it lives."""

    def save(self, item: T) -> bool:
        """Store an item. Returns False if one with the same key already exists."""
        ...

    def replace(self, item: T) -> None:
        """Store an item, overwriting any existing one with the same key."""
        ...

    def remove(self, key: str) -> bool:
        """Delete by key. Returns False if there was nothing to delete."""
        ...

    def get(self, key: str) -> T | None: ...

    def list_all(self) -> list[T]: ...


class JsonFileStore[T: BaseModel]:
    """Stores one kind of model as a single JSON file. Intended to be replaced by a database."""

    def __init__(
        self,
        path: Path,
        model: type[T],
        key_of: Callable[[T], str],
        sort_key: Callable[[T], Any] | None = None,
        reverse: bool = False,
    ) -> None:
        self._path = path
        self._model = model
        self._key_of = key_of
        self._sort_key = sort_key
        self._reverse = reverse

    def _read(self) -> dict[str, T]:
        if not self._path.exists():
            return {}

        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return {key: self._model.model_validate(value) for key, value in raw.items()}

    def _write(self, items: dict[str, T]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: value.model_dump(mode="json") for key, value in items.items()}
        temporary = self._path.with_name(self._path.name + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(temporary, self._path)

    def save(self, item: T) -> bool:
        items = self._read()
        key = self._key_of(item)
        if key in items:
            return False

        items[key] = item
        self._write(items)
        return True

    def replace(self, item: T) -> None:
        items = self._read()
        items[self._key_of(item)] = item
        self._write(items)

    def remove(self, key: str) -> bool:
        items = self._read()
        if key not in items:
            return False

        del items[key]
        self._write(items)
        return True

    def get(self, key: str) -> T | None:
        return self._read().get(key)

    def list_all(self) -> list[T]:
        items = list(self._read().values())
        if self._sort_key is None:
            return items
        return sorted(items, key=self._sort_key, reverse=self._reverse)


class JsonFileDocumentStore(JsonFileStore[Document]):
    def __init__(self, path: Path) -> None:
        super().__init__(
            path,
            model=Document,
            key_of=lambda document: document.doc_id,
            sort_key=lambda document: document.added_at,
            reverse=True,
        )


class JsonFileSourceStore(JsonFileStore[Source]):
    def __init__(self, path: Path) -> None:
        super().__init__(
            path,
            model=Source,
            key_of=lambda source: source.slug,
            sort_key=lambda source: source.slug,
        )


class JsonFileCategoryStore(JsonFileStore[Category]):
    def __init__(self, path: Path) -> None:
        super().__init__(
            path,
            model=Category,
            key_of=lambda category: category.slug,
            sort_key=lambda category: category.slug,
        )


DocumentStore = Repository[Document]
SourceStore = Repository[Source]
CategoryStore = Repository[Category]
