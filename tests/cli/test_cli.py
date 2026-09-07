import json
from pathlib import Path

from typer.testing import CliRunner

from knowledgey.cli.app import app

runner = CliRunner()
SRC = Path(__file__).resolve().parens[1] / "src" / "knowledgey"

def test_version_text() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "knowledgey" in result.output



