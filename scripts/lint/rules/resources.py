"""SC-080, SC-082: Resource management — context managers required."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.core.visitor import get_visitor
from scripts.lint.config import ResourcesConfig



class ResourceContextManagerRule(Rule):
    """SC-080/082: Resources must be managed via context managers."""

    def __init__(self, config: ResourcesConfig | None = None) -> None:
        self._calls = frozenset((config or ResourcesConfig()).calls)

    @property
    def code(self) -> str:
        return "SC080"

    @property
    def description(self) -> str:
        return "Context managers for all resources"

    def check_Call(self, a_node: ast.Call, a_filepath: str) -> list[Violation]:
        """Check that resource calls are used with context managers."""
        func_name = ""
        if isinstance(a_node.func, ast.Name):
            func_name = a_node.func.id
        elif isinstance(a_node.func, ast.Attribute):
            func_name = a_node.func.attr

        violations: list[Violation] = []
        if func_name in self._calls:
            visitor = get_visitor()
            if not (visitor and visitor.is_with_context(a_node)):
                violations = [Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    f"'{func_name}()' must be used with a context manager (with statement)",
                )]
        return violations
