from dataclasses import dataclass

from knowledgey.document import Document, Origin
from knowledgey.feed import parse_feed
from knowledgey.fetcher import ContentFetcher
from knowledgey.markup import html_to_markdown
from knowledgey.store import DocumentStore


@dataclass(frozen=True)
class AddResult:
    document: Document
    created: bool

    def as_dict(self) -> dict[str, str]:
        return {"status": "added" if self.created else "duplicate", **self.document.as_dict()}


@dataclass(frozen=True)
class FeedIngestResult:
    feed_title: str
    entries: int
    added: int
    duplicates: int

    def as_dict(self) -> dict[str, str]:
        return {
            "feed": self.feed_title or "-",
            "entries": str(self.entries),
            "added": str(self.added),
            "duplicated": str(self.duplicates),
        }


def ingest_feed(fetcher: ContentFetcher, store: DocumentStore, *, url: str) -> FeedIngestResult:
    """Fetch a feed, convert each entry to a document, and store the new ones."""
    parsed = parse_feed(fetcher.fetch(url))
    added = 0
    duplicates = 0

    for entry in parsed.entries:
        content = html_to_markdown(entry.content_html)
        if not content:
            continue
        document = Document(
            title=entry.title,
            content=content,
            origin=Origin.RSS,
            url=entry.url,
            authors=entry.authors,
            published_at=entry.published_at,
        )

        if store.save(document):
            added += 1
        else:
            duplicates += 1

    return FeedIngestResult(
        feed_title=parsed.title,
        entries=len(parsed.entries),
        added=added,
        duplicates=duplicates,
    )


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
