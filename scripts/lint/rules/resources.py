"""SC-080, SC-082: Resource management — context managers required."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
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

    def check_Call(self, node: ast.Call, filepath: str) -> list[Violation]:
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in self._calls:
            return [Violation(
                filepath, node.lineno, node.col_offset,
                self.code,
                f"'{func_name}()' must be used with a context manager (with statement)",
            )]
        return []
