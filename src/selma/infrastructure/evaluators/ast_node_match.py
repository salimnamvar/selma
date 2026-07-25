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
        a_target_node = a_config.get("target_node", "")
        a_conditions = a_config.get("conditions", [])
        a_message_template = a_config.get("message_template", "")
        a_exemptions = a_rule.get("parameters", {})
        for a_node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self._node_name(a_node) != a_target_node:
                b_continue = False
            if b_continue and self._is_node_excluded(a_node, a_exemptions):
                b_continue = False
            if b_continue and self._all_conditions_match(a_node, a_conditions):
                a_ctx = self._build_context(a_node)
                a_msg = self._render_message(a_message_template, a_ctx)
                findings.append(
                    Finding(
                        rule_id=a_rule.get("lineage_id", ""),
                        file="",
                        line=self._get_line(a_node),
                        col=self._get_col(a_node),
                        message=a_msg,
                    )
                )
        return findings

    @staticmethod
    def _is_node_excluded(a_node: ast.AST, a_exemptions: dict[str, Any]) -> bool:
        """Check if a node should be excluded based on exemption parameters."""
        b_continue = True
        result = False
        if b_continue and a_exemptions.get("exempt_dunders", False):
            a_name = getattr(a_node, "name", "")
            if b_continue and self._is_dunder(a_name):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_properties", False):
            if b_continue and self._has_decorator(a_node, "property"):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_abstract", False):
            if b_continue and self._has_decorator(a_node, "abstractmethod"):
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
        for a_cond in a_conditions:
            if b_continue and not _match_condition(a_node, a_cond):
                b_continue = False
                result = False
        return result

    @staticmethod
    def _build_context(a_node: ast.AST) -> dict[str, Any]:
        """Build template context from a matched node."""
        a_name = getattr(a_node, "name", "<unknown>")
        result: dict[str, Any] = {
            "name": a_name,
            "root.name": a_name,
        }
        return result


def _match_condition(a_node: ast.AST, a_cond: dict[str, Any]) -> bool:
    """Evaluate a single condition against an AST node."""
    b_continue = True
    result = False
    a_field = a_cond.get("field", "")
    a_operator = a_cond.get("operator", "")
    a_value = a_cond.get("value", "")
    a_field_value = _resolve_field(a_node, a_field)
    if b_continue and a_operator == "exists":
        b_continue = False
        result = a_field_value is not None
    if b_continue and a_operator == "not_exists":
        b_continue = False
        result = a_field_value is None
    if b_continue and a_operator == "equals":
        b_continue = False
        result = str(a_field_value) == str(a_value)
    if b_continue and a_operator == "not_equals":
        b_continue = False
        result = str(a_field_value) != str(a_value)
    if b_continue and a_operator == "matches":
        b_continue = False
        result = bool(re.search(str(a_value), str(a_field_value)))
    if b_continue and a_operator == "not_matches":
        b_continue = False
        result = not bool(re.search(str(a_value), str(a_field_value)))
    if b_continue and a_operator == "contains":
        b_continue = False
        result = str(a_value) in str(a_field_value)
    if b_continue and a_operator == "not_contains":
        b_continue = False
        result = str(a_value) not in str(a_field_value)
    if b_continue and a_operator == "contains_node":
        b_continue = False
        result = _contains_node_type(a_node, str(a_value))
    return result


def _resolve_field(a_node: ast.AST, a_field: str) -> Any:
    """Resolve a dotted field path on an AST node (e.g. 'returns.annotation')."""
    b_continue = True
    result: Any = None
    parts = a_field.split(".")
    current: Any = a_node
    for a_part in parts:
        if b_continue and current is None:
            b_continue = False
            result = None
        if b_continue and isinstance(current, ast.AST):
            current = getattr(current, a_part, None)
        if b_continue and not isinstance(current, ast.AST) and current is not None:
            current = None
    if b_continue:
        result = current
    return result


def _contains_node_type(a_node: ast.AST, a_type_name: str) -> bool:
    """Check if a node's body contains a specific node type."""
    b_continue = True
    result = False
    a_body = getattr(a_node, "body", None)
    if b_continue and a_body is None:
        b_continue = False
        result = False
    if b_continue and isinstance(a_body, list):
        for a_child in a_body:
            if b_continue and type(a_child).__name__ == a_type_name:
                b_continue = False
                result = True
    return result
