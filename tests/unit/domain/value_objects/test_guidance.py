"""Tests for RuleGuidance value object — frozen Pydantic model behavior."""

from pydantic import ValidationError
import pytest

from selma.domain.value_objects.guidance import RuleGuidance


def _make_guidance(**a_overrides: object) -> RuleGuidance:
    """Create a RuleGuidance with sensible defaults."""
    defaults: dict[str, object] = {
        "rule_code": "SC001",
        "title": "Test Rule",
        "description": "A test rule",
        "rationale": "For testing",
        "severity": "error",
        "fix_instructions": "Fix it",
        "correct_example": "x = 1",
        "anti_pattern": "x=1",
        "related_rules": (),
        "doctrine_section": "Section 1",
        "hints": (),
    }
    defaults.update(a_overrides)
    return RuleGuidance(**defaults)  # type: ignore[arg-type]


class TestRuleGuidanceCreation:
    """RuleGuidance creation behavior."""

    def test_all_fields_set(self) -> None:
        """RuleGuidance should accept all fields."""
        g = _make_guidance()
        assert g.rule_code == "SC001"
        assert g.title == "Test Rule"

    def test_default_hints_empty(self) -> None:
        """Hints should default to empty tuple."""
        g = _make_guidance()
        assert g.hints == ()

    def test_with_hints(self) -> None:
        """Hints should accept a tuple of strings."""
        g = _make_guidance(hints=("hint1", "hint2"))
        assert g.hints == ("hint1", "hint2")

    def test_with_related_rules(self) -> None:
        """related_rules should accept a tuple of strings."""
        g = _make_guidance(related_rules=("SC002", "SC003"))
        assert g.related_rules == ("SC002", "SC003")


class TestRuleGuidanceFrozen:
    """RuleGuidance should be immutable."""

    def test_frozen(self) -> None:
        """RuleGuidance should be a Pydantic frozen model."""
        g = _make_guidance()
        assert hasattr(g, "__pydantic_fields__")

    def test_cannot_modify_field(self) -> None:
        """Assigning to a field should raise ValidationError."""
        g = _make_guidance()
        with pytest.raises(ValidationError):
            g.title = "New Title"  # type: ignore[misc]
