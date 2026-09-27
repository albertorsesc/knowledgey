from knowledgey.domain.slug import has_match, match_key, normalize_slugs, slugify


def test_slugify_lowercases_and_hyphenates() -> None:
    assert slugify("The Neural Maze") == "the-neural-maze"


def test_slugify_collapses_runs_and_trims() -> None:
    assert slugify("  MLOps!!  &  Data  ") == "mlops-data"


def test_match_key_drops_separators_entirely() -> None:
    assert match_key("ml-ops") == "mlops"


def test_separator_variants_share_a_match_key() -> None:
    assert match_key("ML Ops") == match_key("mlops") == match_key("ml-ops")


def test_match_key_does_not_resolve_synonyms() -> None:
    assert match_key("ops") != match_key("operations")


def test_normalize_slugs_drops_empties_and_repeats() -> None:
    assert normalize_slugs(("MLOps", "ml ops", "mlops", "!!!", "Data Eng")) == (
        "mlops",
        "ml-ops",
        "data-eng",
    )


def test_has_match_compares_by_key() -> None:
    assert has_match(("mlops", "rag"), "ML Ops")
    assert not has_match(("mlops", "rag"), "ops")
