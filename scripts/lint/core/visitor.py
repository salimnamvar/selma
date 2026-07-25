"""AST visitor with rule dispatch and parent context tracking."""
from __future__ import annotations

import ast
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

from scripts.lint.core.result import Result

if TYPE_CHECKING:
    from scripts.lint.core.rule import Rule
    from scripts.lint.core.violation import Violation


_current_visitor: ContextVar[Any] = ContextVar("_current_visitor")


def get_visitor() -> Result[Any]:
    """Return the current LintVisitor from context, or Ok(None).

    Precondition: none.
    Postcondition: returns Ok with current visitor or Ok(None).
    Side effect: none.
    Resource: none.
    Failure: never fails.
    """
    b_continue = True
    result: Result[Any] = Result.success(None)
    if b_continue:
        result = Result.success(_current_visitor.get(None))
    return result


class LintVisitor(ast.NodeVisitor):
    def __init__(self, rules: list[Rule], filepath: str) -> None:
        self.rules = rules
        self.filepath = filepath
        self.violations: list[Violation] = []
        self._parent_stack: list[ast.AST] = []
        self._with_calls: set[int] = set()

    def visit(self, a_node: ast.AST) -> Result[None]:
        """Visit an AST node, tracking parent context.

        Precondition: a_node is a valid AST node.
        Postcondition: returns Ok(None) after visiting.
        Side effect: pushes and pops parent stack, sets context var.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        result: Result[None] = Result.success(None)
        if b_continue:
            self._parent_stack.append(a_node)
            if isinstance(a_node, ast.With):
                for item in a_node.items:
                    self._mark_with_calls(item.context_expr)
            _current_visitor.set(self)
            super().visit(a_node)
            self._parent_stack.pop()
        return result

    def _mark_with_calls(self, node: ast.AST) -> Result[None]:
        """Mark node and all descendants as with-statement context.

        Precondition: node is a valid AST node.
        Postcondition: returns Ok(None) after marking.
        Side effect: adds node IDs to _with_calls set.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        result: Result[None] = Result.success(None)
        if b_continue:
            self._with_calls.add(id(node))
            for child in ast.iter_child_nodes(node):
                self._mark_with_calls(child)
        return result

    def generic_visit(self, a_node: ast.AST) -> Result[None]:
        """Dispatch to rule check hooks for the given node type.

        Precondition: a_node is a valid AST node.
        Postcondition: returns Ok(None) after dispatching.
        Side effect: appends violations found by rules.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        result: Result[None] = Result.success(None)
        if b_continue:
            node_type = type(a_node).__name__
            for rule in self.rules:
                hook = f"check_{node_type}"
                if hasattr(rule, hook):
                    hook_result = getattr(rule, hook)(a_node, self.filepath)
                    if hook_result.is_success() and hook_result.value:
                        self.violations.extend(hook_result.value)
            super().generic_visit(a_node)
        return result

    def is_inside_with(self) -> Result[bool]:
        """Check whether the current node is inside a with-statement.

        Precondition: none.
        Postcondition: returns Ok(True) if inside with, Ok(False) otherwise.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        result: Result[bool] = Result.success(False)
        if b_continue:
            result = Result.success(any(isinstance(p, ast.With) for p in self._parent_stack))
        return result

    def is_with_context(self, a_node: ast.AST) -> Result[bool]:
        """Check whether the given node is inside a with-statement context.

        Precondition: a_node is a valid AST node.
        Postcondition: returns Ok(True) if in with context, Ok(False) otherwise.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        result: Result[bool] = Result.success(False)
        if b_continue:
            result = Result.success(id(a_node) in self._with_calls)
        return result
