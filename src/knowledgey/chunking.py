import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from knowledgey.document import Document

DEFAULT_CHUNK_SIZE = 4000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_SEPARATORS: tuple[str, ...] = (
    "\n---\n",
    "\n\n",
    "\n```\n",
    "\n## ",
    "\n# ",
    "\n**",
    "\n",
    ". ",
    "! ",
    "? ",
    " ",
    "",
)

LengthFn = Callable[[str], int]


@dataclass(frozen=True)
class Chunk:
    document_id: str
    index: int
    text: str

    @property
    def chunk_id(self) -> str:
        """Stable identity: the same document, position and text always give the same id."""
        basis = f"{self.document_id}:{self.index}:{self.text}"
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

    def as_dict(self) -> dict[str, str]:
        first_line = self.text.splitlines()[0] if self.text else ""
        return {
            "id": self.chunk_id,
            "index": str(self.index),
            "chars": str(len(self.text)),
            "starts": first_line[:60],
        }


def split_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    separators: Sequence[str] = DEFAULT_SEPARATORS,
    length: LengthFn = len,
) -> list[str]:
    """
    Cut text into chunks of at most chunk_size, as measured by length, breaking
    at the most structural separator available and repeating each chunk's tail in the next.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=list(separators),
        length_function=length,
    )

    return splitter.split_text(text)


def chunk_document(
    document: Document,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    length: LengthFn = len,
) -> list[Chunk]:
    texts = split_text(
        document.content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length=length,
    )

    return [Chunk(document_id=document.doc_id, index=i, text=t) for i, t in enumerate(texts)]
