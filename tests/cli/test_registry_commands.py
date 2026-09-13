import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from knowledgey.cli.app import app
from knowledgey.config import get_settings

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KG_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()


def test_category_add_reports_the_canonical_slug() -> None:
    result = runner.invoke(app, ["category", "add", "MLOps", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.output)["slug"] == "mlops"


def test_category_add_is_idempotent_across_spellings() -> None:
    runner.invoke(app, ["category", "add", "MLOps"])
    result = runner.invoke(app, ["category", "add", "ml ops", "--json"])
    listed = runner.invoke(app, ["category", "list", "--json"])

    assert json.loads(result.output)["status"] == "exists"
    assert len(json.loads(listed.output)) == 1


def test_source_add_files_under_a_declared_category() -> None:
    runner.invoke(app, ["category", "add", "MLOps"])
    result = runner.invoke(
        app,
        [
            "source",
            "add",
            "-n",
            "The Neural Maze",
            "-u",
            "https://x.com/feed",
            "-c",
            "ML Ops",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.output)["categories"] == "mlops"


def test_source_add_rejects_an_undeclared_category() -> None:
    result = runner.invoke(
        app, ["source", "add", "-n", "X", "-u", "https://x.com/feed", "-c", "rag"]
    )

    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "unknown category" in result.output


def test_source_add_rejects_a_non_http_url() -> None:
    result = runner.invoke(app, ["source", "add", "-n", "X", "-u", "x.com/feed"])

    assert result.exit_code == 1
    assert "http" in result.output


def test_source_list_filters_by_category() -> None:
    runner.invoke(app, ["category", "add", "MLOps"])
    runner.invoke(app, ["category", "add", "RAG"])
    runner.invoke(app, ["source", "add", "-n", "A", "-u", "https://a.com/feed", "-c", "MLOps"])
    runner.invoke(app, ["source", "add", "-n", "B", "-u", "https://b.com/feed", "-c", "RAG"])
    listed = runner.invoke(app, ["source", "list", "-c", "mlops", "--json"])

    assert [row["name"] for row in json.loads(listed.output)] == ["A"]
