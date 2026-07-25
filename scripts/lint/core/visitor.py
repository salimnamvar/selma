from __future__ import annotations

import ast
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scripts.lint.core.rule import Rule
    from scripts.lint.core.violation import Violation


_current_visitor: ContextVar[Any] = ContextVar("_current_visitor")


def get_visitor() -> Any:
    """Return the current LintVisitor from context, or None."""
    return _current_visitor.get(None)


class LintVisitor(ast.NodeVisitor):
    def __init__(self, rules: list[Rule], filepath: str) -> None:
        self.rules = rules
        self.filepath = filepath
        self.violations: list[Violation] = []
        self._parent_stack: list[ast.AST] = []
        self._with_calls: set[int] = set()

    def visit(self, a_node: ast.AST) -> None:
        """Visit an AST node, tracking parent context."""
        self._parent_stack.append(a_node)
        if isinstance(a_node, ast.With):
            for item in a_node.items:
                self._mark_with_calls(item.context_expr)
        _current_visitor.set(self)
        super().visit(a_node)
        self._parent_stack.pop()

    def _mark_with_calls(self, node: ast.AST) -> None:
        self._with_calls.add(id(node))
        for child in ast.iter_child_nodes(node):
            self._mark_with_calls(child)

    def generic_visit(self, a_node: ast.AST) -> None:
        """Dispatch to rule check hooks for the given node type."""
        node_type = type(a_node).__name__
        for rule in self.rules:
            hook = f"check_{node_type}"
            if hasattr(rule, hook):
                result = getattr(rule, hook)(a_node, self.filepath)
                if result:
                    self.violations.extend(result)
        super().generic_visit(a_node)

    def is_inside_with(self) -> bool:
        """Check whether the current node is inside a with-statement."""
        return any(isinstance(p, ast.With) for p in self._parent_stack)

    def is_with_context(self, a_node: ast.AST) -> bool:
        """Check whether the given node is inside a with-statement context."""
        return id(a_node) in self._with_calls
