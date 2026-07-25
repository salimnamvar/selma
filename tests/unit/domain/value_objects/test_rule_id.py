"""Tests for RuleId value object — equality, hashing, validation."""

import pytest

from selma.domain.value_objects.rule_id import RuleId


class TestRuleIdEquality:
    """RuleId equality behavior."""

    def test_same_value_equal(self) -> None:
        """RuleId with same value should be equal."""
        id1 = RuleId("SC001")
        id2 = RuleId("SC001")
        assert id1 == id2

    def test_different_value_not_equal(self) -> None:
        """RuleId with different values should not be equal."""
        id1 = RuleId("SC001")
        id2 = RuleId("SC002")
        assert id1 != id2

    def test_not_equal_to_non_rule_id(self) -> None:
        """RuleId should not be equal to a non-RuleId object."""
        rid = RuleId("SC001")
        assert rid != "SC001"
        assert rid != 42

    def test_equal_same_instance(self) -> None:
        """RuleId should be equal to itself."""
        rid = RuleId("SC001")
        assert rid == rid


class TestRuleIdHashing:
    """RuleId hashing behavior."""

    def test_same_value_same_hash(self) -> None:
        """RuleId with same value should have same hash."""
        id1 = RuleId("SC001")
        id2 = RuleId("SC001")
        assert hash(id1) == hash(id2)

    def test_usable_in_set(self) -> None:
        """RuleId should be usable as a set element."""
        s = {RuleId("SC001"), RuleId("SC001"), RuleId("SC002")}
        assert len(s) == 2

    def test_usable_as_dict_key(self) -> None:
        """RuleId should be usable as a dictionary key."""
        d = {RuleId("SC001"): "value"}
        assert d[RuleId("SC001")] == "value"


class TestRuleIdValidation:
    """RuleId validation behavior."""

    def test_empty_raises(self) -> None:
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            RuleId("")

    def test_valid_value(self) -> None:
        """Non-empty string should create valid RuleId."""
        rid = RuleId("SC001")
        assert rid.value == "SC001"


class TestRuleIdString:
    """RuleId string representations."""

    def test_str(self) -> None:
        """str() should return the raw value."""
        rid = RuleId("SC001")
        assert str(rid) == "SC001"

    def test_repr(self) -> None:
        """repr() should show the RuleId wrapper."""
        rid = RuleId("SC001")
        assert repr(rid) == "RuleId('SC001')"
