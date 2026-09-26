import json
from collections.abc import Sequence
from typing import Protocol

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from knowledgey.document import Document

console = Console()
error_console = Console(stderr=True)


class Renderable(Protocol):
    def as_dict(self) -> dict[str, str]: ...


def _print_fields(data: dict[str, str]) -> None:
    for key, value in data.items():
        console.print(f"[bold cyan]{key}[/bold cyan]: {value}")


def render(result: Renderable, *, as_json: bool) -> None:
    data = result.as_dict()

    if as_json:
        console.print_json(json.dumps(data))
        return
    _print_fields(data)


def render_many(results: Sequence[Renderable], *, as_json: bool) -> None:
    rows = [result.as_dict() for result in results]
    if as_json:
        console.print_json(json.dumps(rows))
        return
    if not rows:
        console.print("[dim]Nothing stored yet.[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    for column in rows[0]:
        table.add_column(column)
    for row in rows:
        table.add_row(*row.values())

    console.print(table)


def render_document(document: Document, *, raw: bool, as_json: bool) -> None:
    if raw:
        print(document.content)
        return

    detail = document.as_detail()
    if as_json:
        console.print_json(json.dumps(detail))
        return

    body = detail.pop("content")
    _print_fields(detail)
    console.print()
    console.print(Markdown(body))
