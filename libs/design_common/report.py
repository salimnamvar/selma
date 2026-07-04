"""Shared report + violation model for design linters (non-C4).

All linters should produce compatible output shapes for the selma skill.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Violation:
    rule_id: str
    severity: str  # critical | high | medium | low
    message: str
    location: str = ""
    fix_suggestion: str = ""
    principle: str = ""
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "fix_suggestion": self.fix_suggestion,
        }
        if self.principle:
            payload["principle"] = self.principle
        if self.reasoning:
            payload["reasoning"] = self.reasoning
        return payload


@dataclass
class LayerReport:
    filename: str
    layer: str
    total_violations: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    rules_triggered: list[str] = field(default_factory=list)
    violations: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    def to_text(self) -> str:
        lines = []
        lines.append(f"File: {self.filename}")
        lines.append(f"Layer: {self.layer}")
        lines.append(
            f"Violations: {self.total_violations} "
            f"(critical={self.critical}, high={self.high}, medium={self.medium})"
        )
        if self.rules_triggered:
            lines.append(f"Rules: {', '.join(sorted(self.rules_triggered))}")
        lines.append("")
        for v in self.violations:
            loc = v.get("location", "")
            lines.append(f"[{v['severity'].upper():8}] {v['rule_id']}: {v['message']}")
            if v.get("principle"):
                lines.append(f"           principle: {v['principle']}")
            if v.get("reasoning"):
                lines.append(f"           reasoning: {v['reasoning']}")
            if loc:
                lines.append(f"           at {loc}")
            if v.get("fix_suggestion"):
                lines.append(f"           fix: {v['fix_suggestion']}")
            lines.append("")
        return "\n".join(lines)


@dataclass
class ProjectReport:
    layer: str = "uc"
    project_root: str = ""
    files: int = 0
    total_violations: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    principle_assessments: list[dict[str, Any]] = field(default_factory=list)
    project_violations: list[dict[str, Any]] = field(default_factory=list)
    file_reports: list[LayerReport] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "project_root": self.project_root,
            "files": self.files,
            "total_violations": self.total_violations,
            "critical": self.critical,
            "high": self.high,
            "medium": self.medium,
            "principle_assessments": self.principle_assessments,
            "project_violations": self.project_violations,
            "file_reports": [json.loads(r.to_json()) for r in self.file_reports],
        }


def build_layer_report(filename: str, layer: str, violations: list[Violation]) -> LayerReport:
    crit = sum(1 for v in violations if v.severity == "critical")
    hi = sum(1 for v in violations if v.severity == "high")
    med = sum(1 for v in violations if v.severity == "medium")
    rules = sorted({v.rule_id for v in violations})
    return LayerReport(
        filename=filename,
        layer=layer,
        total_violations=len(violations),
        critical=crit,
        high=hi,
        medium=med,
        rules_triggered=rules,
        violations=[v.to_dict() for v in violations],
    )