"""AstWalkEvaluator — walk AST counting specific node types within root nodes."""

from __future__ import annotations

import ast
import re
from typing import Any

from selma.domain.entities.finding import Finding
from selma.infrastructure.evaluators.base import EvaluatorBase


class AstWalkEvaluator(EvaluatorBase):
    """Evaluate rules by walking AST and counting node types.

    Used for: SC-001 (single exit), SC-002 (zero raise), SC-010 (function length).

    Config fields:
        root_node: Name of root node to iterate (e.g. "FunctionDef")
        walk_nodes: List of child node names to count (e.g. ["Return", "Raise"])
        walk_config: Exclusion flags (exclude_nested_functions, exclude_dunders, etc.)
        count: Threshold check {"operator": "gt", "value": 1}
        count_breakdown: Map node name to label for message
        message_template: Template string with {root.name}, {count}, {breakdown}
    """

    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> list[Finding]:
        """Walk AST counting specific node types within root nodes."""
        b_continue = True
        findings: list[Finding] = []
        a_root_node = a_config.get("root_node", "")
        a_walk_nodes = a_config.get("walk_nodes", [])
        a_walk_config = a_config.get("walk_config", {})
        a_count_config = a_config.get("count", {})
        a_count_breakdown = a_config.get("count_breakdown", {})
        a_message_template = a_config.get("message_template", "")
        a_threshold_value = a_count_config.get("value", 0)
        a_threshold_op = a_count_config.get("operator", "gt")
        for a_node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self._node_name(a_node) != a_root_node:
                b_continue = False
            if b_continue and self._is_excluded(a_node, a_walk_config, a_config):
                b_continue = False
            if b_continue:
                a_count = self._count_child_nodes(a_node, a_walk_nodes, a_walk_config)
                if b_continue and self._check_operator(a_count, a_threshold_op, a_threshold_value):
                    a_breakdown = self._build_breakdown(a_node, a_walk_nodes, a_count_breakdown)
                    a_ctx = self._build_context(a_node, a_count, a_breakdown)
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
    def _is_excluded(
        a_node: ast.AST,
        a_walk_config: dict[str, Any],
        a_config: dict[str, Any],
    ) -> bool:
        """Check if a root node should be excluded from evaluation."""
        b_continue = True
        result = False
        if b_continue and a_walk_config.get("exclude_dunders", False):
            a_name = getattr(a_node, "name", "")
            if b_continue and self._is_dunder(a_name):
                b_continue = False
                result = True
        if b_continue and a_walk_config.get("exclude_generators", False):
            if b_continue and self._is_generator(a_node):
                b_continue = False
                result = True
        if b_continue and a_walk_config.get("exclude_framework_adapters", False):
            a_params = a_config.get("parameters", {})
            a_adapter_keywords = a_params.get("adapter_keywords", ["exception", "error", "http"])
            a_name = getattr(a_node, "name", "")
            if b_continue:
                for a_kw in a_adapter_keywords:
                    if b_continue and a_kw.lower() in a_name.lower():
                        b_continue = False
                        result = True
        return result

    @staticmethod
    def _is_generator(a_node: ast.AST) -> bool:
        """Check if a FunctionDef is a generator (contains yield)."""
        b_continue = True
        result = False
        if b_continue and not isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            b_continue = False
            result = False
        if b_continue:
            for a_child in ast.walk(a_node):
                if b_continue and isinstance(a_child, (ast.Yield, ast.YieldFrom)):
                    b_continue = False
                    result = True
        return result

    @staticmethod
    def _count_child_nodes(
        a_node: ast.AST,
        a_walk_nodes: list[str],
        a_walk_config: dict[str, Any],
    ) -> int:
        """Count matching child nodes within a root node, respecting exclusions."""
        b_continue = True
        a_count = 0
        a_exclude_nested = a_walk_config.get("exclude_nested_functions", False)
        for a_child in ast.walk(a_node):
            b_continue = True
            if b_continue and a_exclude_nested and isinstance(a_child, ast.FunctionDef):
                b_continue = False
            if b_continue and a_exclude_nested and isinstance(a_child, ast.AsyncFunctionDef):
                b_continue = False
            if b_continue and self._node_name(a_child) in a_walk_nodes:
                a_count += 1
        return a_count

    @staticmethod
    def _build_breakdown(
        a_node: ast.AST,
        a_walk_nodes: list[str],
        a_count_breakdown: dict[str, str],
    ) -> str:
        """Build a breakdown string like '2 return, 1 raise'."""
        b_continue = True
        result = ""
        if b_continue and not a_count_breakdown:
            b_continue = False
            result = ""
        if b_continue:
            parts: list[str] = []
            for a_child in ast.walk(a_node):
                a_name = self._node_name(a_child)
                if a_name in a_count_breakdown:
                    parts.append(a_count_breakdown[a_name])
            if b_continue:
                b_continue = False
                result = ", ".join(parts) if parts else ""
        return result

    @staticmethod
    def _build_context(
        a_node: ast.AST,
        a_count: int,
        a_breakdown: str,
    ) -> dict[str, Any]:
        """Build template context dict from a node and count."""
        b_continue = True
        a_name = getattr(a_node, "name", "<unknown>")
        result: dict[str, Any] = {
            "root.name": a_name,
            "name": a_name,
            "count": a_count,
            "breakdown": a_breakdown,
        }
        return result
