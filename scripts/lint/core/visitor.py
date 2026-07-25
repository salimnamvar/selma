"""AST visitor with rule dispatch and parent context tracking."""

from __future__ import annotations

import ast
from contextvars import ContextVar
import re
from typing import TYPE_CHECKING
from typing import Any

from scripts.lint.core.result import Result

if TYPE_CHECKING:
    from scripts.lint.core.rule import Rule

_current_visitor: ContextVar[Any] = ContextVar("_current_visitor")


def get_visitor() -> Result[Any]:
    """Return the current LintVisitor from context, or Ok(None)."""
    return Result.success(_current_visitor.get(None))


_VALID_AST_HOOKS: set[str] = {
    f"check_{re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()}"
    for cls in ast.__dict__.values()
    if isinstance(cls, type) and issubclass(cls, ast.AST)
}


class LintVisitor(ast.NodeVisitor):
    """AST visitor with rule dispatch and parent context tracking."""

    def __init__(self, rules: list[Rule], filepath: str) -> None:
        self.rules = rules
        self.filepath = filepath
        self.violations: list[Violation] = []
        self._parent_stack: list[ast.AST] = []
        self._with_calls: set[int] = set()
        self._validate_rule_hooks()

    def _validate_rule_hooks(self) -> None:
        """Validate that all check_* methods on registered rules target valid AST nodes."""
        for rule in self.rules:
            for attr_name in dir(rule):
                if attr_name.startswith("check_") and callable(
                    getattr(rule, attr_name)
                ):
                    if attr_name not in _VALID_AST_HOOKS:
                        rule_name = rule.__class__.__name__
                        raise ValueError(
                            f"Invalid rule hook '{attr_name}' on {rule_name}. "
                            f"Does not match any ast.AST node type."
                        )

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
            hook_name = re.sub(r"(?<!^)(?=[A-Z])", "_", node_type).lower()
            hook = f"check_{hook_name}"
            for rule in self.rules:
                if hasattr(rule, hook):
                    try:
                        hook_result = getattr(rule, hook)(a_node, self.filepath)
                        if hook_result.is_success().value and hook_result.value:
                            self.violations.extend(hook_result.value)
                    except Exception as exc:
                        line_no = getattr(a_node, "lineno", 1)
                        col_no = getattr(a_node, "col_offset", 0)
                        rule_cls = rule.__class__.__name__
                        self.violations.append(
                            Violation(
                                filepath=self.filepath,
                                line=line_no,
                                col=col_no,
                                code="LINT-ERR",
                                message=(f"Internal error in {rule_cls}.{hook}: {exc}"),
                                severity="error",
                            )
                        )
            super().generic_visit(a_node)
        return result

    @property
    def parent_stack(self) -> tuple[ast.AST, ...]:
        """Return the current parent node stack as an immutable tuple.

        Precondition: none.
        Postcondition: returns tuple of ancestor AST nodes.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        b_result: tuple[ast.AST, ...] = ()
        if b_continue:
            b_result = tuple(self._parent_stack)
        return b_result

    def is_inside_with(self) -> Result[bool]:
        """Check whether the current node is inside a with-statement.

        Precondition: none.
        Postcondition: returns Ok(True) if inside with, Ok(False) otherwise.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        result: Result[bool] = Result.success(a_value=False)
        if b_continue:
            result = Result.success(
                any(isinstance(p, ast.With) for p in self._parent_stack)
            )
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
        result: Result[bool] = Result.success(a_value=False)
        if b_continue:
            result = Result.success(id(a_node) in self._with_calls)
        return result
