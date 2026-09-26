from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from knowledgey.document import Document, Origin
from knowledgey.feed import FeedParseError, parse_feed
from knowledgey.fetcher import ContentFetcher, FetchError
from knowledgey.markup import html_to_markdown
from knowledgey.source import Source
from knowledgey.store import DocumentStore, SourceStore


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
            "duplicates": str(self.duplicates),
        }


def ingest_feed(
    fetcher: ContentFetcher,
    store: DocumentStore,
    *,
    url: str,
    source: str | None = None,
    categories: Sequence[str] = (),
) -> FeedIngestResult:
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
            source=source,
            categories=tuple(categories),
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
    categories: Sequence[str] = (),
) -> AddResult:
    """Create a document from pasted text and store it."""
    document = Document(
        title=title,
        content=content,
        origin=Origin.PASTE,
        url=url,
        authors=authors or [],
        categories=tuple(categories),
    )

    return AddResult(document=document, created=store.save(document))


@dataclass(frozen=True)
class SourceFetchResult:
    source: Source
    ingested: FeedIngestResult | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def as_dict(self) -> dict[str, str]:
        counts = self.ingested
        return {
            "source": self.source.slug,
            "status": "ok" if self.ok else "failed",
            "entries": str(counts.entries) if counts else "-",
            "added": str(counts.added) if counts else "-",
            "duplicates": str(counts.duplicates) if counts else "-",
            "error": self.error or "-",
        }


def ingest_source(
    fetcher: ContentFetcher,
    documents: DocumentStore,
    sources: SourceStore,
    source: Source,
) -> SourceFetchResult:
    """Fetch one registered source; stamp it as fetched only when the feed came through."""
    try:
        ingested = ingest_feed(
            fetcher,
            documents,
            url=source.feed_url,
            source=source.slug,
            categories=source.categories,
        )
    except (FetchError, FeedParseError) as exc:
        return SourceFetchResult(source=source, error=str(exc))

    stamped = source.model_copy(update={"last_fetched_at": datetime.now(UTC)})
    sources.replace(stamped)
    return SourceFetchResult(source=stamped, ingested=ingested)


def ingest_sources(
    fetcher: ContentFetcher,
    documents: DocumentStore,
    sources: SourceStore,
    selected: Sequence[Source],
) -> list[SourceFetchResult]:
    """Fetch sources in turn; a failing feed fills its own row and does not stop the rest"""
    return [ingest_source(fetcher, documents, sources, source) for source in selected]
