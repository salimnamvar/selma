"""Report formatting — builds structured reports from violations and assessments."""

from __future__ import annotations

from dataclasses import dataclass, field

from usecase_diagram.domain.entities.violation import AssessmentResult, Violation


@dataclass
class LayerReport:
    """Structured report for a single design layer."""

    layer: str
    violations: list[Violation] = field(default_factory=list)
    assessments: list[AssessmentResult] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(v.severity == "error" for v in self.violations)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")


def build_uc_report(
    violations: list[Violation],
    assessments: list[AssessmentResult] | None = None,
) -> LayerReport:
    """Build a usecase-diagram layer report."""
    return LayerReport(
        layer="usecase-diagram",
        violations=violations,
        assessments=assessments or [],
    )


def format_text_report(report: LayerReport) -> str:
    """Format a LayerReport as human-readable text."""
    lines: list[str] = []
    lines.append(f"=== {report.layer} ===")
    lines.append(f"Errors: {report.error_count}  Warnings: {report.warning_count}")
    lines.append("")

    for v in report.violations:
        loc = f"{v.file}:{v.line}" if v.line else v.file
        lines.append(f"  [{v.severity.upper()}] {v.rule_id}: {v.message}")
        lines.append(f"    at {loc}")
        if v.fix:
            lines.append(f"    fix: {v.fix}")
        lines.append("")

    if report.assessments:
        lines.append("--- Assessments ---")
        for a in report.assessments:
            status = "OK" if a.status == "OK" else "VIOLATED"
            lines.append(f"  [{status}] {a.id} ({a.name}): {a.detail}")
        lines.append("")

    return "\n".join(lines)
