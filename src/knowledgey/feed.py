from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import feedparser


class FeedParseError(ValueError):
    """Raised when the input is not a usable feed."""


@dataclass(frozen=True)
class FeedEntry:
    title: str
    url: str
    content_html: str
    authors: list[str]
    published_at: datetime | None


@dataclass(frozen=True)
class ParsedFeed:
    title: str
    entries: list[FeedEntry]


def _published(entry: Any) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    year, month, day, hour, minute, second = parsed[:6]
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


def _authors(entry: Any) -> list[str]:
    names = [a.get("name", "").strip() for a in entry.get("authors", [])]
    named = [name for name in names if name]
    if named:
        return named
    single = str(entry.get("author", "")).strip()
    return [single] if single else []


def _content_html(entry: Any) -> str:
    blocks = entry.get("content") or []
    if blocks and blocks[0].get("value"):
        return str(blocks[0]["value"])
    return str(entry.get("summary", ""))


def parse_feed(raw: str | bytes) -> ParsedFeed:
    """Parse RSS or Atom bytes into entries, skipping items with no link or no body."""
    parsed = feedparser.parse(raw)
    if not parsed.version:
        raise FeedParseError("input is not a readable RSS or Atom feed.")

    entries: list[FeedEntry] = []
    for entry in parsed.entries:
        url = str(entry.get("link", "")).strip()
        content_html = _content_html(entry).strip()
        if not url or not content_html:
            continue

        entries.append(
            FeedEntry(
                title=str(entry.get("title", "")).strip() or "Untitled",
                url=url,
                content_html=content_html,
                authors=_authors(entry),
                published_at=_published(entry),
            )
        )

    return ParsedFeed(title=str(parsed.feed.get("title", "")).strip(), entries=entries)
