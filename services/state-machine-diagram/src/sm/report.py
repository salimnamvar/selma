"""SM report builder."""
from __future__ import annotations

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import LayerReport, Violation, build_layer_report
from .ir import SMDiagram


def build_sm_report(diagram: SMDiagram, violations: list[Violation]) -> LayerReport:
    return build_layer_report(diagram.filename, "sm", violations)