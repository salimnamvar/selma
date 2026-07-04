"""ERD fixer (header)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .ir import ERDDiagram
from .validator import validate_erd
from .rewriter import rewrite_erd
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


@dataclass
class ERDFixResult:
    diagram: ERDDiagram
    fixes_applied: list[dict] = field(default_factory=list)


def apply_erd_fixes(diagram: ERDDiagram, violations: list[Violation] | None = None) -> ERDFixResult:
    if violations is None:
        violations = validate_erd(diagram)
    fixes = []
    d = diagram
    if any(v.rule_id == "ERD-003" for v in violations):
        src = d.source
        if "@startuml" in src and "Source:" not in src[:1500]:
            header = "' Source: ...\n' Store: ...\n' Legend: ||--o{ 1:M \n\n"
            lines = src.splitlines(keepends=True)
            out = []
            ins = False
            for ln in lines:
                out.append(ln)
                if not ins and ln.strip().lower().startswith("@startuml"):
                    out.append(header)
                    ins = True
            d.source = "".join(out)
            fixes.append({"rule": "ERD-003", "action": "inject_erd_header"})
    return ERDFixResult(diagram=d, fixes_applied=fixes)