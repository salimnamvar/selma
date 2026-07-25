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

    def _check_body(self, body: list[ast.stmt], filepath: str, func_name: str) -> list[Violation]:
        violations: list[Violation] = []
        for stmt in body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                violations.append(Violation(
                    filepath, stmt.lineno, stmt.col_offset,
                    self.code,
                    f"Import inside function '{func_name}' forbidden",
                ))
            elif isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                for inner in ast.iter_child_nodes(stmt):
                    if isinstance(inner, ast.stmt):
                        violations.extend(self._check_body([inner], filepath, func_name))
        return violations

    def check_FunctionDef(self, node: ast.FunctionDef, filepath: str) -> list[Violation]:
        return self._check_body(node.body, filepath, node.name)

    check_AsyncFunctionDef = check_FunctionDef
