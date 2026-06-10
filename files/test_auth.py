import pytest
from typing import Optional, Type

from tests.fixtures.hints_fixtures import (
    hints_simple,
    hints_optional,
    hints_no_annotation,
    hints_wrong_type,
    HintsWithSimpleType,
    HintsWithOptionalType,
    HintsWithNoAnnotation,
    HintsWithWrongType,
    BaseHandler,
    ConcreteHandler,
    UnrelatedHandler,
)


# ===========================================================================
# attr_class_types — classmethod
# ===========================================================================

def test_attr_class_types_returns_type_hint_for_known_attr():
    result = HintsWithSimpleType.attr_class_types(attr_name="handler")
    assert result is not None


def test_attr_class_types_returns_none_for_unknown_attr():
    result = HintsWithSimpleType.attr_class_types(attr_name="unknown_attr")
    assert result is None


def test_attr_class_types_returns_none_when_no_annotation():
    result = HintsWithNoAnnotation.attr_class_types(attr_name="handler")
    assert result is None


def test_attr_class_types_returns_optional_hint():
    result = HintsWithOptionalType.attr_class_types(attr_name="handler")
    assert result is not None
    assert hasattr(result, "__args__")


def test_attr_class_types_result_contains_base_class_in_args():
    result = HintsWithOptionalType.attr_class_types(attr_name="handler")
    # Optional[Type[BaseHandler]] → __args__ contains Type[BaseHandler]
    assert any(
        hasattr(arg, "__args__") and BaseHandler in arg.__args__
        for arg in result.__args__
        if arg is not type(None)
    )


# ===========================================================================
# _get_class_type — type check passes
# ===========================================================================

def test_get_class_type_returns_attr_class(hints_simple):
    result = hints_simple._get_class_type("handler")
    assert result is ConcreteHandler


def test_get_class_type_returns_attr_class_with_optional_hint(hints_optional):
    result = hints_optional._get_class_type("handler")
    assert result is ConcreteHandler


def test_get_class_type_returns_attr_class_when_no_annotation(hints_no_annotation):
    result = hints_no_annotation._get_class_type("handler")
    assert result is ConcreteHandler


def test_get_class_type_returns_none_for_missing_attr(hints_simple):
    result = hints_simple._get_class_type("nonexistent_attr")
    assert result is None


# ===========================================================================
# _get_class_type — type check skipped (no __args__)
# ===========================================================================

def test_get_class_type_skips_check_when_type_has_no_args(hints_simple):
    """Simple Type[X] hint without Union/Optional → no __args__ at top level → skip check."""
    # Type[BaseHandler] doesn't have __args__ at the top-level hint
    # so the assert block is skipped and ConcreteHandler is returned
    result = hints_simple._get_class_type("handler")
    assert result is not None


# ===========================================================================
# _get_class_type — AssertionError on type mismatch
# ===========================================================================

def test_get_class_type_raises_assertion_error_on_wrong_type(hints_wrong_type):
    """
    When _types has __args__ and _AttrClass is not a subclass
    of any expected type → AssertionError.
    """
    with pytest.raises(AssertionError):
        hints_wrong_type._get_class_type("handler")


def test_get_class_type_assertion_error_message_contains_attr_name(hints_wrong_type):
    with pytest.raises(AssertionError, match="handler"):
        hints_wrong_type._get_class_type("handler")


def test_get_class_type_assertion_error_message_contains_type_info(hints_wrong_type):
    with pytest.raises(AssertionError, match="must be type of"):
        hints_wrong_type._get_class_type("handler")
