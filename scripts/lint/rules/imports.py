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

    def _check_body(self, a_body: list[ast.stmt], a_filepath: str, a_func_name: str) -> list[Violation]:
        violations: list[Violation] = []
        for stmt in a_body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                violations.append(Violation(
                    a_filepath, stmt.lineno, stmt.col_offset,
                    self.code,
                    f"Import inside function '{a_func_name}' forbidden",
                ))
            elif isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                for inner in ast.iter_child_nodes(stmt):
                    if isinstance(inner, ast.stmt):
                        violations.extend(self._check_body([inner], a_filepath, a_func_name))
        return violations

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that no imports exist inside function bodies."""
        return self._check_body(a_node.body, a_filepath, a_node.name)

    check_AsyncFunctionDef = check_FunctionDef
