from pathlib import Path

from knowledgey.application.ingest import ingest_feed
from knowledgey.infrastructure.persistence.json_store import JsonFileDocumentStore

FEED = """<?xml version="1.0"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel><title>Test Feed</title>
    <item><title>One</title><link>https://ex.com/1</link>
      <content:encoded>
        <![CDATA[<p>First <b>body</b></p><script>alert(1)</script>]]>
      </content:encoded>
    </item>
    <item><title>Two</title><link>https://ex.com/2</link>
      <content:encoded><![CDATA[<p>Second body</p>]]></content:encoded>
    </item>
  </channel>
</rss>"""


class FakeFetcher:
    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.calls: list[str] = []

    def fetch(self, url: str) -> str:
        self.calls.append(url)
        return self.payload


def test_entries_become_documents(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    result = ingest_feed(FakeFetcher(FEED), store, url="https://ex.com/feed")
    assert (result.feed_title, result.entries, result.added, result.duplicates) == (
        "Test Feed",
        2,
        2,
        0,
    )
    assert len(store.list_all()) == 2


def test_second_run_finds_only_duplicates(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    ingest_feed(FakeFetcher(FEED), store, url="https://ex.com/feed")
    result = ingest_feed(FakeFetcher(FEED), store, url="https://ex.com/feed")
    assert (result.added, result.duplicates) == (0, 2)
    assert len(store.list_all()) == 2


def test_documents_are_marked_as_rss(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    ingest_feed(FakeFetcher(FEED), store, url="https://ex.com/feed")
    assert {d.origin.value for d in store.list_all()} == {"rss"}


def test_script_content_is_not_stored(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    ingest_feed(FakeFetcher(FEED), store, url="https://ex.com/feed")
    assert all("alert(1)" not in d.content for d in store.list_all())


def test_the_requested_url_is_the_one_fetched(tmp_path: Path) -> None:
    fetcher = FakeFetcher(FEED)
    ingest_feed(fetcher, JsonFileDocumentStore(tmp_path / "d.json"), url="https://ex.com/feed")
    assert fetcher.calls == ["https://ex.com/feed"]


def test_documents_carry_their_source_and_categories(tmp_path: Path) -> None:
    store = JsonFileDocumentStore(tmp_path / "d.json")
    ingest_feed(
        FakeFetcher(FEED), store, url="https://ex.com/feed", source="tnm", categories=("mlops",)
    )
    assert {(d.source, d.categories) for d in store.list_all()} == {("tnm", ("mlops",))}
