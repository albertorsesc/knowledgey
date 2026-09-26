import pytest

from knowledgey.chunking import chunk_document, split_text
from knowledgey.document import Document, Origin


def _words(text: str) -> int:
    return len(text.split())


def test_short_text_is_one_chunk() -> None:
    assert split_text("just a note", chunk_size=100, chunk_overlap=0) == ["just a note"]


def test_paragraphs_are_packed_up_to_the_size() -> None:
    a, b, c = "a" * 100, "b" * 100, "c" * 100
    text = f"{a}\n\n{b}\n\n{c}"

    assert split_text(text, chunk_size=250, chunk_overlap=0) == [f"{a}\n\n{b}", c]


def test_a_heading_opens_the_next_chunk() -> None:
    text = "x" * 90 + "\n## Head\n" + "y" * 90

    chunks = split_text(text, chunk_size=100, chunk_overlap=0)

    assert len(chunks) == 2
    assert chunks[1].startswith("## Head")


def test_overlap_repeats_the_tail_of_the_previous_chunk() -> None:
    text = " ".join(f"w{i}" for i in range(50))

    chunks = split_text(text, chunk_size=30, chunk_overlap=10)

    assert len(chunks) > 1
    assert max(len(chunk) for chunk in chunks) <= 30
    assert all(chunks[i].split()[-1] in chunks[i + 1].split() for i in range(len(chunks) - 1))


def test_text_without_separators_is_hard_cut() -> None:
    assert split_text("z" * 25, chunk_size=10, chunk_overlap=0) == ["z" * 10, "z" * 10, "z" * 5]


def test_blank_text_yields_nothing() -> None:
    assert split_text("  \n\n ", chunk_size=10, chunk_overlap=0) == []


def test_no_chunk_exceeds_the_size() -> None:
    text = "\n\n".join(f"Paragraph {i}. " + "word " * (i * 7) for i in range(1, 40))

    chunks = split_text(text, chunk_size=500, chunk_overlap=50)

    assert chunks
    assert max(len(chunk) for chunk in chunks) <= 500


def test_overlap_must_be_smaller_than_size() -> None:
    with pytest.raises(ValueError):
        split_text("abc", chunk_size=10, chunk_overlap=10)


def test_size_can_be_measured_in_units_other_than_characters() -> None:
    text = "alpha beta gamma delta epsilon zeta"

    chunks = split_text(text, chunk_size=2, chunk_overlap=0, length=_words)

    assert chunks == ["alpha beta", "gamma delta", "epsilon zeta"]


def test_chunk_ids_are_stable_and_distinct() -> None:
    document = Document(title="T", content="one. two. three. four.", origin=Origin.PASTE)

    first = chunk_document(document, chunk_size=12, chunk_overlap=6)
    again = chunk_document(document, chunk_size=12, chunk_overlap=6)

    assert len(first) > 1
    assert [c.chunk_id for c in first] == [c.chunk_id for c in again]
    assert len({c.chunk_id for c in first}) == len(first)
    assert [c.index for c in first] == list(range(len(first)))
    assert all(c.document_id == document.doc_id for c in first)
