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

    def check_FunctionDef(self, node: ast.FunctionDef, filepath: str) -> list[Violation]:
        violations: list[Violation] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                if isinstance(child.value, ast.Tuple):
                    violations.append(Violation(
                        filepath, child.lineno, child.col_offset,
                        "SC005",
                        f"Function '{node.name}' returns a tuple; use Result[T]",
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

    def check_FunctionDef(self, node: ast.FunctionDef, filepath: str) -> list[Violation]:
        if node.name.startswith("__") and node.name.endswith("__"):
            return []
        if node.returns is None:
            return [Violation(
                filepath, node.lineno, node.col_offset,
                self.code,
                f"Function '{node.name}' missing return type annotation",
            )]
        return []

    check_AsyncFunctionDef = check_FunctionDef


class NoStarImportRule(Rule):
    """SC-025: No wildcard imports."""

    @property
    def code(self) -> str:
        return "SC025"

    @property
    def description(self) -> str:
        return "No wildcard imports"

    def check_ImportFrom(self, node: ast.ImportFrom, filepath: str) -> list[Violation]:
        for alias in node.names:
            if alias.name == "*":
                module = node.module or ""
                return [Violation(
                    filepath, node.lineno, node.col_offset,
                    self.code,
                    f"Wildcard import from '{module}' forbidden",
                )]
        return []


class InvalidResultSentinelRule(Rule):
    """SC-004: Module-level INVALID_RESULT sentinel."""

    @property
    def code(self) -> str:
        return "SC004"

    @property
    def description(self) -> str:
        return "Module-level INVALID_RESULT sentinel"

    def check_Module(self, node: ast.Module, filepath: str) -> list[Violation]:
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "INVALID_RESULT":
                        return []
        return [Violation(
            filepath, 1, 0,
            self.code,
            "Module lacks INVALID_RESULT sentinel",
        )]
