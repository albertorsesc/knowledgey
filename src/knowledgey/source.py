from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from knowledgey.document import Origin
from knowledgey.slug import normalize_slugs, slugify


class Source(BaseModel):
    """A place documents are fetched from, repeatedly."""

    model_config = ConfigDict(frozen=True)

    slug: str = ""
    name: str
    feed_url: str
    origin: Origin = Origin.RSS
    categories: tuple[str, ...] = ()
    enabled: bool = True
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_fetched_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _derive_slug(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("slug"):
            return {**data, "slug": slugify(str(data.get("name", "")))}
        return data

    @field_validator("name")
    @classmethod
    def _reject_blank_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("feed_url")
    @classmethod
    def _require_http_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("must start with http:// or https://")
        return value

    @field_validator("slug")
    @classmethod
    def _reject_empty_slug(cls, value: str) -> str:
        if not value:
            raise ValueError("could not be derived from the name; pass one explicitly")
        return value

    @field_validator("categories")
    @classmethod
    def _normalize_categories(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return normalize_slugs(value)

    def as_dict(self) -> dict[str, str]:
        return {
            "slug": self.slug,
            "name": self.name,
            "origin": self.origin.value,
            "categories": ", ".join(self.categories) or "-",
            "enabled": "yes" if self.enabled else "no",
            "last_fetched": (
                self.last_fetched_at.date().isoformat() if self.last_fetched_at else "never"
            ),
        }
