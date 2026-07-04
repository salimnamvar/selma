"""ERD validator per erd.md.

- ERD-001: Filename er_*.puml or er_overview.puml
- ERD-002: Only 1:M relationships (basic crow foot detection)
- ERD-003: Header block present (Source/Store/Legend per policy)
"""
from __future__ import annotations

import re

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.puml import has_header_block
from .ir import ERDDiagram
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


def validate_erd(d: ERDDiagram) -> list[Violation]:
    violations: list[Violation] = []
    fn = d.filename
    stem = __import__("pathlib").Path(fn).stem

    if not (stem.startswith("er_") or "overview" in stem):
        violations.append(Violation(rule_id="ERD-001", severity="medium",
            message="ERD files: er_{store}.puml or er_overview.puml", location=fn))

    # simplistic: look for forbidden non 1:M if we see 1--1 or similar patterns
    src = d.source.lower()
    if "1--1" in src or "|--||" in src or "0..1--0..1" in src:
        violations.append(Violation(rule_id="ERD-002", severity="critical",
            message="Non 1:M relationship detected. Only ||--o{ style 1:M allowed.",
            location=fn, fix_suggestion="Flatten or use proper crow's foot 1:M"))

    if not has_header_block(d.source, ["Source:", "Store:", "Legend"]):
        violations.append(Violation(rule_id="ERD-003", severity="high",
            message="Missing ERD header comment block (Source / Store / Legend)", location=fn))

    return violations