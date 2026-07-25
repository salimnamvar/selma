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

    def _is_result_type(self, a_node: ast.expr | None) -> bool:
        if a_node is None:
            return False
        if isinstance(a_node, ast.Name) and a_node.id == "Result":
            return True
        if isinstance(a_node, ast.Subscript) and isinstance(a_node.value, ast.Name):
            return a_node.value.id == "Result"
        return False

    def _is_exempt(self, a_name: str) -> bool:
        if a_name.startswith("__") and a_name.endswith("__"):
            return True
        return False

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that functions do not return tuples and use Result[T]."""
        violations: list[Violation] = []
        for child in ast.walk(a_node):
            if isinstance(child, ast.Return) and child.value is not None:
                if isinstance(child.value, ast.Tuple):
                    violations.append(Violation(
                        a_filepath, child.lineno, child.col_offset,
                        "SC005",
                        f"Function '{a_node.name}' returns a tuple; use Result[T]",
                    ))
        if not self._is_exempt(a_node.name):
            if a_node.returns is None:
                has_return_value = any(
                    isinstance(c, ast.Return) and c.value is not None
                    for c in ast.walk(a_node)
                )
                if has_return_value:
                    violations.append(Violation(
                        a_filepath, a_node.lineno, a_node.col_offset,
                        self.code,
                        f"Function '{a_node.name}' missing return type annotation (must be Result[T])",
                    ))
            elif not self._is_result_type(a_node.returns):
                violations.append(Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    f"Function '{a_node.name}' return type is not Result[T]",
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
        if a_node.name.startswith("__") and a_node.name.endswith("__"):
            return violations
        for dec in a_node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == "abstractmethod":
                return violations
            if isinstance(dec, ast.Attribute) and dec.attr == "abstractmethod":
                return violations
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
    """SC-004: Module-level INVALID_RESULT sentinel (frozen, immutable — no SC-070 conflict)."""

    @property
    def code(self) -> str:
        return "SC004"

    @property
    def description(self) -> str:
        return "INVALID_RESULT module-level sentinel required"

    def check_Module(self, a_node: ast.Module, a_filepath: str) -> list[Violation]:
        """Verify the module defines INVALID_RESULT."""
        has_sentinel = False
        for stmt in a_node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "INVALID_RESULT":
                        has_sentinel = True
                        break
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if stmt.target.id == "INVALID_RESULT":
                    has_sentinel = True
                    break
            if has_sentinel:
                break

        if not has_sentinel:
            return [Violation(
                a_filepath, 1, 0,
                self.code,
                "Module missing required INVALID_RESULT sentinel",
            )]
        return []
