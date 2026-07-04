from __future__ import annotations
from dataclasses import dataclass, field
from .ir import OASDoc
from .validator import validate_oas
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


@dataclass
class OASFixResult:
    doc: OASDoc
    fixes_applied: list[dict] = field(default_factory=list)


def apply_oas_fixes(doc: OASDoc, violations=None) -> OASFixResult:
    if violations is None:
        violations = validate_oas(doc)
    fixes = []
    d = doc
    # example: ensure openapi key at top if missing simple
    if any(v.rule_id == "OAS-001" for v in violations) and "openapi:" not in d.source[:200]:
        d.source = 'openapi: "3.1.0"\n' + d.source
        fixes.append({"rule": "OAS-001", "action": "add_openapi_version"})
    return OASFixResult(doc=d, fixes_applied=fixes)