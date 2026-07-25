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

    def check_FunctionDef(self, node: ast.FunctionDef, filepath: str) -> list[Violation]:
        lines: set[int] = set()
        for child in ast.walk(node):
            if isinstance(child, _EXECUTABLE_NODES) and hasattr(child, "lineno"):
                lines.add(child.lineno)
        if len(lines) > self._max:
            return [Violation(
                filepath, node.lineno, node.col_offset,
                self.code,
                f"Function '{node.name}' has {len(lines)} executable lines (max {self._max})",
            )]
        return []

    check_AsyncFunctionDef = check_FunctionDef
