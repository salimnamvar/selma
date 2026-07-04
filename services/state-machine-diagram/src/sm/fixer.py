"""SM fixer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ir import SMDiagram
from .validator import validate_sm
from .rewriter import rewrite_sm
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


@dataclass
class SMFixResult:
    diagram: SMDiagram
    fixes_applied: list[dict] = field(default_factory=list)


def apply_sm_fixes(diagram: SMDiagram, violations: list[Violation] | None = None) -> SMFixResult:
    if violations is None:
        violations = validate_sm(diagram)

    fixes: list[dict] = []
    d = diagram

    if any(v.rule_id == "SM-004" for v in violations):
        src = d.source
        if "@startuml" in src and "Source:" not in src[:1500]:
            header = (
                "' === HEADER ========================================\n"
                "' Source:    sm_{scope}_lifecycle.puml\n"
                "' Purpose:   Lifecycle for entity\n"
                "' Milestone: Phase 1\n"
                "' ===================================================\n\n"
            )
            lines = src.splitlines(keepends=True)
            out = []
            inserted = False
            for ln in lines:
                out.append(ln)
                if not inserted and ln.strip().lower().startswith("@startuml"):
                    out.append(header)
                    inserted = True
            d.source = "".join(out)
            fixes.append({"rule": "SM-004", "action": "inject_header"})

    return SMFixResult(diagram=d, fixes_applied=fixes)