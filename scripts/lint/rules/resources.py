"""SC-080, SC-082: Resource management — context managers required."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from scripts.lint.config import ResourcesConfig
from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

if TYPE_CHECKING:
    from scripts.lint.core.visitor import VisitorContext


def _is_try_finally_resource_guard(
    a_node: ast.Call,
    a_context: VisitorContext,
) -> Result[bool]:
    """Check whether a resource call is guarded by a try/finally block.

    SC-080 permits resource management via with statements OR try/finally.
    This walks the parent stack to detect try nodes that have finally blocks.

    Precondition: a_node is a Call AST node; a_context is a valid VisitorContext.
    Postcondition: Returns Ok(True) if the call is inside a try/finally guard.
    Side effect: None.
    Resource: Reads a_context.parent_stack.
    Failure: Never fails (pure function).
    """
    for parent in a_context.parent_stack:
        if isinstance(parent, ast.Try) and parent.finalbody:
            for child in ast.walk(parent):
                if child is a_node:
                    return Result.success(True)
    return Result.success(False)


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

    def check_call(
        self,
        a_node: ast.Call,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that resource calls are used with context managers.

        Precondition: a_node is a Call AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: Reads the VisitorContext for with-statement and try/finally detection.
        Failure: Never fails (always returns Ok).
        """
        violations: list[Violation] = []
        if a_context is not None:
            func_name = ""
            if isinstance(a_node.func, ast.Name):
                func_name = a_node.func.id
            elif isinstance(a_node.func, ast.Attribute):
                func_name = a_node.func.attr

            if func_name in self._calls:
                is_ctx = a_context.is_with_context(a_node)
                is_with = is_ctx.is_success().value and is_ctx.value

                is_try_finally = False
                if not is_with:
                    tf_result = _is_try_finally_resource_guard(a_node, a_context)
                    is_try_finally = tf_result.is_success().value and tf_result.value

                if not is_with and not is_try_finally:
                    violations = [
                        Violation(
                            a_filepath,
                            a_node.lineno,
                            a_node.col_offset,
                            self.code,
                            f"'{func_name}()' must be used with a context"
                            " manager (with statement) or try/finally block",
                        )
                    ]
        return Result.success(violations)
