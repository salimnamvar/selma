"""SC-010: Function length limit (max 60 executable lines)."""

from __future__ import annotations

import ast

from scripts.lint.config import ComplexityConfig
from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

_EXECUTABLE_NODES = (
    ast.Assign,
    ast.AugAssign,
    ast.AnnAssign,
    ast.Expr,
    ast.If,
    ast.For,
    ast.While,
    ast.With,
    ast.Try,
    ast.Raise,
    ast.Assert,
    ast.Delete,
    ast.Pass,
    ast.Break,
    ast.Continue,
    ast.Await,
    ast.Yield,
    ast.YieldFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
)


class FunctionLengthRule(Rule):
    """SC-010: Max N executable lines per function (configurable)."""

    def __init__(self, config: ComplexityConfig | None = None) -> None:
        self._max = (config or ComplexityConfig()).max_lines

    @property
    def code(self) -> str:
        """Short rule identifier, e.g. 'SC001'.

        Precondition: None.
        Postcondition: Returns the rule code string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = "SC010"
        return b_result

    @property
    def description(self) -> str:
        """One-line human description.

        Precondition: None.
        Postcondition: Returns the rule description string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = f"Function length <= {self._max} lines"
        return b_result

    def check_function_def(
        self, a_node: ast.FunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
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
                violations = [
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        self.code,
                        f"Function '{a_node.name}' has {len(lines)}"
                        f" executable lines (max {self._max})",
                    )
                ]
            result = Result.success(violations)
        return result

    def check_async_function_def(
        self, a_node: ast.AsyncFunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that async function does not exceed maximum executable lines.

        Precondition: a_node is an AsyncFunctionDef AST node.
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
                violations = [
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        self.code,
                        f"Function '{a_node.name}' has {len(lines)}"
                        f" executable lines (max {self._max})",
                    )
                ]
            result = Result.success(violations)
        return result
