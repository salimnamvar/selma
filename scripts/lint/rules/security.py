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

    def check_Call(self, a_node: ast.Call, a_filepath: str) -> list[Violation]:
        """Check that eval/exec/compile are not called."""
        violations: list[Violation] = []
        if isinstance(a_node.func, ast.Name) and a_node.func.id in ("eval", "exec", "compile"):
            violations = [Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                self.code,
                f"Forbidden call to '{a_node.func.id}()'",
            )]
        return violations


class ParameterizedQueryRule(Rule):
    """SC-101: All database queries must use parameterized queries."""

    @property
    def code(self) -> str:
        return "SC101"

    @property
    def description(self) -> str:
        return "Parameterized queries (no SQL injection)"

    def check_Call(self, a_node: ast.Call, a_filepath: str) -> list[Violation]:
        """Check that .execute() uses parameterized queries."""
        violations: list[Violation] = []
        if isinstance(a_node.func, ast.Attribute) and a_node.func.attr == "execute":
            if a_node.args and isinstance(a_node.args[0], (ast.JoinedStr, ast.Call)):
                violations = [Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    "Possible SQL injection: use parameterized queries",
                )]
            elif a_node.args and isinstance(a_node.args[0], ast.BinOp):
                if isinstance(a_node.args[0].op, ast.Mod):
                    violations = [Violation(
                        a_filepath, a_node.lineno, a_node.col_offset,
                        self.code,
                        "Possible SQL injection: use parameterized queries",
                    )]
            elif a_node.args and isinstance(a_node.args[0], ast.Call):
                if isinstance(a_node.args[0].func, ast.Attribute) and a_node.args[0].func.attr == "format":
                    violations = [Violation(
                        a_filepath, a_node.lineno, a_node.col_offset,
                        self.code,
                        "Possible SQL injection: use parameterized queries",
                    )]
        return violations


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

    def _check_name(self, a_name: str, node: ast.AST, a_filepath: str) -> list[Violation]:
        name_lower = a_name.lower()
        if any(p in name_lower for p in self._patterns):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == a_name:
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            return [Violation(
                                a_filepath, node.lineno, node.col_offset,
                                self.code,
                                f"Possible hardcoded secret in '{a_name}'; use environment variable",
                            )]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == a_name:
                if node.value and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    return [Violation(
                        a_filepath, node.lineno, node.col_offset,
                        self.code,
                        f"Possible hardcoded secret in '{a_name}'; use environment variable",
                    )]
        return []

    def check_Assign(self, a_node: ast.Assign, a_filepath: str) -> list[Violation]:
        """Check assignments for hardcoded secrets."""
        violations: list[Violation] = []
        for target in a_node.targets:
            if isinstance(target, ast.Name):
                result = self._check_name(target.id, a_node, a_filepath)
                if result:
                    violations = result
                    break
        return violations

    def check_AnnAssign(self, a_node: ast.AnnAssign, a_filepath: str) -> list[Violation]:
        """Check annotated assignments for hardcoded secrets."""
        violations: list[Violation] = []
        if isinstance(a_node.target, ast.Name):
            violations = self._check_name(a_node.target.id, a_node, a_filepath)
        return violations
