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


def test_empty_store_says_so() -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Nothing stored yet" in result.output


def test_empty_store_as_json_is_an_empty_array() -> None:
    result = runner.invoke(app, ["list", "--json"])
    assert json.loads(result.output) == []


def test_added_documents_appear() -> None:
    runner.invoke(app, ["add", "--title", "First"], input="alpha text")
    runner.invoke(app, ["add", "--title", "Second"], input="beta text")
    result = runner.invoke(app, ["list", "--json"])
    titles = [row["title"] for row in json.loads(result.output)]
    assert sorted(titles) == ["First", "Second"]


def test_table_output_shows_titles() -> None:
    runner.invoke(app, ["add", "--title", "Findable"], input="alpha text")
    result = runner.invoke(app, ["list"])
    assert "Findable" in result.output


def test_blank_content_shows_a_clean_message() -> None:
    result = runner.invoke(app, ["add", "--title", "Note"], input="   ")
    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "must not be blank" in result.output


def test_list_filters_by_category() -> None:
    runner.invoke(app, ["category", "add", "MLOps"])
    runner.invoke(app, ["category", "add", "RAG"])
    runner.invoke(app, ["add", "--title", "A", "-c", "MLOps"], input="alpha text")
    runner.invoke(app, ["add", "--title", "B", "-c", "RAG"], input="beta text")
    result = runner.invoke(app, ["list", "-c", "mlops", "--json"])

    assert [row["title"] for row in json.loads(result.output)] == ["A"]
