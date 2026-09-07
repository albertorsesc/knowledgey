import sys
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from pydantic import ValidationError

from knowledgey.cli.render import error_console, render
from knowledgey.config import get_settings
from knowledgey.ingest import add_pasted_document
from knowledgey.store import DocumentStore, JsonFileDocumentStore
from knowledgey.version import get_version

app = typer.Typer(help="Ingest and search your knowledge sources.", no_args_is_help=True)


def _document_store() -> DocumentStore:
    return JsonFileDocumentStore(get_settings().data_dir / "documents.json")


def fail(message: str) -> NoReturn:
    error_console.print(f"[bold red]Error:[/bold red] {message}")
    raise typer.Exit(code=1)


def describe(exc: ValidationError) -> str:
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first["loc"]) or "input"
    return f"{field}: {first['msg']}"


def _read_content(file: Path | None) -> str:
    if file is not None:
        return file.read_text(encoding="utf-8")
    if sys.stdin.isatty():
        fail("no input. Pipe text in, or pass --file.")
    return sys.stdin.read()


@app.command("add")
def add(
    title: Annotated[str, typer.Option("--title", "-t", help="Title of the document.")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Read from a file.")] = None,
    url: Annotated[str | None, typer.Option("--url", help="Original URL, if any.")] = None,
    author: Annotated[list[str] | None, typer.Option("--author", help="Repeatable.")] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """Add a document from a file or standard input."""
    try:
        result = add_pasted_document(
            _document_store(),
            title=title,
            content=_read_content(file),
            url=url,
            authors=author,
        )
    except ValidationError as exc:
        fail(describe(exc))

    render(result, as_json=as_json)


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
