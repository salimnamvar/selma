"""Tests for LintResult aggregate — add_finding, complete, violation_count."""

import pytest

from selma.domain.aggregates.lint_result import LintResult
from selma.domain.entities.finding import Finding
from selma.domain.entities.source_file import SourceFile
from selma.domain.exceptions.domain_errors import LintResultAlreadyComplete
from selma.domain.value_objects.enums import Severity
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.source_hash import SourceHash


def _make_source_file() -> SourceFile:
    """Create a SourceFile for testing."""
    return SourceFile(path=FilePath("/src/main.py"), hash=SourceHash("abc123"))


def _make_finding(
    a_severity: Severity = Severity.MEDIUM, a_rule_id: str = "SC001"
) -> Finding:
    """Create a Finding for testing."""
    return Finding(rule_id=a_rule_id, file="main.py", line=10, severity=a_severity)


class TestLintResultAddFinding:
    """LintResult.add_finding behavior."""

    def test_add_single_finding(self) -> None:
        """Adding a finding should increase finding count."""
        lr = LintResult(source_file=_make_source_file())
        lr.add_finding(_make_finding())
        assert lr.finding_count == 1

    def test_add_multiple_findings(self) -> None:
        """Adding multiple findings should accumulate."""
        lr = LintResult(source_file=_make_source_file())
        lr.add_finding(_make_finding(a_rule_id="SC001"))
        lr.add_finding(_make_finding(a_rule_id="SC002"))
        assert lr.finding_count == 2

    def test_findings_returns_tuple(self) -> None:
        """Findings property should return a tuple."""
        lr = LintResult(source_file=_make_source_file())
        lr.add_finding(_make_finding())
        assert isinstance(lr.findings, tuple)
        assert len(lr.findings) == 1


class TestLintResultComplete:
    """LintResult.complete behavior."""

    def test_complete_prevents_adding(self) -> None:
        """After complete(), adding a finding should raise."""
        lr = LintResult(source_file=_make_source_file())
        lr.add_finding(_make_finding())
        lr.complete()
        with pytest.raises(LintResultAlreadyComplete):
            lr.add_finding(_make_finding())

    def test_complete_without_findings(self) -> None:
        """complete() should work even with no findings."""
        lr = LintResult(source_file=_make_source_file())
        lr.complete()
        assert lr.finding_count == 0


class TestLintResultViolationCount:
    """LintResult.violation_count behavior."""

    def test_no_violations(self) -> None:
        """violation_count should be 0 when no violations."""
        lr = LintResult(source_file=_make_source_file())
        lr.add_finding(_make_finding(a_severity=Severity.LOW))
        assert lr.violation_count == 0

    def test_has_violations(self) -> None:
        """violation_count should count CRITICAL and HIGH findings."""
        lr = LintResult(source_file=_make_source_file())
        lr.add_finding(_make_finding(a_severity=Severity.CRITICAL))
        lr.add_finding(_make_finding(a_severity=Severity.HIGH))
        lr.add_finding(_make_finding(a_severity=Severity.LOW))
        assert lr.violation_count == 2

    def test_has_violations_property(self) -> None:
        """has_violations should be True when violations exist."""
        lr = LintResult(source_file=_make_source_file())
        lr.add_finding(_make_finding(a_severity=Severity.HIGH))
        assert lr.has_violations is True

    def test_no_violations_property(self) -> None:
        """has_violations should be False when no violations."""
        lr = LintResult(source_file=_make_source_file())
        lr.add_finding(_make_finding(a_severity=Severity.LOW))
        assert lr.has_violations is False

    def test_empty_result_no_violations(self) -> None:
        """Empty result should have no violations."""
        lr = LintResult(source_file=_make_source_file())
        assert lr.violation_count == 0
        assert lr.has_violations is False
