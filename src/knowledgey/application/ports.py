from typing import Protocol

from knowledgey.domain.category import Category
from knowledgey.domain.document import Document
from knowledgey.domain.source import Source


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


DocumentStore = Repository[Document]
SourceStore = Repository[Source]
CategoryStore = Repository[Category]


class FetchError(RuntimeError):
    """Raised when a URL cannot be retrieved."""


class ContentFetcher(Protocol):
    """What the application needs from the network."""

    def fetch(self, url: str) -> str: ...
