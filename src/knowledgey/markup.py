from bs4 import BeautifulSoup
from markdownify import markdownify


def html_to_markdown(html: str) -> str:
    """Convert feed HTML to Markdown, discarding scripts and styles entirely."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = markdownify(str(soup), heading_style="ATX", bullets="*")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())
