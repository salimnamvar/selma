"""SC-007, SC-113: Assert validation — no assert for input validation."""
from __future__ import annotations

import ast

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

    def _find_enclosing_function(self, a_node: ast.Assert) -> ast.FunctionDef | None:
        for parent in ast.walk(a_node):
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(parent):
                    if child is a_node:
                        return parent
        return None

    def _is_invariant_assert(self, a_node: ast.Assert, a_func: ast.FunctionDef) -> bool:
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

        if not ref_names:
            return False
        if ref_names & param_names:
            return False
        if ref_names & assigned_names:
            return True
        return False

    def check_Assert(self, a_node: ast.Assert, a_filepath: str) -> list[Violation]:
        """Check that assert is not used for input validation."""
        func = self._find_enclosing_function(a_node)
        if func and self._is_invariant_assert(a_node, func):
            return []
        return [Violation(
            a_filepath, a_node.lineno, a_node.col_offset,
            self.code,
            "assert forbidden for validation; use explicit checks with Result return",
        )]
