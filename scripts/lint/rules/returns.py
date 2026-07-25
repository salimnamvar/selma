"""SC-003, SC-004, SC-005, SC-024, SC-025: Return type and result rules."""
from __future__ import annotations

import ast

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


class ResultReturnRule(Rule):
    """SC-003/005: Functions returning values must use Result[T], no tuple returns."""

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

    def _is_none_annotation(self, a_node: ast.expr | None) -> bool:
        if a_node is None:
            return True
        if isinstance(a_node, ast.Constant) and a_node.value is None:
            return True
        if isinstance(a_node, ast.Name) and a_node.id == "None":
            return True
        return False

    def _has_return_value(self, a_node: ast.FunctionDef) -> bool:
        for child in ast.walk(a_node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child is not a_node:
                    continue
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False

    def _is_exempt(self, a_name: str) -> bool:
        if a_name.startswith("__") and a_name.endswith("__"):
            return True
        return False

    def _is_property_or_abstract(self, a_node: ast.FunctionDef) -> bool:
        for dec in a_node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id in ("property", "staticmethod", "classmethod"):
                return True
            if isinstance(dec, ast.Attribute) and dec.attr in ("setter", "getter", "deleter", "abstractmethod"):
                return True
            if isinstance(dec, ast.Name) and dec.id == "abstractmethod":
                return True
        return False

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> Result[list[Violation]]:
        """Check that functions do not return tuples and use Result[T]."""
        violations: list[Violation] = []
        for child in ast.walk(a_node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child is not a_node:
                    continue
            if isinstance(child, ast.Return) and child.value is not None:
                if isinstance(child.value, ast.Tuple):
                    violations.append(Violation(
                        a_filepath, child.lineno, child.col_offset,
                        "SC005",
                        f"Function '{a_node.name}' returns a tuple; use Result[T]",
                    ))
        if self._is_exempt(a_node.name) or self._is_property_or_abstract(a_node):
            return Result.success(violations)
        has_return_value = self._has_return_value(a_node)
        if self._is_none_annotation(a_node.returns):
            pass
        elif self._is_result_type(a_node.returns):
            pass
        elif a_node.returns is not None and has_return_value:
            violations.append(Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                self.code,
                f"Function '{a_node.name}' returns values but type is not Result[T]",
            ))
        elif a_node.returns is None and has_return_value:
            violations.append(Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                self.code,
                f"Function '{a_node.name}' missing return type (must be Result[T])",
            ))
        return Result.success(violations)

    check_AsyncFunctionDef = check_FunctionDef


class ExplicitReturnTypeRule(Rule):
    """SC-024: Every function must have an explicit return type annotation."""

    @property
    def code(self) -> str:
        return "SC024"

    @property
    def description(self) -> str:
        return "Explicit return type annotation"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> Result[list[Violation]]:
        """Check that functions have explicit return type annotations."""
        violations: list[Violation] = []
        if a_node.name.startswith("__") and a_node.name.endswith("__"):
            return Result.success(violations)
        for dec in a_node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == "abstractmethod":
                return Result.success(violations)
            if isinstance(dec, ast.Attribute) and dec.attr == "abstractmethod":
                return Result.success(violations)
        if a_node.returns is None:
            violations = [Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                self.code,
                f"Function '{a_node.name}' missing return type annotation",
            )]
        return Result.success(violations)

    check_AsyncFunctionDef = check_FunctionDef


class NoStarImportRule(Rule):
    """SC-025: No wildcard imports."""

    @property
    def code(self) -> str:
        return "SC025"

    @property
    def description(self) -> str:
        return "No wildcard imports"

    def check_ImportFrom(self, a_node: ast.ImportFrom, a_filepath: str) -> Result[list[Violation]]:
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
        return Result.success(violations)


class InvalidResultSentinelRule(Rule):
    """SC-004: Module-level INVALID_RESULT sentinel required when module has Result[T] functions."""

    @property
    def code(self) -> str:
        return "SC004"

    @property
    def description(self) -> str:
        return "INVALID_RESULT module-level sentinel required"

    def _is_result_type(self, a_node: ast.expr | None) -> bool:
        if a_node is None:
            return False
        if isinstance(a_node, ast.Name) and a_node.id == "Result":
            return True
        if isinstance(a_node, ast.Subscript) and isinstance(a_node.value, ast.Name):
            return a_node.value.id == "Result"
        return False

    def _has_result_functions(self, a_node: ast.Module) -> bool:
        for stmt in ast.walk(a_node):
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._is_result_type(stmt.returns):
                    return True
        return False

    def _has_sentinel(self, a_node: ast.Module) -> bool:
        for stmt in a_node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "INVALID_RESULT":
                        return True
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if stmt.target.id == "INVALID_RESULT":
                    return True
            elif isinstance(stmt, ast.ImportFrom):
                for alias in stmt.names:
                    if alias.name == "INVALID_RESULT":
                        return True
        return False

    def check_Module(self, a_node: ast.Module, a_filepath: str) -> Result[list[Violation]]:
        """Verify INVALID_RESULT exists if module has Result[T] functions."""
        if not self._has_result_functions(a_node):
            return Result.success([])
        if self._has_sentinel(a_node):
            return Result.success([])
        return Result.success([Violation(
            a_filepath, 1, 0,
            self.code,
            "Module has Result[T] functions but missing INVALID_RESULT sentinel",
        )])
