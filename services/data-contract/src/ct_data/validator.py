"""ODCS validator (odcs.md + schema rules)."""
from __future__ import annotations

import re

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation
from .ir import ODCSDoc


REQUIRED_TOP = ["version", "apiVersion", "kind", "id", "name", "status", "schema"]

ALLOWED_STATUS = {"draft", "active", "proposed", "retired"}


def validate_odcs(d: ODCSDoc) -> list[Violation]:
    violations: list[Violation] = []
    fn = d.filename
    src = d.source

    # Header schema comment
    if "# yaml-language-server: $schema=" not in src.splitlines()[0] + "\n" + src[:300]:
        if "odcs-json-schema" not in src[:400]:
            violations.append(Violation(
                rule_id="ODCS-001", severity="high",
                message="Missing yaml-language-server schema header comment for ODCS",
                location=fn,
                fix_suggestion="Add # yaml-language-server: $schema=...odcs... at top"
            ))

    # Required keys
    for k in REQUIRED_TOP:
        if k not in d.top_keys and (not d.data or k not in (d.data or {})):
            violations.append(Violation(
                rule_id="ODCS-002", severity="critical",
                message=f"Missing required top-level key: {k}",
                location=fn
            ))

    # status value
    if d.data and isinstance(d.data, dict):
        st = str(d.data.get("status", "")).lower()
        if st and st not in ALLOWED_STATUS:
            violations.append(Violation(rule_id="ODCS-003", severity="critical",
                message=f"Invalid status '{st}'", location=fn))

    # servers array rule (from odcs.md)
    if d.data and "servers" in d.data:
        sv = d.data.get("servers")
        if not isinstance(sv, list):
            violations.append(Violation(rule_id="ODCS-004", severity="high",
                message="servers must be array, not map", location=fn))

    # schema present and list
    if d.data and "schema" in d.data and not isinstance(d.data.get("schema"), list):
        violations.append(Violation(rule_id="ODCS-005", severity="medium",
            message="schema should be array of structures", location=fn))

    return violations