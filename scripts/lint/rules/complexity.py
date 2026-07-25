"""SC-010: Function length limit (max 60 executable lines)."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.config import ComplexityConfig


_EXECUTABLE_NODES = (
    ast.Assign, ast.AugAssign, ast.AnnAssign,
    ast.Expr, ast.If, ast.For, ast.While, ast.With, ast.Try,
    ast.Raise, ast.Assert, ast.Delete, ast.Pass, ast.Break, ast.Continue,
    ast.Await, ast.Yield, ast.YieldFrom,
    ast.FunctionDef, ast.AsyncFunctionDef,
)


class FunctionLengthRule(Rule):
    """SC-010: Max N executable lines per function (configurable)."""

    def __init__(self, config: ComplexityConfig | None = None) -> None:
        self._max = (config or ComplexityConfig()).max_lines

    @property
    def code(self) -> str:
        return "SC010"

    @property
    def description(self) -> str:
        return f"Function length <= {self._max} lines"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that function does not exceed maximum executable lines."""
        lines: set[int] = set()
        for child in ast.walk(a_node):
            if isinstance(child, _EXECUTABLE_NODES) and hasattr(child, "lineno"):
                lines.add(child.lineno)
        violations: list[Violation] = []
        if len(lines) > self._max:
            violations = [Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                self.code,
                f"Function '{a_node.name}' has {len(lines)} executable lines (max {self._max})",
            )]
        return violations

    check_AsyncFunctionDef = check_FunctionDef
