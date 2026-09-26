from collections.abc import Sequence
from dataclasses import dataclass

from knowledgey.category import Category
from knowledgey.slug import match_key
from knowledgey.source import Source
from knowledgey.store import CategoryStore, SourceStore


class UnknownCategoryError(ValueError):
    """Raised when a source is filed under a category that was never declared."""


@dataclass(frozen=True)
class CategoryAddResult:
    category: Category
    created: bool

    def as_dict(self) -> dict[str, str]:
        return {"status": "added" if self.created else "exists", **self.category.as_dict()}


@dataclass(frozen=True)
class SourceAddResult:
    source: Source
    created: bool

    def as_dict(self) -> dict[str, str]:
        return {"status": "added" if self.created else "exists", **self.source.as_dict()}


def _find(categories: Sequence[Category], key: str) -> Category | None:
    return next((item for item in categories if item.key == key), None)


def add_category(store: CategoryStore, *, label: str) -> CategoryAddResult:
    """Declare a category. A spelling variant of an existing one resolves to it."""
    candidate = Category.model_validate({"label": label})
    existing = _find(store.list_all(), candidate.key)
    if existing is not None:
        return CategoryAddResult(category=existing, created=False)

    return CategoryAddResult(category=candidate, created=store.save(candidate))


def resolve_categories(store: CategoryStore, labels: Sequence[str]) -> tuple[str, ...]:
    """Map user-supplied labels onto canonical slugs, rejecting anything undeclared."""
    known = store.list_all()
    resolved: list[str] = []

    for label in labels:
        found = _find(known, match_key(label))
        if found is None:
            available = ", ".join(sorted(item.slug for item in known)) or "none declared yet"
            raise UnknownCategoryError(
                f"unknown category {label!r}. Declared: {available}. "
                f"Add it first with: kg category add {label!r}"
            )

        if found.slug not in resolved:
            resolved.append(found.slug)

    return tuple(resolved)


def add_source(
    categories: CategoryStore,
    sources: SourceStore,
    *,
    name: str,
    feed_url: str,
    category_labels: Sequence[str] = (),
) -> SourceAddResult:
    """Register a feed, filing it under categories that must already exist."""
    resolved = resolve_categories(categories, category_labels)
    candidate = Source.model_validate({"name": name, "feed_url": feed_url, "categories": resolved})
    existing = sources.get(candidate.slug)
    if existing is not None:
        return SourceAddResult(source=existing, created=False)

    return SourceAddResult(source=candidate, created=sources.save(candidate))


def select_sources(
    sources: SourceStore,
    *,
    category: str | None = None,
    enabled_only: bool = True,
) -> list[Source]:
    """Pick registered sources, optionally narrowed to one category."""
    wanted = match_key(category) if category is not None else None
    return [
        source
        for source in sources.list_all()
        if (not enabled_only or source.enabled)
        and (wanted is None or any(match_key(slug) == wanted for slug in source.categories))
    ]
