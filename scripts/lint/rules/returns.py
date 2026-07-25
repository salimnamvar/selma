"""SC-003, SC-004, SC-005, SC-024, SC-025: Return type and result rules."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation



class ResultReturnRule(Rule):
    """SC-003/005: Functions must return Result[T], not tuples."""

    @property
    def code(self) -> str:
        return "SC003"

    @property
    def description(self) -> str:
        return "Result[T] returns, no tuples"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that functions do not return tuples."""
        violations: list[Violation] = []
        for child in ast.walk(a_node):
            if isinstance(child, ast.Return) and child.value is not None:
                if isinstance(child.value, ast.Tuple):
                    violations.append(Violation(
                        a_filepath, child.lineno, child.col_offset,
                        "SC005",
                        f"Function '{a_node.name}' returns a tuple; use Result[T]",
                    ))
        return violations

    check_AsyncFunctionDef = check_FunctionDef


class ExplicitReturnTypeRule(Rule):
    """SC-024: Every function must have an explicit return type annotation."""

    @property
    def code(self) -> str:
        return "SC024"

    @property
    def description(self) -> str:
        return "Explicit return type annotation"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that functions have explicit return type annotations."""
        violations: list[Violation] = []
        if not (a_node.name.startswith("__") and a_node.name.endswith("__")):
            if a_node.returns is None:
                violations = [Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    f"Function '{a_node.name}' missing return type annotation",
                )]
        return violations

    check_AsyncFunctionDef = check_FunctionDef


class NoStarImportRule(Rule):
    """SC-025: No wildcard imports."""

    @property
    def code(self) -> str:
        return "SC025"

    @property
    def description(self) -> str:
        return "No wildcard imports"

    def check_ImportFrom(self, a_node: ast.ImportFrom, a_filepath: str) -> list[Violation]:
        """Check that no wildcard imports are used."""
        violations: list[Violation] = []
        for alias in a_node.names:
            if alias.name == "*":
                module = a_node.module or ""
                violations = [Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    f"Wildcard import from '{module}' forbidden",
                )]
                break
        return violations


class InvalidResultSentinelRule(Rule):
    """SC-004: Module-level INVALID_RESULT sentinel — DISABLED, conflicts with SC-070."""

    @property
    def code(self) -> str:
        return "SC004"

    @property
    def description(self) -> str:
        return "DISABLED: conflicts with no-module-level-state rule"

    def check_Module(self, a_node: ast.Module, a_filepath: str) -> list[Violation]:
        """Disabled: conflicts with no-module-level-state rule."""
        return []
