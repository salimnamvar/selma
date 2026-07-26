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
        target_node = a_config.get("target_node", "Call")
        target_functions = a_config.get("target_functions", [])
        context = a_config.get("context", {})
        message_template = a_config.get("message_template", "")
        for node in ast.walk(a_tree):
            if self.node_name(node) != target_node:
                continue
            if not isinstance(node, ast.Call):
                continue
            b_continue = True
            func_name = _extract_call_name(node)
            if b_continue and func_name not in target_functions:
                b_continue = False
            if b_continue and not _is_in_required_context(node, a_tree, context):
                ctx = {"function": func_name, "name": func_name}
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
    _a_must_be_inside = a_context.get("must_be_inside", [])
    or_try_finally = a_context.get("or_try_finally", False)
    parents = _find_parents(a_node, a_tree)
    if b_continue:
        for parent in parents:
            b_continue_inner = True
            if b_continue_inner and isinstance(parent, ast.With):
                b_continue_inner = False
                result = True
            if b_continue_inner and or_try_finally and isinstance(parent, ast.Try):
                if b_continue_inner and parent.finalbody:
                    b_continue_inner = False
                    result = True
                if b_continue_inner and parent.handlers:
                    b_continue_inner = False
                    result = True
            if result:
                b_continue = False
    return result


def _find_parents(a_node: ast.AST, a_tree: ast.AST) -> list[ast.AST]:
    """Find all parent nodes of a given node by walking the tree."""
    result: list[ast.AST] = []
    for parent in ast.walk(a_tree):
        for descendant in ast.walk(parent):
            if descendant is a_node and descendant is not parent:
                result.append(parent)
                break
    return result
