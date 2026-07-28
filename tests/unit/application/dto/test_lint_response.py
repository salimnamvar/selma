"""Tests for LintResponse DTO — creation."""

from selma.application.dto.lint_response import LintResponse
from selma.domain.entities.finding import Finding
from selma.domain.value_objects.enums import Severity


class TestLintResponseCreation:
    """LintResponse creation behavior."""

    def test_required_fields(self) -> None:
        """LintResponse should accept findings."""
        r = LintResponse(findings=())
        assert r.findings == ()

    def test_defaults(self) -> None:
        """LintResponse should have sensible defaults."""
        r = LintResponse(findings=())
        assert r.summary == ""
        assert r.has_errors is False

    def test_with_findings(self) -> None:
        """LintResponse should accept findings."""
        f1 = Finding(rule_id="SC001", file="main.py", line=10, severity=Severity.HIGH)
        f2 = Finding(rule_id="SC002", file="main.py", line=20, severity=Severity.LOW)
        r = LintResponse(findings=(f1, f2))
        assert r.finding_count == 2

    def test_finding_count(self) -> None:
        """finding_count should return the number of findings."""
        f = Finding(rule_id="SC001", file="main.py", line=10)
        r = LintResponse(findings=(f,))
        assert r.finding_count == 1

    def test_violation_count(self) -> None:
        """violation_count should count CRITICAL and HIGH findings."""
        f1 = Finding(
            rule_id="SC001", file="main.py", line=10, severity=Severity.CRITICAL
        )
        f2 = Finding(rule_id="SC002", file="main.py", line=20, severity=Severity.HIGH)
        f3 = Finding(rule_id="SC003", file="main.py", line=30, severity=Severity.LOW)
        r = LintResponse(findings=(f1, f2, f3))
        assert r.violation_count == 2

    def test_violation_count_empty(self) -> None:
        """violation_count should be 0 for empty findings."""
        r = LintResponse(findings=())
        assert r.violation_count == 0

    def test_frozen(self) -> None:
        """LintResponse should be immutable."""
        r = LintResponse(findings=())
        assert hasattr(r, "__pydantic_fields__")
        try:
            r.summary = "changed"  # type: ignore[misc]
            assert False, "Should have raised ValidationError"
        except Exception:
            pass
