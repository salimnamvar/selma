"""ODCS fixer (header + basic normalization)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .ir import ODCSDoc
from .validator import validate_odcs
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


@dataclass
class ODCSFixResult:
    doc: ODCSDoc
    fixes_applied: list[dict] = field(default_factory=list)


def apply_odcs_fixes(doc: ODCSDoc, violations: list[Violation] | None = None) -> ODCSFixResult:
    if violations is None:
        violations = validate_odcs(doc)
    fixes = []
    d = doc
    src = d.source
    if any(v.rule_id == "ODCS-001" for v in violations):
        if not src.startswith("# yaml-language-server"):
            hdr = '# yaml-language-server: $schema=https://raw.githubusercontent.com/bitol-io/open-data-contract-standard/main/schema/odcs-json-schema-latest.json\n'
            d.source = hdr + src
            fixes.append({"rule": "ODCS-001", "action": "add_schema_header"})
    return ODCSFixResult(doc=d, fixes_applied=fixes)