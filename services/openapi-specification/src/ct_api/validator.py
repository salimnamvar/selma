"""OpenAPI / ROD linter rules from openapi.md + rod.md + cicd."""
from __future__ import annotations
import re
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation
from .ir import OASDoc


def validate_oas(d: OASDoc) -> list[Violation]:
    vs: list[Violation] = []
    fn = d.filename
    src = d.source[:2000]

    if "openapi:" not in src:
        vs.append(Violation(rule_id="OAS-001", severity="critical",
            message="Missing openapi: version field", location=fn))

    # UC ID in summary pattern recommended
    # We do a light scan for operation summaries
    if d.data and isinstance(d.data, dict):
        for pth, methods in (d.data.get("paths") or {}).items():
            if not isinstance(methods, dict):
                continue
            for m, op in methods.items():
                if not isinstance(op, dict):
                    continue
                summ = op.get("summary", "")
                if not re.search(r"[A-Z]{2,5}-\d{2,}", str(summ)):
                    vs.append(Violation(rule_id="OAS-002", severity="high",
                        message=f"Operation summary should contain UC-ID: {m} {pth}",
                        location=f"{pth}:{m}"))

    # info.version etc basic
    if d.data:
        info = d.data.get("info") or {}
        if not info.get("version"):
            vs.append(Violation(rule_id="OAS-003", severity="medium", message="info.version required", location=fn))

    return vs