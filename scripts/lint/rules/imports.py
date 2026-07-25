"""Import rules: no imports inside functions, proper grouping."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation



class ImportInFunctionRule(Rule):
    """No imports inside function/method bodies."""

    @property
    def code(self) -> str:
        return "import-in-function"

    @property
    def description(self) -> str:
        return "No imports inside functions"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that no imports exist inside function bodies."""
        violations: list[Violation] = []
        for node in ast.walk(a_node):
            if node is a_node:
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                violations.append(Violation(
                    a_filepath, node.lineno, node.col_offset,
                    self.code,
                    f"Import inside function '{a_node.name}' forbidden",
                ))
        return violations

    check_AsyncFunctionDef = check_FunctionDef
