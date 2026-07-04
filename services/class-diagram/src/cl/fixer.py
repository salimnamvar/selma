"""CL fixer."""
from __future__ import annotations

from dataclasses import dataclass, field

from .ir import CLDiagram
from .validator import validate_cl
from .rewriter import rewrite_cl
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


@dataclass
class CLFixResult:
    diagram: CLDiagram
    fixes_applied: list[dict] = field(default_factory=list)


def apply_cl_fixes(diagram: CLDiagram, violations: list[Violation] | None = None) -> CLFixResult:
    if violations is None:
        violations = validate_cl(diagram)
    fixes = []
    d = diagram
    if any(v.rule_id == "CL-004" for v in violations):
        src = d.source
        if "@startuml" in src and "Source:" not in src[:1200]:
            header = "' Source: cl_xxx.puml\n' Purpose: Domain model\n\n"
            lines = src.splitlines(keepends=True)
            out = []
            ins = False
            for ln in lines:
                out.append(ln)
                if not ins and ln.strip().lower().startswith("@startuml"):
                    out.append(header)
                    ins = True
            d.source = "".join(out)
            fixes.append({"rule": "CL-004", "action": "inject_header"})
    return CLFixResult(diagram=d, fixes_applied=fixes)