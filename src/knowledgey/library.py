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
