from pathlib import Path

from knowledgey.category import Category
from knowledgey.source import Source
from knowledgey.store import (
    CategoryStore,
    JsonFileCategoryStore,
    JsonFileSourceStore,
    SourceStore,
)


def a_source(name: str = "The Neural Maze") -> Source:
    return Source.model_validate({"name": name, "feed_url": "https://example.com/feed"})


def test_source_round_trips(tmp_path: Path) -> None:
    store = JsonFileSourceStore(tmp_path / "sources.json")
    source = a_source()
    assert store.save(source) is True
    assert store.get("the-neural-maze") == source


def test_duplicate_slug_is_rejected(tmp_path: Path) -> None:
    store = JsonFileSourceStore(tmp_path / "sources.json")
    store.save(a_source())
    assert store.save(a_source()) is False


def test_replace_overwrites_in_place(tmp_path: Path) -> None:
    store = JsonFileSourceStore(tmp_path / "sources.json")
    store.save(a_source())
    store.replace(a_source().model_copy(update={"enabled": False}))

    stored = store.get("the-neural-maze")
    assert stored is not None
    assert stored.enabled is False
    assert len(store.list_all()) == 1


def test_remove_reports_whether_it_was_there(tmp_path: Path) -> None:
    store = JsonFileSourceStore(tmp_path / "sources.json")
    store.save(a_source())
    assert store.remove("the-neural-maze") is True
    assert store.remove("the-neural-maze") is False
    assert store.list_all() == []


def test_categories_use_the_same_machinery(tmp_path: Path) -> None:
    store: CategoryStore = JsonFileCategoryStore(tmp_path / "categories.json")
    assert store.save(Category.model_validate({"label": "MLOps"})) is True
    assert store.get("mlops") is not None


def test_separate_stores_do_not_share_a_file(tmp_path: Path) -> None:
    sources: SourceStore = JsonFileSourceStore(tmp_path / "sources.json")
    categories: CategoryStore = JsonFileCategoryStore(tmp_path / "categories.json")
    sources.save(a_source())
    assert categories.list_all() == []
