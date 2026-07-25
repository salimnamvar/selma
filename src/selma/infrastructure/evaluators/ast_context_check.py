"""AstContextCheckEvaluator — check that calls appear inside required context managers."""

from __future__ import annotations

import ast
from typing import Any

from selma.domain.entities.finding import Finding
from selma.infrastructure.evaluators.base import EvaluatorBase


class AstContextCheckEvaluator(EvaluatorBase):
    """Evaluate rules by checking parent context of function calls.

    Used for: SC-080 (context managers).

    Config fields:
        target_node: Node type to find (e.g. "Call")
        target_functions: Function names that need context managers
        context: Required parent context configuration
        message_template: Template string
    """

    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> list[Finding]:
        """Check that target function calls appear inside required context."""
        b_continue = True
        findings: list[Finding] = []
        a_target_node = a_config.get("target_node", "Call")
        a_target_functions = a_config.get("target_functions", [])
        a_context = a_config.get("context", {})
        a_message_template = a_config.get("message_template", "")
        for a_node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self._node_name(a_node) != a_target_node:
                b_continue = False
            if b_continue and not isinstance(a_node, ast.Call):
                b_continue = False
            if b_continue:
                a_func_name = _extract_call_name(a_node)
                if b_continue and a_func_name not in a_target_functions:
                    b_continue = False
                if b_continue and not _is_in_required_context(a_node, a_tree, a_context):
                    a_ctx = {"function": a_func_name, "name": a_func_name}
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


def _extract_call_name(a_node: ast.Call) -> str:
    """Extract the function name from a Call node."""
    b_continue = True
    result = ""
    if b_continue and isinstance(a_node.func, ast.Name):
        b_continue = False
        result = a_node.func.id
    if b_continue and isinstance(a_node.func, ast.Attribute):
        b_continue = False
        result = a_node.func.attr
    return result


def _is_in_required_context(
    a_node: ast.AST,
    a_tree: ast.AST,
    a_context: dict[str, Any],
) -> bool:
    """Check if a node is inside a required context (with statement or try/finally)."""
    b_continue = True
    result = False
    a_must_be_inside = a_context.get("must_be_inside", [])
    a_or_try_finally = a_context.get("or_try_finally", False)
    a_parents = _find_parents(a_node, a_tree)
    if b_continue:
        for a_parent in a_parents:
            b_continue_inner = True
            if b_continue_inner and isinstance(a_parent, ast.With):
                b_continue_inner = False
                result = True
            if b_continue_inner and a_or_try_finally and isinstance(a_parent, ast.Try):
                if b_continue_inner and a_parent.finalbody:
                    b_continue_inner = False
                    result = True
                if b_continue_inner and a_parent.handlers:
                    b_continue_inner = False
                    result = True
            if result:
                b_continue = False
    return result


def _find_parents(a_node: ast.AST, a_tree: ast.AST) -> list[ast.AST]:
    """Find all parent nodes of a given node by walking the tree."""
    b_continue = True
    result: list[ast.AST] = []
    for a_parent in ast.walk(a_tree):
        if b_continue:
            for a_child in ast.iter_child_nodes(a_parent):
                if b_continue and a_child is a_node:
                    result.append(a_parent)
                    break
                if b_continue:
                    for a_descendant in ast.walk(a_child):
                        if b_continue and a_descendant is a_node:
                            result.append(a_parent)
                            b_continue = False
                            break
    return result
