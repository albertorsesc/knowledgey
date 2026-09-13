from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from knowledgey.slug import match_key, slugify


class Category(BaseModel):
    """A label sources are filed under. The set of these is deliberately closed."""

    model_config = ConfigDict(frozen=True)

    slug: str = ""
    label: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="before")
    @classmethod
    def _derive_slug(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("slug"):
            return {**data, "slug": slugify(str(data.get("label", "")))}
        return data

    @field_validator("label")
    @classmethod
    def _reject_blank_label(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("slug")
    @classmethod
    def _reject_empty_slug(cls, value: str) -> str:
        if not value:
            raise ValueError("could not be derived from the label; pass one explicitly")
        return value

    @property
    def key(self) -> str:
        """What two spellings of the same category have in common."""
        return match_key(self.slug)

    def as_dict(self) -> dict[str, str]:
        return {"slug": self.slug, "label": self.label}
