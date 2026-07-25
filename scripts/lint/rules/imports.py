"""Import rules: no imports inside functions, proper grouping."""

from __future__ import annotations

import ast

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


class ImportInFunctionRule(Rule):
    """No imports inside function/method bodies."""

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
            b_result = "import-in-function"
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
            b_result = "No imports inside functions"
        return b_result

    def check_function_def(
        self, a_node: ast.FunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that no imports exist inside function bodies.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            for node in ast.walk(a_node):
                if node is a_node:
                    continue
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    violations.append(
                        Violation(
                            a_filepath,
                            node.lineno,
                            node.col_offset,
                            self.code,
                            f"Import inside function '{a_node.name}' forbidden",
                        )
                    )
            result = Result.success(violations)
        return result

    def check_async_function_def(
        self, a_node: ast.AsyncFunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that no imports exist inside async function bodies.

        Precondition: a_node is an AsyncFunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            for node in ast.walk(a_node):
                if node is a_node:
                    continue
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    violations.append(
                        Violation(
                            a_filepath,
                            node.lineno,
                            node.col_offset,
                            self.code,
                            f"Import inside function '{a_node.name}' forbidden",
                        )
                    )
            result = Result.success(violations)
        return result
