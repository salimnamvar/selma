"""SC-100, SC-101, SC-104: Security rules."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.config import SecurityConfig


class NoEvalExecRule(Rule):
    """SC-104: No eval() or exec() in production code."""

    @property
    def code(self) -> str:
        return "SC104"

    @property
    def description(self) -> str:
        return "No eval() or exec()"

    def check_Call(self, node: ast.Call, filepath: str) -> list[Violation]:
        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec", "compile"):
            return [Violation(
                filepath, node.lineno, node.col_offset,
                self.code,
                f"Forbidden call to '{node.func.id}()'",
            )]
        return []


class ParameterizedQueryRule(Rule):
    """SC-101: All database queries must use parameterized queries."""

    @property
    def code(self) -> str:
        return "SC101"

    @property
    def description(self) -> str:
        return "Parameterized queries (no SQL injection)"

    def check_Call(self, node: ast.Call, filepath: str) -> list[Violation]:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "execute":
            if node.args and isinstance(node.args[0], (ast.JoinedStr, ast.Call)):
                return [Violation(
                    filepath, node.lineno, node.col_offset,
                    self.code,
                    "Possible SQL injection: use parameterized queries",
                )]
        return []


class NoSecretsRule(Rule):
    """SC-100: No hardcoded secrets in source code."""

    def __init__(self, config: SecurityConfig | None = None) -> None:
        self._patterns = frozenset((config or SecurityConfig()).secret_patterns)

    @property
    def code(self) -> str:
        return "SC100"

    @property
    def description(self) -> str:
        return "No hardcoded secrets"

    def _check_name(self, name: str, node: ast.AST, filepath: str) -> list[Violation]:
        name_lower = name.lower()
        if any(p in name_lower for p in self._patterns):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            return [Violation(
                                filepath, node.lineno, node.col_offset,
                                self.code,
                                f"Possible hardcoded secret in '{name}'; use environment variable",
                            )]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
                if node.value and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    return [Violation(
                        filepath, node.lineno, node.col_offset,
                        self.code,
                        f"Possible hardcoded secret in '{name}'; use environment variable",
                    )]
        return []

    def check_Assign(self, node: ast.Assign, filepath: str) -> list[Violation]:
        for target in node.targets:
            if isinstance(target, ast.Name):
                result = self._check_name(target.id, node, filepath)
                if result:
                    return result
        return []

    def check_AnnAssign(self, node: ast.AnnAssign, filepath: str) -> list[Violation]:
        if isinstance(node.target, ast.Name):
            return self._check_name(node.target.id, node, filepath)
        return []
