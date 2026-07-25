"""SC-001, SC-002: Exit door rules — single exit point and zero-raise policy."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation



_SC002_EXEMPT_DUNDERS = frozenset({
    "__init__", "__enter__", "__exit__", "__iter__", "__next__",
    "__getitem__", "__len__", "__bool__", "__eq__", "__lt__",
    "__str__", "__repr__", "__aenter__", "__aexit__", "__aiter__", "__anext__",
})


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _collect_returns(node: ast.AST) -> list[ast.Return]:
    """Collect all Return nodes within a function body, excluding nested functions."""
    returns: list[ast.Return] = []
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child is not node:
                continue
        if isinstance(child, ast.Return):
            returns.append(child)
    return returns


class SingleExitRule(Rule):
    """SC-001: Every function must have exactly one exit point."""

    @property
    def code(self) -> str:
        return "SC001"

    @property
    def description(self) -> str:
        return "Single exit point per function"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that function has exactly one return statement."""
        violations: list[Violation] = []
        if not _is_dunder(a_node.name):
            returns = _collect_returns(a_node)
            if len(returns) > 1:
                violations = [Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    f"Function '{a_node.name}' has {len(returns)} return statements (expected 1)",
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

    def _is_framework_boundary_adapter(self, a_node: ast.FunctionDef) -> bool:
        name_lower = a_node.name.lower()
        has_exception_keyword = "exception" in name_lower or "error" in name_lower or "http" in name_lower
        if not has_exception_keyword:
            return False
        for child in ast.walk(a_node):
            if isinstance(child, ast.Raise):
                return True
        return False

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that no raise statements exist in non-dunder functions."""
        violations: list[Violation] = []
        if a_node.name in _SC002_EXEMPT_DUNDERS:
            return violations
        if self._is_framework_boundary_adapter(a_node):
            return violations
        for child in ast.walk(a_node):
            if isinstance(child, ast.Raise):
                violations.append(Violation(
                    a_filepath, child.lineno, child.col_offset,
                    self.code,
                    f"Forbidden raise in function '{a_node.name}'",
                ))
        return violations

    check_AsyncFunctionDef = check_FunctionDef
