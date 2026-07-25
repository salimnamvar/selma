"""Tests for Finding entity — creation, is_violation."""

from selma.domain.entities.finding import Finding
from selma.domain.value_objects.severity import Severity


class TestFindingCreation:
    """Finding creation behavior."""

    def test_required_fields(self) -> None:
        """Finding should accept required fields."""
        f = Finding(rule_id="SC001", file="main.py", line=10)
        assert f.rule_id == "SC001"
        assert f.file == "main.py"
        assert f.line == 10

    def test_defaults(self) -> None:
        """Finding should have sensible defaults."""
        f = Finding(rule_id="SC001", file="main.py", line=10)
        assert f.col == 0
        assert f.message == ""
        assert f.severity == Severity.MEDIUM
        assert f.guidance is None
        assert f.filepath == ""


class TestFindingIsViolation:
    """Finding.is_violation behavior."""

    def test_critical_is_violation(self) -> None:
        """CRITICAL severity should be a violation."""
        f = Finding(rule_id="SC001", file="main.py", line=10, severity=Severity.CRITICAL)
        assert f.is_violation is True

    def test_high_is_violation(self) -> None:
        """HIGH severity should be a violation."""
        f = Finding(rule_id="SC001", file="main.py", line=10, severity=Severity.HIGH)
        assert f.is_violation is True

    def test_medium_not_violation(self) -> None:
        """MEDIUM severity should not be a violation."""
        f = Finding(rule_id="SC001", file="main.py", line=10, severity=Severity.MEDIUM)
        assert f.is_violation is False

    def test_low_not_violation(self) -> None:
        """LOW severity should not be a violation."""
        f = Finding(rule_id="SC001", file="main.py", line=10, severity=Severity.LOW)
        assert f.is_violation is False

    def test_informational_not_violation(self) -> None:
        """INFORMATIONAL severity should not be a violation."""
        f = Finding(rule_id="SC001", file="main.py", line=10, severity=Severity.INFORMATIONAL)
        assert f.is_violation is False


class TestFindingStr:
    """Finding string representation."""

    def test_str_with_filepath(self) -> None:
        """str() should use filepath when available."""
        f = Finding(rule_id="SC001", file="main.py", line=10, col=5, message="bad", filepath="/src/main.py")
        s = str(f)
        assert "/src/main.py:10:5" in s
        assert "SC001" in s

    def test_str_without_filepath(self) -> None:
        """str() should fall back to file when filepath is empty."""
        f = Finding(rule_id="SC001", file="main.py", line=10, message="bad")
        s = str(f)
        assert "main.py:10" in s
