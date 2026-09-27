import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """A piece of one document, small enough to embed and retrieve on its own."""

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
