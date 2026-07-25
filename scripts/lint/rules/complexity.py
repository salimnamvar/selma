"""SC-010: Function length limit (max 60 executable lines)."""
from __future__ import annotations

import ast

from scripts.lint.config import ComplexityConfig
from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

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

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> Result[list[Violation]]:
        """Check that function does not exceed maximum executable lines.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            lines: set[int] = set()
            for child in ast.walk(a_node):
                if isinstance(child, _EXECUTABLE_NODES) and hasattr(child, "lineno"):
                    lines.add(child.lineno)
            if len(lines) > self._max:
                violations = [Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    f"Function '{a_node.name}' has {len(lines)} executable lines (max {self._max})",
                )]
            result = Result.success(violations)
        return result

    check_AsyncFunctionDef = check_FunctionDef
