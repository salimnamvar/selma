"""SQ layer linter package.

Canonical: tools/software-design/sq/
Bound to rules/software-design/sq.md
"""
from .parser import parse_sq_file
from .validator import validate_sq
from .fixer import apply_sq_fixes
from .rewriter import rewrite_sq
from .report import build_sq_report

__all__ = [
    "parse_sq_file",
    "validate_sq",
    "apply_sq_fixes",
    "rewrite_sq",
    "build_sq_report",
]
