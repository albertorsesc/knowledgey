from dataclasses import dataclass

from knowledgey.document import Document, Origin
from knowledgey.store import DocumentStore


@dataclass(frozen=True)
class AddResult:
    document: Document
    created: bool

    def as_dict(self) -> dict[str, str]:
        return {"status": "added" if self.created else "duplicate", **self.document.as_dict()}


def add_pasted_document(
    store: DocumentStore,
    *,
    title: str,
    content: str,
    url: str | None = None,
    authors: list[str] | None = None,
) -> AddResult:
    """Create a document from pasted text and store it."""
    document = Document(
        title=title, content=content, origin=Origin.PASTE, url=url, authors=authors or []
    )

    return AddResult(document=document, created=store.save(document))
