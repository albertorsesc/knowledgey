from datetime import UTC, datetime
from pathlib import Path

from knowledgey.fetcher import FetchError
from knowledgey.ingest import ingest_source, ingest_sources
from knowledgey.source import Source
from knowledgey.store import JsonFileDocumentStore, JsonFileSourceStore
from tests.test_feed_ingest import FEED, FakeFetcher


def stores(tmp_path: Path) -> tuple[JsonFileDocumentStore, JsonFileSourceStore]:
    return (
        JsonFileDocumentStore(tmp_path / "documents.json"),
        JsonFileSourceStore(tmp_path / "sources.json"),
    )


def registered(sources: JsonFileSourceStore, name: str = "A") -> Source:
    source = Source.model_validate({"name": name, "feed_url": f"https://{name.lower()}.com/feed"})
    sources.save(source)
    return source


class Broken:
    def fetch(self, url: str) -> str:
        raise FetchError(f"could not fetch {url}: timed out")


class BrokenForA:
    def fetch(self, url: str) -> str:
        if url.startswith("https://a.com"):
            raise FetchError(f"could not fetch {url}: timed out")
        return FEED


def test_a_source_is_fetched_from_its_feed_url(tmp_path: Path) -> None:
    documents, sources = stores(tmp_path)
    source = registered(sources)
    fetcher = FakeFetcher(FEED)

    result = ingest_source(fetcher, documents, sources, source)

    assert result.ok
    assert result.ingested is not None
    assert result.ingested.added == 2
    assert fetcher.calls == [source.feed_url]
    assert len(documents.list_all()) == 2


def test_a_successful_fetch_stamps_the_source(tmp_path: Path) -> None:
    documents, sources = stores(tmp_path)
    source = registered(sources)
    before = datetime.now(UTC)

    result = ingest_source(FakeFetcher(FEED), documents, sources, source)

    stored = sources.get(source.slug)
    assert stored is not None
    assert stored.last_fetched_at is not None
    assert stored.last_fetched_at >= before
    assert result.source.last_fetched_at == stored.last_fetched_at


def test_a_failed_fetch_is_reported_and_not_stamped(tmp_path: Path) -> None:
    documents, sources = stores(tmp_path)
    source = registered(sources)

    result = ingest_source(Broken(), documents, sources, source)

    stored = sources.get(source.slug)
    assert stored is not None
    assert not result.ok
    assert result.error is not None
    assert "could not fetch" in result.error
    assert stored.last_fetched_at is None
    assert documents.list_all() == []


def test_a_non_feed_body_is_a_failure(tmp_path: Path) -> None:
    documents, sources = stores(tmp_path)
    source = registered(sources)
    fetcher = FakeFetcher("<html><body>nope</body></html>")

    result = ingest_source(fetcher, documents, sources, source)

    assert not result.ok
    assert result.error is not None
    assert "not a readable RSS or Atom feed" in result.error


def test_one_failing_source_does_not_stop_the_others(tmp_path: Path) -> None:
    documents, sources = stores(tmp_path)
    selected = [registered(sources, "A"), registered(sources, "B")]

    results = ingest_sources(BrokenForA(), documents, sources, selected)

    assert [result.ok for result in results] == [False, True]
    assert len(documents.list_all()) == 2


def test_success_and_failure_rows_share_columns(tmp_path: Path) -> None:
    documents, sources = stores(tmp_path)
    source = registered(sources)

    ok = ingest_source(FakeFetcher(FEED), documents, sources, source).as_dict()
    failed = ingest_source(Broken(), documents, sources, source).as_dict()

    assert list(ok) == list(failed)
