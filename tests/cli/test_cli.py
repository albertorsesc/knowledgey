import json
from pathlib import Path

from typer.testing import CliRunner

import knowledgey
from knowledgey.cli.app import app

runner = CliRunner()
SRC = Path(knowledgey.__file__).resolve().parent


def test_version_text() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "knowledgey" in result.output


def test_version_json_is_parseable() -> None:
    result = runner.invoke(app, ["version", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["name"] == "knowledgey"


def test_cli_framework_does_not_leak() -> None:
    offenders = [
        str(path.relative_to(SRC))
        for path in SRC.rglob("*.py")
        if "cli" not in path.relative_to(SRC).parts
        and ("import typer" in path.read_text() or "import rich" in path.read_text())
    ]

    assert not offenders, f"CLI framework leaked into: {offenders}"
