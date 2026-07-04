"""C4 Auto-Linter + Auto-Fixer.

Parses PlantUML C4 diagrams, validates against deterministic rules,
auto-fixes, and rewrites corrected PlantUML.

This is the canonical implementation, bound to the C4 rules in
rules/software-design/c4.md and orchestrated via skills/software-design.
"""
from .ir import C4Diagram, Node, Edge, Boundary, Violation
from .parser import parse_file, parse_text
from .validator import validate
from .fixer import apply_fixes
from .rewriter import rewrite_diagram

__all__ = [
    "C4Diagram",
    "Node",
    "Edge",
    "Boundary",
    "Violation",
    "parse_file",
    "parse_text",
    "validate",
    "apply_fixes",
    "rewrite_diagram",
]
