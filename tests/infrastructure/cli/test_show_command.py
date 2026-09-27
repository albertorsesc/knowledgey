import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from knowledgey.infrastructure.cli.app import app
from knowledgey.infrastructure.config import get_settings

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KG_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()


def _add(title: str, text: str) -> str:
    result = runner.invoke(app, ["add", "--title", title, "--json"], input=text)
    return str(json.loads(result.output)["id"])


def test_show_prints_metadata_and_body() -> None:
    doc_id = _add("Findable", "# Heading\n\nbody text")

    result = runner.invoke(app, ["show", doc_id])

    assert result.exit_code == 0
    assert "Findable" in result.output
    assert "body text" in result.output


def test_show_accepts_a_unique_prefix() -> None:
    doc_id = _add("Findable", "body text")

    result = runner.invoke(app, ["show", doc_id[:6], "--json"])

    assert json.loads(result.output)["id"] == doc_id


def test_show_raw_prints_only_the_markdown() -> None:
    doc_id = _add("Findable", "# Heading\n\nbody text")

    result = runner.invoke(app, ["show", doc_id, "--raw"])

    assert result.output == "# Heading\n\nbody text\n"


def test_show_unknown_reference_fails_cleanly() -> None:
    result = runner.invoke(app, ["show", "zzzz"])

    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "no document matches" in result.output


def test_show_ambiguous_prefix_fails_cleanly() -> None:
    a = _add("A", "alpha")
    b = _add("B", "beta")

    result = runner.invoke(app, ["show", os.path.commonprefix([a, b])])

    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "2 documents" in result.output
