"""Report formatting — builds structured reports from violations and assessments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from usecase_diagram.domain.entities.violation import AssessmentResult, Violation


@dataclass
class LayerReport:
    """Structured report for a single design layer.

    Attributes:
        layer (str): Layer name.
        violations (List[Violation]): List of violations.
        assessments (List[AssessmentResult]): List of assessment results.
    """

    layer: str = field(metadata={"description": "Layer name"})
    violations: List[Violation] = field(
        default_factory=list, metadata={"description": "List of violations"}
    )
    assessments: List[AssessmentResult] = field(
        default_factory=list, metadata={"description": "List of assessment results"}
    )

    @property
    def has_errors(self) -> bool:
        """Whether any violations have error severity."""
        result: bool = any(v.severity == "error" for v in self.violations)
        return result

    @property
    def error_count(self) -> int:
        """Count of error-severity violations."""
        result: int = sum(1 for v in self.violations if v.severity == "error")
        return result

    @property
    def warning_count(self) -> int:
        """Count of warning-severity violations."""
        result: int = sum(1 for v in self.violations if v.severity == "warning")
        return result


def build_uc_report(
    a_violations: List[Violation],
    a_assessments: Optional[List[AssessmentResult]] = None,
) -> LayerReport:
    """Build a usecase-diagram layer report.

    Args:
        a_violations (List[Violation]): Violations to include.
        a_assessments (Optional[List[AssessmentResult]]): Assessments to include.

    Returns:
        LayerReport: Structured report.
    """
    result: LayerReport = LayerReport(
        layer="usecase-diagram",
        violations=a_violations,
        assessments=a_assessments or [],
    )
    return result


def format_text_report(a_report: LayerReport) -> str:
    """Format a LayerReport as human-readable text.

    Args:
        a_report (LayerReport): Report to format.

    Returns:
        str: Formatted text report.
    """
    lines: List[str] = []
    lines.append(f"=== {a_report.layer} ===")
    lines.append(f"Errors: {a_report.error_count}  Warnings: {a_report.warning_count}")
    lines.append("")

    for v in a_report.violations:
        loc: str = f"{v.file}:{v.line}" if v.line else v.file
        lines.append(f"  [{v.severity.upper()}] {v.rule_id}: {v.message}")
        lines.append(f"    at {loc}")
        if v.fix:
            lines.append(f"    fix: {v.fix}")
        lines.append("")

    if a_report.assessments:
        lines.append("--- Assessments ---")
        for a in a_report.assessments:
            status: str = "OK" if a.status == "OK" else "VIOLATED"
            lines.append(f"  [{status}] {a.id} ({a.name}): {a.detail}")
        lines.append("")

    result: str = "\n".join(lines)
    return result
