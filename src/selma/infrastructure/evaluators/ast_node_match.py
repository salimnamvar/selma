"""AstNodeMatchEvaluator — match AST nodes with field conditions."""

from __future__ import annotations

import ast
import re
from typing import Any

from selma.domain.entities.finding import Finding
from selma.infrastructure.evaluators.base import EvaluatorBase


class AstNodeMatchEvaluator(EvaluatorBase):
    """Evaluate rules by matching AST nodes against field conditions.

    Used for: SC-003 (structured result return), SC-024 (explicit return types).

    Config fields:
        target_node: Node type to match (e.g. "FunctionDef")
        conditions: List of {field, operator, value} dicts
        message_template: Template string
    """

    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> list[Finding]:
        """Match AST nodes against field conditions."""
        b_continue = True
        findings: list[Finding] = []
        target_node = a_config.get("target_node", "")
        conditions = a_config.get("conditions", [])
        message_template = a_config.get("message_template", "")
        exemptions = a_rule.get("parameters", {})
        for node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self.node_name(node) != target_node:
                b_continue = False
            if b_continue and self._is_node_excluded(node, exemptions):
                b_continue = False
            if b_continue and self._all_conditions_match(node, conditions):
                ctx = self._build_context(node)
                msg = self._render_message(message_template, ctx)
                findings.append(
                    Finding(
                        rule_id=a_rule.get("lineage_id", ""),
                        file="",
                        line=self._get_line(node),
                        col=self._get_col(node),
                        message=msg,
                    )
                )
        return findings

    @staticmethod
    def _is_node_excluded(a_node: ast.AST, a_exemptions: dict[str, Any]) -> bool:
        """Check if a node should be excluded based on exemption parameters."""
        b_continue = True
        result = False
        if b_continue and a_exemptions.get("exempt_dunders", False):
            name = getattr(a_node, "name", "")
            if b_continue and EvaluatorBase.is_dunder(name):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_properties", False):
            if b_continue and EvaluatorBase.has_decorator(a_node, "property"):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_abstract", False):
            if b_continue and EvaluatorBase.has_decorator(a_node, "abstractmethod"):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_no_args", False):
            if b_continue and _has_no_non_self_args(a_node):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_init", False):
            name = getattr(a_node, "name", "")
            if b_continue and name in (
                "__init__",
                "__post_init__",
                "__init_subclass__",
            ):
                b_continue = False
                result = True
        return result

    @staticmethod
    def _all_conditions_match(
        a_node: ast.AST,
        a_conditions: list[dict[str, Any]],
    ) -> bool:
        """Check if all conditions match against a node."""
        b_continue = True
        result = True
        for cond in a_conditions:
            if b_continue and not _match_condition(a_node, cond):
                b_continue = False
                result = False
        return result

    @staticmethod
    def _build_context(a_node: ast.AST) -> dict[str, Any]:
        """Build template context from a matched node."""
        name = getattr(a_node, "name", "<unknown>")
        result: dict[str, Any] = {
            "name": name,
            "root.name": name,
        }
        return result


def _match_condition(a_node: ast.AST, a_cond: dict[str, Any]) -> bool:
    """Evaluate a single condition against an AST node."""
    b_continue = True
    result = False
    field = a_cond.get("field", "")
    operator = a_cond.get("operator", "")
    value = a_cond.get("value", "")
    field_value = _resolve_field(a_node, field)
    if b_continue and operator == "exists":
        b_continue = False
        result = field_value is not None
    if b_continue and operator == "not_exists":
        b_continue = False
        result = field_value is None
    if b_continue and operator == "equals":
        b_continue = False
        result = str(field_value) == str(value)
    if b_continue and operator == "not_equals":
        b_continue = False
        result = str(field_value) != str(value)
    if b_continue and operator == "matches":
        b_continue = False
        result = bool(re.search(str(value), str(field_value)))
    if b_continue and operator == "not_matches":
        b_continue = False
        result = not bool(re.search(str(value), str(field_value)))
    if b_continue and operator == "contains":
        b_continue = False
        result = str(value) in str(field_value)
    if b_continue and operator == "not_contains":
        b_continue = False
        result = str(value) not in str(field_value)
    if b_continue and operator == "contains_node":
        b_continue = False
        result = _contains_node_type(a_node, str(value))
    return result


def _resolve_field(a_node: ast.AST, a_field: str) -> Any:
    """Resolve a dotted field path on an AST node (e.g. 'returns.value.id')."""
    current: Any = a_node
    for part in a_field.split("."):
        if current is None:
            return None
        if isinstance(current, ast.AST):
            current = getattr(current, part, None)
        else:
            return None
    return current


def _contains_node_type(a_node: ast.AST, a_type_name: str) -> bool:
    """Check if a node's body contains a specific node type."""
    b_continue = True
    result = False
    body: list[ast.AST] | None = getattr(a_node, "body", None)
    if b_continue and body is None:
        b_continue = False
        result = False
    if b_continue and isinstance(body, list):
        for child in body:
            if b_continue and type(child).__name__ == a_type_name:
                b_continue = False
                result = True
    return result


def _has_no_non_self_args(a_node: ast.AST) -> bool:
    """Check if a function has no arguments besides self/cls."""
    args = getattr(a_node, "args", None)
    if args is None:
        return True
    params: list[ast.arg] = args.args if hasattr(args, "args") else []
    skip_names = {"self", "cls"}
    non_self = [p for p in params if p.arg not in skip_names]
    return len(non_self) == 0
