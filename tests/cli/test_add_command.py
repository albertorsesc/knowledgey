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


def test_add_from_stdin() -> None:
    result = runner.invoke(app, ["add", "--title", "Note"], input="some pasted text")
    assert result.exit_code == 0
    assert "added" in result.output


def test_add_from_file(tmp_path: Path) -> None:
    source = tmp_path / "note.md"
    source.write_text("file content here", encoding="utf-8")
    result = runner.invoke(app, ["add", "--title", "Note", "--file", str(source), "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["status"] == "added"


def test_second_identical_add_is_a_duplicate() -> None:
    runner.invoke(app, ["add", "--title", "Note"], input="same text")
    result = runner.invoke(app, ["add", "--title", "Note", "--json"], input="same text")
    assert json.loads(result.output)["status"] == "duplicate"


def test_repeatable_author_option() -> None:
    result = runner.invoke(
        app,
        ["add", "--title", "N", "--author", "Ada", "--author", "Grace", "--json"],
        input="text",
    )
    assert json.loads(result.output)["authors"] == "Ada, Grace"


def test_blank_content_shows_a_clean_message() -> None:
    result = runner.invoke(app, ["add", "--title", "Note"], input="   ")
    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "must not be blank" in result.output
