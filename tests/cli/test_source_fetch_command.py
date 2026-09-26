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


def _register(name: str, *categories: str) -> None:
    for label in categories:
        runner.invoke(app, ["category", "add", label])
    args = ["source", "add", "-n", name, "-u", f"https://{name.lower()}.com/feed"]
    for label in categories:
        args += ["-c", label]
    runner.invoke(app, args)


def test_fetch_ingests_every_enabled_source(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(FakeFetcher(FEED), monkeypatch)
    _register("A")
    _register("B")

    result = runner.invoke(app, ["source", "fetch", "--json"])

    assert result.exit_code == 0
    rows = json.loads(result.output)
    assert [(row["source"], row["status"]) for row in rows] == [("a", "ok"), ("b", "ok")]


def test_fetch_can_be_narrowed_to_a_category(monkeypatch: pytest.MonkeyPatch) -> None:
    fetcher = FakeFetcher(FEED)
    _use(fetcher, monkeypatch)
    _register("A", "MLOps")
    _register("B", "RAG")

    result = runner.invoke(app, ["source", "fetch", "-c", "mlops", "--json"])

    assert [row["source"] for row in json.loads(result.output)] == ["a"]
    assert fetcher.calls == ["https://a.com/feed"]


def test_fetch_shows_up_as_last_fetched_in_source_list(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(FakeFetcher(FEED), monkeypatch)
    _register("A")

    runner.invoke(app, ["source", "fetch"])
    rows = json.loads(runner.invoke(app, ["source", "list", "--json"]).output)

    assert rows[0]["last_fetched"] != "never"


def test_a_failing_source_is_reported_with_a_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    class Broken:
        def fetch(self, url: str) -> str:
            raise FetchError(f"could not fetch {url}: timed out")

    _use(Broken(), monkeypatch)
    _register("A")

    result = runner.invoke(app, ["source", "fetch"])

    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "failed" in result.output


def test_fetch_with_nothing_registered_says_so() -> None:
    result = runner.invoke(app, ["source", "fetch"])

    assert result.exit_code == 1
    assert "no enabled sources" in result.output
