"""CL validator per cl.md .

- CL-001: Filename cl_*.puml
- CL-002: Attributes snake_case (basic scan)
- CL-003: No manager/adapter/api classes (infrastructure) — domain diagrams only
- CL-004: Header with Source and Purpose — domain diagrams only
- CL-005: Runtime diagrams must declare @cl-type runtime
"""
from __future__ import annotations

import re

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.puml import has_header_block
from .ir import CLDiagram
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


def validate_cl(d: CLDiagram) -> list[Violation]:
    violations: list[Violation] = []
    fn = d.filename
    stem = __import__("pathlib").Path(fn).stem
    is_runtime = d.cl_type == "runtime"

    if not stem.startswith("cl_"):
        violations.append(Violation(rule_id="CL-001", severity="medium",
            message="Class diagrams: cl_{scope}.puml", location=fn))

    # CL-003: No infrastructure classes in domain diagrams
    # Runtime diagrams are exempt — they intentionally show infrastructure classes.
    if not is_runtime:
        bad_names = [c for c in d.classes if any(x in c.lower() for x in ("manager", "adapter", "api", "controller"))]
        for bn in bad_names:
            violations.append(Violation(rule_id="CL-003", severity="critical",
                message=f"Infrastructure class not allowed in CL domain diagram: {bn}", location=bn,
                fix_suggestion="Move to implementation or change to @cl-type runtime"))

    # crude snake check on attributes (look for camel in class bodies rough)
    if re.search(r'\n\s+[a-z]+[A-Z][a-zA-Z]*\s*:', d.source):
        violations.append(Violation(rule_id="CL-002", severity="high",
            message="Attributes must be snake_case", location=fn))

    # CL-004: Header required for domain diagrams (runtime diagrams have relaxed expectations)
    if not is_runtime and not has_header_block(d.source, ["Source:", "Purpose:"]):
        violations.append(Violation(rule_id="CL-004", severity="high",
            message="Missing header block (Source: and Purpose: required)", location=fn))

    # CL-005: Runtime diagrams must declare @cl-type runtime
    if is_runtime and not re.search(r"'?\s*@cl-type\s+runtime", d.source, re.IGNORECASE):
        violations.append(Violation(rule_id="CL-005", severity="medium",
            message="Runtime diagram must declare @cl-type runtime in file header", location=fn,
            fix_suggestion="Add '@cl-type runtime' on line 2 after @startuml"))

    return violations