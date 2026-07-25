from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.lint.core.rule import Rule
    from scripts.lint.core.violation import Violation


class LintVisitor(ast.NodeVisitor):
    def __init__(self, rules: list[Rule], filepath: str) -> None:
        self.rules = rules
        self.filepath = filepath
        self.violations: list[Violation] = []

    def generic_visit(self, node: ast.AST) -> None:
        node_type = type(node).__name__
        for rule in self.rules:
            hook = f"check_{node_type}"
            if hasattr(rule, hook):
                result = getattr(rule, hook)(node, self.filepath)
                if result:
                    self.violations.extend(result)
        super().generic_visit(node)
