"""ERD layer linter package.

Canonical: tools/software-design/erd/
Bound to rules/software-design/erd.md
"""
from .parser import parse_erd_file
from .validator import validate_erd
from .fixer import apply_erd_fixes
from .rewriter import rewrite_erd
from .report import build_erd_report

__all__ = [
    "parse_erd_file",
    "validate_erd",
    "apply_erd_fixes",
    "rewrite_erd",
    "build_erd_report",
]
