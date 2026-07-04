"""SQ fixer (header + notes skeleton)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .ir import SQDiagram
from .validator import validate_sq
from .rewriter import rewrite_sq
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


@dataclass
class SQFixResult:
    diagram: SQDiagram
    fixes_applied: list[dict] = field(default_factory=list)


def apply_sq_fixes(diagram: SQDiagram, violations: list[Violation] | None = None) -> SQFixResult:
    if violations is None:
        violations = validate_sq(diagram)
    fixes: list[dict] = []
    d = diagram
    if any(v.rule_id in ("SQ-002", "SQ-004") for v in violations):
        src = d.source
        if "@startuml" in src and "Scope:" not in src[:2000]:
            header = (
                "' === HEADER ========================================\n"
                "' Scope: SQ for UC\n"
                "' Preconditions: ...\n"
                "' ===================================================\n\n"
                "note over [first]\n"
                "  Scope: ...\n  Preconditions: ...\n  Flow: ...\n  State: ...\n  Failure: ...\n  Success: ...\nend note\n"
            )
            lines = src.splitlines(keepends=True)
            out = []
            ins = False
            for ln in lines:
                out.append(ln)
                if not ins and ln.strip().lower().startswith("@startuml"):
                    out.append(header)
                    ins = True
            d.source = "".join(out)
            fixes.append({"rule": "SQ-004", "action": "inject_sq_notes"})
    return SQFixResult(diagram=d, fixes_applied=fixes)