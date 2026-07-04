"""SM validator. Enforces rules from sm.md.

Core:
- SM-001: Filename sm_{scope}_lifecycle.puml
- SM-002: States are ALL_CAPS_UNDERSCORE (except [*])
- SM-003: Every transition has a guard or is explicit (basic reachability)
- SM-004: Header block present
"""
from __future__ import annotations

import re

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.puml import has_header_block
from .ir import SMDiagram
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


HEADER_MARKERS = ["Source:", "Purpose:"]


def validate_sm(d: SMDiagram) -> list[Violation]:
    violations: list[Violation] = []
    fn = d.filename
    stem = __import__("pathlib").Path(fn).stem

    if not stem.startswith("sm_") or "lifecycle" not in stem:
        violations.append(Violation(
            rule_id="SM-001",
            severity="medium",
            message="Filename should be sm_{scope}_lifecycle.puml",
            location=fn,
        ))

    for st in d.states:
        name = st.get("name", "")
        if name and not re.match(r"^[A-Z0-9_]+$", name) and name != "[*]":
            violations.append(Violation(
                rule_id="SM-002",
                severity="high",
                message=f"State name must be ALL_CAPS_UNDERSCORE: {name}",
                location=name,
                fix_suggestion="Uppercase with underscores per sm.md",
            ))

    if not has_header_block(d.source, HEADER_MARKERS):
        violations.append(Violation(
            rule_id="SM-004",
            severity="high",
            message="Missing required header comment block",
            location=fn,
        ))

    # Very basic: at least one transition present if states > 1
    if len(d.states) > 1 and len(d.transitions) == 0:
        violations.append(Violation(
            rule_id="SM-003",
            severity="medium",
            message="No transitions detected between multiple states",
            location=fn,
        ))

    return violations