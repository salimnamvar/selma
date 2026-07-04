"""CL report builder."""
from __future__ import annotations

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import LayerReport, Violation, build_layer_report
from .ir import CLDiagram


def build_cl_report(diagram: CLDiagram, violations: list[Violation]) -> LayerReport:
    return build_layer_report(diagram.filename, "cl", violations)