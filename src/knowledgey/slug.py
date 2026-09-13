import re


def slugify(value: str) -> str:
    """
    Lowercase, keep letters and digits,
    collapse everything else into single hyphens.
    """
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def match_key(value: str) -> str:
    """Comparison identity for labels differing only in case or separators."""
    return re.sub(r"[^a-z0-9]", "", value.lower())
