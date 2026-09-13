import pytest
from pydantic import ValidationError

from knowledgey.slug import slugify
from knowledgey.source import Source


def make(**overrides: object) -> Source:
    fields: dict[str, object] = {
        "name": "The Neural Maze",
        "feed_url": "https://theneuralmaze.substack.com/feed",
    }
    return Source.model_validate({**fields, **overrides})


def test_slug_is_derived_from_the_name() -> None:
    assert make().slug == "the-neural-maze"


def test_an_explicit_slug_wins() -> None:
    assert make(slug="tnm").slug == "tnm"


def test_punctuation_and_runs_collapse() -> None:
    assert slugify("Hamel's  Substack!! (2025)") == "hamel-s-substack-2025"


def test_a_name_with_no_usable_characters_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make(name="!!!")


def test_blank_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make(name="   ")


def test_feed_url_must_be_http() -> None:
    with pytest.raises(ValidationError):
        make(feed_url="theneuralmaze.substack.com/feed")


def test_categories_are_normalised_and_deduplicated() -> None:
    source = make(categories=("MLOps", "ml ops", "mlops", "Data Eng"))
    assert source.categories == ("mlops", "ml-ops", "data-eng")


def test_categories_default_to_empty() -> None:
    assert make().categories == ()


def test_sources_are_immutable() -> None:
    source = make()
    with pytest.raises(ValidationError):
        source.name = "other"


def test_as_dict_reports_never_fetched() -> None:
    assert make().as_dict()["last_fetched"] == "never"
