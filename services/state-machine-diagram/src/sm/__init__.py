"""SM layer linter package.

Canonical: tools/software-design/sm/
Bound to rules/software-design/sm.md
"""
from .parser import parse_sm_file
from .validator import validate_sm
from .fixer import apply_sm_fixes
from .rewriter import rewrite_sm
from .report import build_sm_report

__all__ = [
    "parse_sm_file",
    "validate_sm",
    "apply_sm_fixes",
    "rewrite_sm",
    "build_sm_report",
]
