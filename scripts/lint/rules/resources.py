"""SC-080, SC-082: Resource management — context managers required."""

from __future__ import annotations

import ast

from scripts.lint.config import ResourcesConfig
from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.core.visitor import get_visitor


class ResourceContextManagerRule(Rule):
    """SC-080/082: Resources must be managed via context managers."""

    def __init__(self, config: ResourcesConfig | None = None) -> None:
        self._calls = frozenset((config or ResourcesConfig()).calls)

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
            b_result = "SC080"
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
            b_result = "Context managers for all resources"
        return b_result

    def check_call(self, a_node: ast.Call, a_filepath: str) -> Result[list[Violation]]:
        """Check that resource calls are used with context managers.

        Precondition: a_node is a Call AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: Reads the current visitor context via get_visitor().
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            func_name = ""
            if isinstance(a_node.func, ast.Name):
                func_name = a_node.func.id
            elif isinstance(a_node.func, ast.Attribute):
                func_name = a_node.func.attr

            if func_name in self._calls:
                visitor_result = get_visitor()
                if visitor_result.is_success().value:
                    visitor = visitor_result.value
                    if visitor is not None:
                        ctx_result = visitor.is_with_context(a_node)
                        is_ctx = ctx_result.is_success().value and ctx_result.value
                        if not is_ctx:
                            violations = [
                                Violation(
                                    a_filepath,
                                    a_node.lineno,
                                    a_node.col_offset,
                                    self.code,
                                    f"'{func_name}()' must be used with a context"
                                    " manager (with statement)",
                                )
                            ]
            result = Result.success(violations)
        return result
