import sys
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from pydantic import ValidationError

from knowledgey.cli.render import error_console, render, render_many
from knowledgey.config import get_settings
from knowledgey.feed import FeedParseError
from knowledgey.fetcher import ContentFetcher, FetchError, HttpxFetcher
from knowledgey.ingest import add_pasted_document, ingest_feed, ingest_sources
from knowledgey.registry import UnknownCategoryError, add_category, add_source, select_sources
from knowledgey.store import (
    CategoryStore,
    DocumentStore,
    JsonFileCategoryStore,
    JsonFileDocumentStore,
    JsonFileSourceStore,
    SourceStore,
)
from knowledgey.version import get_version

category_app = typer.Typer(help="Manage the category vocabulary.", no_args_is_help=True)
source_app = typer.Typer(help="Manage the sources you fetch from.", no_args_is_help=True)
app = typer.Typer(help="Ingest and search your knowledge sources.", no_args_is_help=True)


def _document_store() -> DocumentStore:
    return JsonFileDocumentStore(get_settings().data_dir / "documents.json")


def _content_fetcher() -> ContentFetcher:
    return HttpxFetcher()


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


@app.command("fetch")
def fetch(
    url: Annotated[str, typer.Argument(help="URL of an RSS or Atom feed.")],
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """Fetch a feed and store its entries as documents."""
    try:
        result = ingest_feed(_content_fetcher(), _document_store(), url=url)
    except (FetchError, FeedParseError) as exc:
        fail(str(exc))

    render(result, as_json=as_json)


@app.command("list")
def list_documents(
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """List stored documents, newest first."""
    render_many(_document_store().list_all(), as_json=as_json)


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


def _category_store() -> CategoryStore:
    return JsonFileCategoryStore(get_settings().data_dir / "categories.json")


def _source_store() -> SourceStore:
    return JsonFileSourceStore(get_settings().data_dir / "sources.json")


@category_app.command("add")
def category_add(
    label: Annotated[str, typer.Argument(help="Display name, for example 'MLOps'.")],
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """Declare a category that sources can be filed under."""
    try:
        result = add_category(_category_store(), label=label)
    except ValidationError as exc:
        fail(describe(exc))

    render(result, as_json=as_json)


@category_app.command("list")
def category_list(
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """List the declared categories."""
    render_many(_category_store().list_all(), as_json=as_json)


@source_app.command("add")
def source_add(
    name: Annotated[str, typer.Option("--name", "-n", help="Display name of the source.")],
    feed_url: Annotated[str, typer.Option("--feed-url", "-u", help="RSS or Atom URL.")],
    category: Annotated[
        list[str] | None,
        typer.Option("--category", "-c", help="Repeatable. Must already be declared."),
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """Register a feed to fetch from."""
    try:
        result = add_source(
            _category_store(),
            _source_store(),
            name=name,
            feed_url=feed_url,
            category_labels=category or [],
        )
    except UnknownCategoryError as exc:
        fail(str(exc))
    except ValidationError as exc:
        fail(describe(exc))

    render(result, as_json=as_json)


@source_app.command("list")
def source_list(
    category: Annotated[
        str | None, typer.Option("--category", "-c", help="Show only this category.")
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """List registered sources, optionally filtered by category."""
    sources = select_sources(_source_store(), category=category, enabled_only=False)
    render_many(sources, as_json=as_json)


@source_app.command("fetch")
def source_fetch(
    category: Annotated[
        str | None, typer.Option("--category", "-c", help="Only sources in this category.")
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output in JSON format.")] = False,
) -> None:
    """Fetch every enabled source, optionally only those in one category."""
    sources = _source_store()
    selected = select_sources(sources, category=category)
    if not selected:
        fail("no enabled sources match. Register one with: kg source add")

    results = ingest_sources(_content_fetcher(), _document_store(), sources, selected)
    render_many(results, as_json=as_json)
    if any(not result.ok for result in results):
        raise typer.Exit(code=1)


app.add_typer(category_app, name="category")
app.add_typer(source_app, name="source")
