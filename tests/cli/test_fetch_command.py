import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from knowledgey.cli import app as app_module
from knowledgey.cli.app import app
from knowledgey.config import get_settings
from knowledgey.fetcher import ContentFetcher, FetchError
from tests.test_feed_ingest import FEED, FakeFetcher

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KG_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()


def _use(fetcher: ContentFetcher, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_module, "_content_fetcher", lambda: fetcher)


def test_fetch_stores_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(FakeFetcher(FEED), monkeypatch)
    result = runner.invoke(app, ["fetch", "https://ex.com/feed", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["added"] == "2"


def test_fetched_documents_show_up_in_list(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(FakeFetcher(FEED), monkeypatch)
    runner.invoke(app, ["fetch", "https://ex.com/feed"])
    rows = json.loads(runner.invoke(app, ["list", "--json"]).output)
    assert sorted(row["title"] for row in rows) == ["One", "Two"]


def test_network_failure_is_reported_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    class Broken:
        def fetch(self, url: str) -> str:
            raise FetchError("could not fetch https://ex.com/feed: timed out")

    _use(Broken(), monkeypatch)
    result = runner.invoke(app, ["fetch", "https://ex.com/feed"])
    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "could not fetch" in result.output


def test_non_feed_input_is_reported_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(FakeFetcher("<html><body>not a feed</body></html>"), monkeypatch)
    result = runner.invoke(app, ["fetch", "https://ex.com/page"])
    assert result.exit_code == 1
    assert "not a readable RSS or Atom feed" in result.output
