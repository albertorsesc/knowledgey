import pytest
from pydantic import ValidationError

from knowledgey.domain.category import Category


def make(**overrides: object) -> Category:
    return Category.model_validate({"label": "MLOps", **overrides})


def test_slug_is_derived_from_the_label() -> None:
    assert make().slug == "mlops"


def test_an_explicit_slug_wins() -> None:
    assert make(slug="ops").slug == "ops"


def test_blank_label_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make(label="   ")


def test_a_label_with_no_usable_characters_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make(label="!!!")


def test_spelling_variants_share_a_key() -> None:
    assert make(label="ML Ops").key == make(label="MLOps").key


def test_categories_are_immutable() -> None:
    category = make()
    with pytest.raises(ValidationError):
        category.label = "other"


def test_as_dict_exposes_slug_and_label() -> None:
    assert make().as_dict() == {"slug": "mlops", "label": "MLOps"}
