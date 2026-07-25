"""AST visitor with rule dispatch and parent context tracking."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

from scripts.lint.core.result import Result
from scripts.lint.core.violation import Violation

if TYPE_CHECKING:
    from scripts.lint.core.rule import Rule


@dataclass(frozen=True, slots=True)
class VisitorContext:
    """Read-only traversal context passed to rule check methods.

    Attributes:
        filepath: The file being linted.
        parent_stack: Tuple of ancestor AST nodes.
        with_node_ids: Set of AST node IDs inside with-statement context.
    """

    filepath: str
    parent_stack: tuple[ast.AST, ...] = field(default_factory=tuple)
    with_node_ids: frozenset[int] = field(default_factory=frozenset)

    def is_with_context(self, a_node: ast.AST) -> Result[bool]:
        """Check whether the given node is inside a with-statement context.

        Precondition: a_node is a valid AST node.
        Postcondition: returns Ok(True) if in with context, Ok(False) otherwise.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        return Result.success(id(a_node) in self.with_node_ids)


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
        self._with_node_ids: set[int] = set()
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

    def _build_context(self) -> VisitorContext:
        """Build a read-only VisitorContext from current traversal state.

        Precondition: none.
        Postcondition: returns a VisitorContext snapshot.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        return VisitorContext(
            filepath=self.filepath,
            parent_stack=tuple(self._parent_stack),
            with_node_ids=frozenset(self._with_node_ids),
        )

    def visit(self, a_node: ast.AST) -> Result[None]:
        """Visit an AST node, tracking parent context.

        Precondition: a_node is a valid AST node.
        Postcondition: returns Ok(None) after visiting.
        Side effect: pushes and pops parent stack.
        Resource: none.
        Failure: never fails.
        """
        self._parent_stack.append(a_node)
        if isinstance(a_node, ast.With):
            for item in a_node.items:
                self._mark_with_calls(item.context_expr)
        super().visit(a_node)
        self._parent_stack.pop()
        return Result.success(None)

    def _mark_with_calls(self, node: ast.AST) -> None:
        """Mark node and all descendants as with-statement context.

        Precondition: node is a valid AST node.
        Postcondition: node IDs added to _with_node_ids set.
        Side effect: modifies _with_node_ids.
        Resource: none.
        Failure: never fails.
        """
        self._with_node_ids.add(id(node))
        for child in ast.iter_child_nodes(node):
            self._mark_with_calls(child)

    def generic_visit(self, a_node: ast.AST) -> Result[None]:
        """Dispatch to rule check hooks for the given node type.

        Precondition: a_node is a valid AST node.
        Postcondition: returns Ok(None) after dispatching.
        Side effect: appends violations found by rules.
        Resource: none.
        Failure: never fails (exceptions per rule are caught and recorded).
        """
        node_type = type(a_node).__name__
        hook_name = re.sub(r"(?<!^)(?=[A-Z])", "_", node_type).lower()
        hook = f"check_{hook_name}"
        context = self._build_context()
        for rule in self.rules:
            if hasattr(rule, hook):
                try:
                    hook_result = getattr(rule, hook)(a_node, self.filepath, context)
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
                            message=f"Internal error in {rule_cls}.{hook}: {exc}",
                            severity="error",
                        )
                    )
        super().generic_visit(a_node)
        return Result.success(None)

    @property
    def parent_stack(self) -> tuple[ast.AST, ...]:
        """Return the current parent node stack as an immutable tuple.

        Precondition: none.
        Postcondition: returns tuple of ancestor AST nodes.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        return tuple(self._parent_stack)
