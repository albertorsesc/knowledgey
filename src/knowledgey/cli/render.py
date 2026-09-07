import json
from typing import Protocol

from rich.console import Console

console = Console()
error_console = Console(stderr=True)

class Renderable(Protocol):
    def as_dict(self) -> dict[str, str]: ...


def render(result: Renderable, *, as_json: bool) -> None:
    data = result.as_dict()

    if as_json:
        console.print_json(json.dumps(data))
        return
    for key, value in data.items():
        console.print(f"[bold cyan]{key}[/bold cyan]: {value}")
