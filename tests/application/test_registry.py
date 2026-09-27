from pathlib import Path

import pytest

from knowledgey.application.registry import (
    UnknownCategoryError,
    add_category,
    add_source,
    resolve_categories,
    select_sources,
)
from knowledgey.infrastructure.persistence.json_store import (
    JsonFileCategoryStore,
    JsonFileSourceStore,
)


def stores(tmp_path: Path) -> tuple[JsonFileCategoryStore, JsonFileSourceStore]:
    return (
        JsonFileCategoryStore(tmp_path / "categories.json"),
        JsonFileSourceStore(tmp_path / "sources.json"),
    )


def test_declaring_a_category_creates_it(tmp_path: Path) -> None:
    categories, _ = stores(tmp_path)
    result = add_category(categories, label="MLOps")

    assert result.created is True
    assert result.category.slug == "mlops"


def test_a_spelling_variant_resolves_to_the_existing_one(tmp_path: Path) -> None:
    categories, _ = stores(tmp_path)
    add_category(categories, label="MLOps")
    result = add_category(categories, label="ML Ops")

    assert result.created is False
    assert result.category.slug == "mlops"
    assert len(categories.list_all()) == 1


def test_variants_resolve_to_the_canonical_slug(tmp_path: Path) -> None:
    categories, _ = stores(tmp_path)
    add_category(categories, label="MLOps")

    assert resolve_categories(categories, ["ml-ops", "ML Ops"]) == ("mlops",)


def test_an_undeclared_category_is_rejected(tmp_path: Path) -> None:
    categories, _ = stores(tmp_path)
    add_category(categories, label="MLOps")

    with pytest.raises(UnknownCategoryError, match="mlops"):
        resolve_categories(categories, ["rag"])


def test_a_source_needs_no_categories(tmp_path: Path) -> None:
    categories, sources = stores(tmp_path)
    result = add_source(
        categories, sources, name="The Neural Maze", feed_url="https://example.com/feed"
    )

    assert result.created is True
    assert result.source.categories == ()


def test_a_source_stores_canonical_category_slugs(tmp_path: Path) -> None:
    categories, sources = stores(tmp_path)
    add_category(categories, label="MLOps")
    result = add_source(
        categories,
        sources,
        name="The Neural Maze",
        feed_url="https://example.com/feed",
        category_labels=["ML Ops"],
    )

    assert result.source.categories == ("mlops",)


def test_a_source_with_an_undeclared_category_is_rejected(tmp_path: Path) -> None:
    categories, sources = stores(tmp_path)

    with pytest.raises(UnknownCategoryError):
        add_source(
            categories,
            sources,
            name="X",
            feed_url="https://example.com/feed",
            category_labels=["nope"],
        )

    assert sources.list_all() == []


def test_registering_the_same_source_twice_is_not_a_duplicate(tmp_path: Path) -> None:
    categories, sources = stores(tmp_path)
    add_source(categories, sources, name="X", feed_url="https://example.com/feed")
    result = add_source(categories, sources, name="X", feed_url="https://other.com/feed")

    assert result.created is False
    assert len(sources.list_all()) == 1


def test_select_returns_only_enabled_sources_by_default(tmp_path: Path) -> None:
    categories, sources = stores(tmp_path)
    add_source(categories, sources, name="A", feed_url="https://a.com/feed")
    added = add_source(categories, sources, name="B", feed_url="https://b.com/feed")
    sources.replace(added.source.model_copy(update={"enabled": False}))

    assert [item.name for item in select_sources(sources)] == ["A"]


def test_select_can_include_disabled_sources(tmp_path: Path) -> None:
    categories, sources = stores(tmp_path)
    add_source(categories, sources, name="A", feed_url="https://a.com/feed")
    added = add_source(categories, sources, name="B", feed_url="https://b.com/feed")
    sources.replace(added.source.model_copy(update={"enabled": False}))

    assert [item.name for item in select_sources(sources, enabled_only=False)] == ["A", "B"]


def test_select_narrows_to_a_category_across_spellings(tmp_path: Path) -> None:
    categories, sources = stores(tmp_path)
    add_category(categories, label="MLOps")
    add_category(categories, label="RAG")
    add_source(
        categories, sources, name="A", feed_url="https://a.com/feed", category_labels=["MLOps"]
    )
    add_source(
        categories, sources, name="B", feed_url="https://b.com/feed", category_labels=["RAG"]
    )

    assert [item.name for item in select_sources(sources, category="ML Ops")] == ["A"]


def test_select_with_an_unknown_category_is_empty(tmp_path: Path) -> None:
    categories, sources = stores(tmp_path)
    add_source(categories, sources, name="A", feed_url="https://a.com/feed")

    assert select_sources(sources, category="nope") == []
