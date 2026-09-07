from typing import Annotated

import typer

from knowledgey.cli.render import render
from knowledgey.config import get_settings
from knowledgey.version import get_version

app = typer.Typer(help="Ingest and search your knowledge sources.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Ingest and search your knowledge sources."""


@app.command("config")
def show_config(
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """Show the active configuration."""
    render(get_settings(), as_json=as_json)


@app.command()
def version(
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """Show the installed version."""
    render(get_version(), as_json=as_json)
