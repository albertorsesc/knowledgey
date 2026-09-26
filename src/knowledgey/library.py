from knowledgey.document import Document
from knowledgey.slug import has_match
from knowledgey.store import DocumentStore


def select_documents(store: DocumentStore, *, category: str | None = None) -> list[Document]:
    """Stored documents, newest first, optionally only those filed under one category."""
    return [
        document
        for document in store.list_all()
        if category is None or has_match(document.categories, category)
    ]


class AmbiguousReferenceError(LookupError):
    """Raised when a prefix matches more than one document."""


def find_document(store: DocumentStore, ref: str) -> Document | None:
    """Look a document up by its id, or by a prefix of it that matches exactly one."""
    exact = store.get(ref)
    if exact is not None:
        return exact

    matches = [document for document in store.list_all() if document.doc_id.startswith(ref)]
    if len(matches) > 1:
        raise AmbiguousReferenceError(
            f"{ref!r} matches {len(matches)} documents. Give more characters of the ID."
        )

    return matches[0] if matches else None
