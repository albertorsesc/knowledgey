import re
from collections.abc import Iterable


def slugify(value: str) -> str:
    """
    Lowercase, keep letters and digits,
    collapse everything else into single hyphens.
    """
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def match_key(value: str) -> str:
    """Comparison identity for labels differing only in case or separators."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def normalize_slugs(values: Iterable[str]) -> tuple[str, ...]:
    """Slugify each value, dropping empties and repeats, keeping first-seen order."""
    kept: list[str] = []
    for raw in values:
        slug = slugify(raw)
        if slug and slug not in kept:
            kept.append(slug)
    return tuple(kept)


def has_match(slugs: Iterable[str], label: str) -> bool:
    """Whether any slug names the same category as the label, ignoring case and separators."""
    wanted = match_key(label)
    return any(match_key(slug) == wanted for slug in slugs)
