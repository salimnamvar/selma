"""Tests for Violation entity — creation, to_dict."""

from selma.domain.entities.violation import Violation
from selma.domain.value_objects.guidance import RuleGuidance


def _make_guidance() -> RuleGuidance:
    """Create a RuleGuidance for testing."""
    return RuleGuidance(
        rule_code="SC001",
        title="Test Rule",
        description="A test rule",
        rationale="For testing",
        severity="error",
        fix_instructions="Fix it",
        correct_example="x = 1",
        anti_pattern="x=1",
        related_rules=(),
        doctrine_section="Section 1",
    )


class TestViolationCreation:
    """Violation creation behavior."""

    def test_required_fields(self) -> None:
        """Violation should accept all required fields."""
        v = Violation(filepath="main.py", line=10, col=5, code="SC001", message="bad")
        assert v.filepath == "main.py"
        assert v.line == 10
        assert v.col == 5
        assert v.code == "SC001"
        assert v.message == "bad"

    def test_default_severity(self) -> None:
        """Violation should default severity to 'error'."""
        v = Violation(filepath="main.py", line=10, col=5, code="SC001", message="bad")
        assert v.severity == "error"

    def test_default_guidance_none(self) -> None:
        """Violation should default guidance to None."""
        v = Violation(filepath="main.py", line=10, col=5, code="SC001", message="bad")
        assert v.guidance is None


class TestViolationToDict:
    """Violation.to_dict behavior."""

    def test_to_dict_base(self) -> None:
        """to_dict should return dict with all required fields."""
        v = Violation(filepath="main.py", line=10, col=5, code="SC001", message="bad")
        d = v.to_dict()
        assert d["file"] == "main.py"
        assert d["line"] == 10
        assert d["col"] == 5
        assert d["code"] == "SC001"
        assert d["severity"] == "error"
        assert d["message"] == "bad"

    def test_to_dict_includes_guidance_when_requested(self) -> None:
        """to_dict with a_include_guidance=True should include guidance."""
        g = _make_guidance()
        v = Violation(filepath="main.py", line=10, col=5, code="SC001", message="bad", guidance=g)
        d = v.to_dict(a_include_guidance=True)
        assert "guidance" in d
        assert d["guidance"]["title"] == "Test Rule"

    def test_to_dict_excludes_guidance_by_default(self) -> None:
        """to_dict without a_include_guidance should not include guidance."""
        g = _make_guidance()
        v = Violation(filepath="main.py", line=10, col=5, code="SC001", message="bad", guidance=g)
        d = v.to_dict()
        assert "guidance" not in d

    def test_to_dict_guidance_none_not_included(self) -> None:
        """to_dict with a_include_guidance=True but no guidance should not include it."""
        v = Violation(filepath="main.py", line=10, col=5, code="SC001", message="bad")
        d = v.to_dict(a_include_guidance=True)
        assert "guidance" not in d


class TestViolationStr:
    """Violation string representation."""

    def test_str(self) -> None:
        """str() should show filepath, line, col, severity, message, code."""
        v = Violation(filepath="main.py", line=10, col=5, code="SC001", message="bad")
        s = str(v)
        assert "main.py:10:5" in s
        assert "error" in s
        assert "SC001" in s
