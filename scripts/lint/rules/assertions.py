"""SC-007, SC-113: Assert validation — no assert for input validation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

if TYPE_CHECKING:
    from scripts.lint.core.visitor import VisitorContext


class AssertValidationRule(Rule):
    """SC-007/113: assert shall not be used for input validation."""

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
            b_result = "SC007"
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
            b_result = "No assert for input validation"
        return b_result

    def _find_enclosing_function(
        self, a_node: ast.Assert
    ) -> Result[ast.FunctionDef | None]:
        """Find the nearest enclosing function definition for an assert node.

        Precondition: a_node is an Assert AST node.
        Postcondition: Returns Ok with the enclosing FunctionDef
            or Ok(None) if not found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: ast.FunctionDef | None = None
        if b_continue:
            for parent in ast.walk(a_node):
                if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for child in ast.walk(parent):
                        if child is a_node:
                            b_result = parent
                            break
                    if b_result is not None:
                        break
        return Result.success(b_result)

    @staticmethod
    def _collect_param_names(a_func: ast.FunctionDef) -> set[str]:
        """Collect all parameter names from a function definition.

        Precondition: a_func is a FunctionDef AST node.
        Postcondition: Returns set of parameter name strings.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: set[str] = set()
        if b_continue:
            b_result = {
                arg.arg
                for arg in a_func.args.args
                + a_func.args.posonlyargs
                + a_func.args.kwonlyargs
            }
        return b_result

    @staticmethod
    def _collect_assigned_names(a_func: ast.FunctionDef) -> set[str]:
        """Collect all locally assigned names from a function body.

        Precondition: a_func is a FunctionDef AST node.
        Postcondition: Returns set of assigned name strings.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: set[str] = set()
        if b_continue:
            for stmt in a_func.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            b_result.add(target.id)
                elif isinstance(stmt, ast.AnnAssign) and isinstance(
                    stmt.target, ast.Name
                ):
                    b_result.add(stmt.target.id)
        return b_result

    @staticmethod
    def _collect_ref_names(a_test: ast.expr) -> set[str]:
        """Collect all referenced names from an expression subtree.

        Precondition: a_test is an AST expression node.
        Postcondition: Returns set of referenced name strings.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: set[str] = set()
        if b_continue:
            for node in ast.walk(a_test):
                if isinstance(node, ast.Name):
                    b_result.add(node.id)
        return b_result

    def _is_invariant_assert(
        self, a_node: ast.Assert, a_func: ast.FunctionDef
    ) -> Result[bool]:
        """Check whether an assert is checking an internal invariant.

        Rather than validating input.

        Precondition: a_node is an Assert AST node; a_func is its
            enclosing FunctionDef.
        Postcondition: Returns Ok(True) if the assert references only
            locally assigned names, Ok(False) otherwise.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: bool = False
        if b_continue:
            param_names = self._collect_param_names(a_func)
            assigned_names = self._collect_assigned_names(a_func)
            ref_names = self._collect_ref_names(a_node.test)
            b_result = (
                bool(ref_names)
                and not bool(ref_names & param_names)
                and bool(ref_names & assigned_names)
            )
        return Result.success(b_result)

    def check_assert(
        self,
        a_node: ast.Assert,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that assert is not used for input validation.

        Precondition: a_node is an Assert AST node; a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC007 violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        b_invariant = False
        if b_continue:
            func_result = self._find_enclosing_function(a_node)
            if func_result.is_success().value and func_result.value is not None:
                inv_result = self._is_invariant_assert(a_node, func_result.value)
                if inv_result.is_success().value and inv_result.value:
                    b_invariant = True
        if b_continue and not b_invariant:
            violations.append(
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    self.code,
                    "assert forbidden for validation;"
                    " use explicit checks with Result return",
                )
            )
        return Result.success(violations)
