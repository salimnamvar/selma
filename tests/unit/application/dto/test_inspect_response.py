"""Tests for InspectResponse DTO."""

from selma.application.dto.inspect_response import InspectResponse
from selma.domain.entities.finding import Finding
from selma.domain.value_objects.enums import Severity


def test_empty() -> None:
    """Test empty."""
    resp = InspectResponse()
    assert resp.finding_count == 0
    assert resp.has_errors is False


def test_with_findings() -> None:
    """Test with findings."""
    finding = Finding(
        rule_id="SC-001",
        file="a.py",
        line=1,
        message="x",
        severity=Severity.HIGH,
    )
    resp = InspectResponse(findings=(finding,), has_errors=True, summary="1 issue")
    assert resp.finding_count == 1
    assert resp.has_errors is True
