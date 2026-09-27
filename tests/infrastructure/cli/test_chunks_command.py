import json
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


def test_chunks_lists_one_row_per_chunk() -> None:
    body = "\n\n".join(f"Paragraph {i}. " + "word " * 300 for i in range(4))
    added = runner.invoke(app, ["add", "--title", "Long", "--json"], input=body)
    doc_id = json.loads(added.output)["id"]

    result = runner.invoke(app, ["chunks", doc_id, "--json"])

    rows = json.loads(result.output)
    assert result.exit_code == 0
    assert len(rows) > 1
    assert [row["index"] for row in rows] == [str(i) for i in range(len(rows))]
    assert all(int(row["chars"]) <= 4000 for row in rows)


def test_chunks_accepts_a_prefix_and_fails_cleanly_on_unknown() -> None:
    added = runner.invoke(app, ["add", "--title", "Short", "--json"], input="tiny note")
    doc_id = json.loads(added.output)["id"]

    result = runner.invoke(app, ["chunks", doc_id[:6], "--json"])
    assert json.loads(result.output)[0]["chars"] == "9"

    missing = runner.invoke(app, ["chunks", "zzzz"])
    assert missing.exit_code == 1
    assert "no document matches" in missing.output
