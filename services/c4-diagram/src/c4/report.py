"""Reporting helpers for C4 linter."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from .ir import C4Diagram, Violation


@dataclass
class Report:
    filename: str
    total_violations: int
    critical: int
    high: int
    medium: int
    rules_triggered: list[str]
    violations: list[dict[str, Any]]
    levels: list[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    def to_text(self) -> str:
        lines = []
        lines.append(f"File: {self.filename}")
        lines.append(f"Levels: {', '.join(self.levels) if self.levels else 'unknown'}")
        lines.append(f"Violations: {self.total_violations} (critical={self.critical}, high={self.high}, medium={self.medium})")
        if self.rules_triggered:
            lines.append(f"Rules: {', '.join(sorted(self.rules_triggered))}")
        lines.append("")
        for v in self.violations:
            loc = v.get("node") or (f"{v.get('edge')[0]}->{v.get('edge')[1]}" if v.get("edge") else "")
            lines.append(f"[{v['severity'].upper():8}] {v['rule_id']}: {v['message']}")
            if loc:
                lines.append(f"           at {loc}")
            if v.get("fix_suggestion"):
                lines.append(f"           fix: {v['fix_suggestion']}")
            lines.append("")
        return "\n".join(lines)


def build_report(diagram: C4Diagram, violations: list[Violation]) -> Report:
    crit = sum(1 for v in violations if v.severity == "critical")
    hi = sum(1 for v in violations if v.severity == "high")
    med = sum(1 for v in violations if v.severity == "medium")
    rules = sorted({v.rule_id for v in violations})
    return Report(
        filename=diagram.info.filename,
        total_violations=len(violations),
        critical=crit,
        high=hi,
        medium=med,
        rules_triggered=rules,
        violations=[v.to_dict() for v in violations],
        levels=diagram.info.levels,
    )
