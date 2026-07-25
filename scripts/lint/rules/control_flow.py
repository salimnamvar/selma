"""SC-001, SC-002: Exit door rules — single exit point and zero-raise policy."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

INVALID_RESULT = None


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _collect_exits(node: ast.AST) -> list[ast.AST]:
    exits: list[ast.AST] = []
    for child in ast.walk(node):
        if isinstance(child, (ast.Return, ast.Raise)):
            exits.append(child)
    return exits


class SingleExitRule(Rule):
    """SC-001: Every function must have exactly one exit point."""

    @property
    def code(self) -> str:
        return "SC001"

    @property
    def description(self) -> str:
        return "Single exit point per function"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that function has exactly one exit point."""
        violations: list[Violation] = []
        if not _is_dunder(a_node.name) and not a_node.name.startswith("_"):
            exits = _collect_exits(a_node)
            if len(exits) > 1:
                violations = [Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    f"Function '{a_node.name}' has {len(exits)} exit points (expected 1)",
                )]
        return violations

    check_AsyncFunctionDef = check_FunctionDef


class ZeroRaiseRule(Rule):
    """SC-002: No raise statements in non-dunder functions."""

    @property
    def code(self) -> str:
        return "SC002"

    @property
    def description(self) -> str:
        return "Zero raise statements in non-dunder functions"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that no raise statements exist in non-dunder functions."""
        violations: list[Violation] = []
        if not _is_dunder(a_node.name):
            for child in ast.walk(a_node):
                if isinstance(child, ast.Raise):
                    violations.append(Violation(
                        a_filepath, child.lineno, child.col_offset,
                        self.code,
                        f"Forbidden raise in function '{a_node.name}'",
                    ))
        return violations

    check_AsyncFunctionDef = check_FunctionDef
