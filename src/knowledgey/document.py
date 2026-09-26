import hashlib
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from knowledgey.slug import normalize_slugs


class Origin(StrEnum):
    """How a document entered the system."""

    PASTE = "paste"
    RSS = "rss"


class Document(BaseModel):
    """A single piece of the text content, normalized to Markdown."""

    model_config = ConfigDict(frozen=True)

    title: str
    content: str
    origin: Origin
    url: str | None = None
    authors: list[str] = Field(default_factory=list)
    source: str | None = None
    categories: tuple[str, ...] = ()
    published_at: datetime | None = None
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("title", "content")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank.")

        return value

    @field_validator("categories")
    @classmethod
    def _normalize_categories(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return normalize_slugs(value)

    @property
    def doc_id(self) -> str:
        """Stable identity: the URL when there is one, otherwise the content itself."""
        basis = self.url if self.url else self.content

        return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.doc_id,
            "title": self.title,
            "origin": self.origin.value,
            "source": self.source or "-",
            "categories": ", ".join(self.categories) or "-",
            "url": self.url or "-",
            "authors": ", ".join(self.authors) or "-",
            "words": str(len(self.content.split())),
        }

    def as_detail(self) -> dict[str, str]:
        return {
            **self.as_dict(),
            "published": self.published_at.isoformat() if self.published_at else "-",
            "added": self.added_at.isoformat(),
            "content": self.content,
        }
