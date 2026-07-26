"""Reporters — finding output formatters."""

from __future__ import annotations

import json

from selma.application.ports.reporter_port import FindingReporter
from selma.domain.entities.finding import Finding
from selma.domain.value_objects.result import Result


class DefaultReporter(FindingReporter):
    """Default human-readable reporter."""

    def report(self, a_findings: tuple[Finding, ...]) -> Result[str]:
        lines: list[str] = []
        for f in a_findings:
            lines.append(str(f))
        return Result.success("\n".join(lines))


class JsonReporter(FindingReporter):
    """JSON reporter with optional guidance."""

    def __init__(self, a_guide: bool = False) -> None:
        self._guide = a_guide

    def report(self, a_findings: tuple[Finding, ...]) -> Result[str]:
        output: list[dict[str, object]] = []
        for f in a_findings:
            d: dict[str, object] = {
                "file": f.filepath or f.file,
                "line": f.line,
                "col": f.col,
                "code": f.rule_id,
                "severity": f.severity,
                "message": f.message,
            }
            if self._guide and f.guidance:
                d["guidance"] = {
                    "title": f.guidance.title,
                    "description": f.guidance.description,
                    "rationale": f.guidance.rationale,
                    "severity": f.guidance.severity,
                    "fix_instructions": f.guidance.fix_instructions,
                    "correct_example": f.guidance.correct_example,
                    "anti_pattern": f.guidance.anti_pattern,
                    "related_rules": f.guidance.related_rules,
                    "doctrine_section": f.guidance.doctrine_section,
                    "hints": f.guidance.hints,
                }
            output.append(d)
        return Result.success(json.dumps(output, indent=2))


class GccReporter(FindingReporter):
    """GCC-style reporter."""

    def report(self, a_findings: tuple[Finding, ...]) -> Result[str]:
        lines: list[str] = []
        for f in a_findings:
            lines.append(
                f"{f.filepath or f.file}:{f.line}:{f.col}: "
                + f"{f.severity} [{f.rule_id}] {f.message}"
            )
        return Result.success("\n".join(lines))
