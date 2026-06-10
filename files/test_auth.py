import pytest
from typing import Optional, Type

from tests.fixtures.hints_fixtures import (
    hints_simple,
    hints_optional,
    hints_plain,
    hints_no_annotation,
    hints_wrong_type,
    HintsWithSimpleType,
    HintsWithOptionalType,
    HintsWithPlainType,
    HintsWithNoAnnotation,
    HintsWithWrongType,
    BaseHandler,
    ConcreteHandler,
)


# ===========================================================================
# attr_class_types — classmethod
# ===========================================================================

def test_attr_class_types_returns_hint_for_known_attr():
    result = HintsWithSimpleType.attr_class_types(attr_name="handler")
    assert result is not None


def test_attr_class_types_returns_none_for_unknown_attr():
    result = HintsWithSimpleType.attr_class_types(attr_name="unknown_attr")
    assert result is None


def test_attr_class_types_returns_none_when_no_annotation():
    result = HintsWithNoAnnotation.attr_class_types(attr_name="handler")
    assert result is None


def test_attr_class_types_optional_hint_has_args():
    # Optional[BaseHandler] → has __args__
    result = HintsWithOptionalType.attr_class_types(attr_name="handler")
    assert hasattr(result, "__args__")


def test_attr_class_types_plain_type_has_no_args():
    # BaseHandler (plain) → no __args__
    result = HintsWithPlainType.attr_class_types(attr_name="handler")
    assert not hasattr(result, "__args__")


def test_attr_class_types_optional_args_contain_base_handler():
    # Optional[BaseHandler].__args__ = (BaseHandler, NoneType)
    result = HintsWithOptionalType.attr_class_types(attr_name="handler")
    assert BaseHandler in result.__args__


# ===========================================================================
# _get_class_type — type check passes
# ===========================================================================

def test_get_class_type_returns_correct_class_with_type_hint(hints_simple):
    result = hints_simple._get_class_type("handler")
    assert result is ConcreteHandler


def test_get_class_type_returns_correct_class_with_optional_hint(hints_optional):
    # Optional[BaseHandler] → ConcreteHandler is subclass of BaseHandler → OK
    result = hints_optional._get_class_type("handler")
    assert result is ConcreteHandler


def test_get_class_type_returns_correct_class_with_plain_hint(hints_plain):
    # Plain type → check skipped → returns ConcreteHandler
    result = hints_plain._get_class_type("handler")
    assert result is ConcreteHandler


def test_get_class_type_returns_correct_class_when_no_annotation(hints_no_annotation):
    # No annotation → _types is None → check skipped
    result = hints_no_annotation._get_class_type("handler")
    assert result is ConcreteHandler


def test_get_class_type_returns_none_for_missing_attr(hints_simple):
    result = hints_simple._get_class_type("nonexistent_attr")
    assert result is None


# ===========================================================================
# _get_class_type — check skipped (no __args__)
# ===========================================================================

def test_get_class_type_skips_check_when_type_has_no_args(hints_plain):
    """Plain type annotation → no __args__ → assert block skipped."""
    # No AssertionError even though ConcreteHandler doesn't strictly
    # match a plain BaseHandler annotation at class level
    result = hints_plain._get_class_type("handler")
    assert result is not None


def test_get_class_type_skips_check_when_types_is_none(hints_no_annotation):
    """No annotation → _types is None → assert block skipped."""
    result = hints_no_annotation._get_class_type("handler")
    assert result is not None


# ===========================================================================
# _get_class_type — AssertionError on type mismatch
# ===========================================================================

def test_get_class_type_raises_assertion_error_on_wrong_type(hints_wrong_type):
    """Optional[UnrelatedHandler] → ConcreteHandler not subclass → AssertionError."""
    with pytest.raises(AssertionError):
        hints_wrong_type._get_class_type("handler")


def test_get_class_type_assertion_message_contains_attr_name(hints_wrong_type):
    with pytest.raises(AssertionError, match="handler"):
        hints_wrong_type._get_class_type("handler")


def test_get_class_type_assertion_message_contains_must_be_type_of(hints_wrong_type):
    with pytest.raises(AssertionError, match="must be type of"):
        hints_wrong_type._get_class_type("handler")
