"""SC-007, SC-113: Assert validation — no assert for input validation."""
from __future__ import annotations

import ast

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


class AssertValidationRule(Rule):
    """SC-007/113: assert shall not be used for input validation."""

    @property
    def code(self) -> str:
        return "SC007"

    @property
    def description(self) -> str:
        return "No assert for input validation"

    def _find_enclosing_function(self, a_node: ast.Assert) -> Result[ast.FunctionDef | None]:
        """Find the nearest enclosing function definition for an assert node.

        Precondition: a_node is an Assert AST node.
        Postcondition: Returns Ok with the enclosing FunctionDef or Ok(None) if not found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_result: ast.FunctionDef | None = None
        for parent in ast.walk(a_node):
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(parent):
                    if child is a_node:
                        b_result = parent
                        break
                if b_result is not None:
                    break
        return Result.success(b_result)

    def _is_invariant_assert(self, a_node: ast.Assert, a_func: ast.FunctionDef) -> Result[bool]:
        """Check whether an assert is checking an internal invariant rather than validating input.

        Precondition: a_node is an Assert AST node; a_func is its enclosing FunctionDef.
        Postcondition: Returns Ok(True) if the assert references only locally assigned names, Ok(False) otherwise.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_result: bool = False
        param_names = {arg.arg for arg in a_func.args.args + a_func.args.posonlyargs + a_func.args.kwonlyargs}
        assigned_names: set[str] = set()
        for stmt in a_func.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        assigned_names.add(target.id)
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                assigned_names.add(stmt.target.id)

        test = a_node.test
        ref_names: set[str] = set()
        for node in ast.walk(test):
            if isinstance(node, ast.Name):
                ref_names.add(node.id)

        if ref_names and not (ref_names & param_names) and (ref_names & assigned_names):
            b_result = True
        return Result.success(b_result)

    def check_Assert(self, a_node: ast.Assert, a_filepath: str) -> Result[list[Violation]]:
        """Check that assert is not used for input validation.

        Precondition: a_node is an Assert AST node; a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC007 violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        violations: list[Violation] = []
        b_invariant = False
        func_result = self._find_enclosing_function(a_node)
        if func_result.is_success() and func_result.value is not None:
            inv_result = self._is_invariant_assert(a_node, func_result.value)
            if inv_result.is_success() and inv_result.value:
                b_invariant = True
        if not b_invariant:
            violations.append(Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                self.code,
                "assert forbidden for validation; use explicit checks with Result return",
            ))
        return Result.success(violations)
