"""EvaluatorBase — abstract base for all AST evaluator strategies."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
import ast
import re
from typing import Any
from typing import cast

from selma.domain.entities.finding import Finding


class EvaluatorBase(ABC):
    """Abstract base for AST evaluator strategies.

    Each evaluator type (ast_walk, ast_node_match, etc.) implements
    this interface. The interpreter dispatches to the correct evaluator
    based on the rule's evaluator_type field.
    """

    @abstractmethod
    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> list[Finding]:
        """Evaluate a rule configuration against an AST.

        Preconditions:
            - a_tree is a valid Python AST.
            - a_config is the evaluator_config dict from the JSON rule.
            - a_rule is the full rule dict.

        Postconditions:
            Returns a list of Finding objects (may be empty).

        Side Effects: None.
        Resource: None.
        Failure: Never raises — returns empty list on error.
        """

    @staticmethod
    def node_name(a_node: ast.AST) -> str:
        """Return the class name of an AST node."""
        return type(a_node).__name__

    @staticmethod
    def _get_line(a_node: ast.AST) -> int:
        """Return the line number of an AST node, defaulting to 0."""
        return getattr(a_node, "lineno", 0)

    @staticmethod
    def _get_col(a_node: ast.AST) -> int:
        """Return the column offset of an AST node, defaulting to 0."""
        return getattr(a_node, "col_offset", 0)

    @staticmethod
    def _get_attr(a_node: ast.AST, a_attr: str, a_default: Any = None) -> Any:
        """Safely get an attribute from an AST node."""
        return getattr(a_node, a_attr, a_default)

    @staticmethod
    def _render_message(a_template: str, a_context: dict[str, Any]) -> str:
        """Render a message template with context values."""
        b_continue = True
        result = a_template
        if b_continue and a_context:
            # Only format when every simple placeholder key is present
            # (SC-006: do not use exceptions for expected missing-key cases).
            field_names = set(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", a_template))
            if field_names and field_names.issubset(set(a_context.keys())):
                result = a_template.format(**{k: a_context[k] for k in field_names})
            elif not field_names:
                result = a_template
            else:
                result = a_template
        return result

    @staticmethod
    def _check_operator(a_value: int, a_operator: str, a_threshold: int) -> bool:
        """Check a value against a threshold using an operator."""
        b_continue = True
        result = False
        if b_continue and a_operator == "gt":
            b_continue = False
            result = a_value > a_threshold
        if b_continue and a_operator == "gte":
            b_continue = False
            result = a_value >= a_threshold
        if b_continue and a_operator == "lt":
            b_continue = False
            result = a_value < a_threshold
        if b_continue and a_operator == "lte":
            b_continue = False
            result = a_value <= a_threshold
        if b_continue and a_operator == "eq":
            b_continue = False
            result = a_value == a_threshold
        if b_continue and a_operator == "neq":
            b_continue = False
            result = a_value != a_threshold
        return result

    @staticmethod
    def is_dunder(a_name: str) -> bool:
        """Check if a name is a dunder (double underscore) method."""
        b_continue = True
        result = False
        if b_continue and a_name.startswith("__") and a_name.endswith("__"):
            b_continue = False
            result = True
        return result

    @staticmethod
    def has_decorator(a_node: ast.AST, a_decorator_name: str) -> bool:
        r"""Check if an AST node has a specific decorator.

        Matches bare names (@property), attributes (@app.command), and
        calls of those forms (@app.command(), @click.command(name=\"x\")).
        """
        b_continue = True
        result = False
        if b_continue and not hasattr(a_node, "decorator_list"):
            b_continue = False
            result = False
        if b_continue and a_node.decorator_list is None:  # type: ignore[union-attr]
            b_continue = False
            result = False
        if b_continue:
            for decorator in a_node.decorator_list:  # type: ignore[union-attr]
                target: ast.expr = cast("ast.expr", decorator)
                # @app.command() → Call(func=Attribute(...)); unwrap to the callee.
                if isinstance(target, ast.Call):
                    target = target.func
                b_continue_inner = True
                if b_continue_inner and isinstance(target, ast.Name):
                    b_continue_inner = False
                    result = target.id == a_decorator_name
                if b_continue_inner and isinstance(target, ast.Attribute):
                    b_continue_inner = False
                    result = target.attr == a_decorator_name
                if result:
                    b_continue = False
        return result
