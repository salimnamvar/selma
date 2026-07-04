"""Report builder for RoD-CSR-SQ analysis."""
from __future__ import annotations

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import LayerReport, Violation, build_layer_report

from .ir import RodCsrSqDiagram


def build_rod_csr_sq_report(diagram: RodCsrSqDiagram, violations: list[Violation]) -> LayerReport:
    """Build a report for RoD-CSR-SQ analysis."""
    return build_layer_report(diagram.filename, "rod_csr_sq", violations)
