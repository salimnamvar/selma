"""AstModuleCheckEvaluator — module-level checks (sentinels, imports, globals)."""

from __future__ import annotations

import ast
from typing import Any

from selma.domain.entities.finding import Finding
from selma.infrastructure.evaluators.base import EvaluatorBase


class AstModuleCheckEvaluator(EvaluatorBase):
    """Evaluate rules at the module level.

    Used for: SC-004 (INVALID_RESULT sentinel).

    Config fields:
        check: Check configuration dict
        message_template: Template string
    """

    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> list[Finding]:
        """Run module-level checks."""
        b_continue = True
        findings: list[Finding] = []
        a_check = a_config.get("check", {})
        a_message_template = a_config.get("message_template", "")
        a_check_type = a_check.get("type", "")
        if b_continue and a_check_type == "sentinel_exists":
            a_sentinel_name = a_check.get("sentinel_name", "INVALID_RESULT")
            a_condition = a_check.get("condition", "")
            if b_continue and a_condition == "module_has_result_returning_functions":
                if b_continue and not _has_sentinel(a_tree, a_sentinel_name):
                    if b_continue and _has_result_returning_functions(a_tree):
                        a_ctx = {"sentinel": a_sentinel_name, "name": a_sentinel_name}
                        a_msg = self._render_message(a_message_template, a_ctx)
                        findings.append(
                            Finding(
                                rule_id=a_rule.get("lineage_id", ""),
                                file="",
                                line=1,
                                col=0,
                                message=a_msg,
                            )
                        )
        return findings


def _has_sentinel(a_tree: ast.AST, a_name: str) -> bool:
    """Check if a module-level assignment with the given name exists."""
    b_continue = True
    result = False
    for a_node in ast.iter_child_nodes(a_tree):
        if b_continue and isinstance(a_node, ast.Assign):
            for a_target in a_node.targets:
                if (
                    b_continue
                    and isinstance(a_target, ast.Name)
                    and a_target.id == a_name
                ):
                    b_continue = False
                    result = True
        if b_continue and isinstance(a_node, ast.AnnAssign):
            if (
                b_continue
                and isinstance(a_node.target, ast.Name)
                and a_node.target.id == a_name
            ):
                b_continue = False
                result = True
    return result


def _has_result_returning_functions(a_tree: ast.AST) -> bool:
    """Check if any function in the module has a Result return type annotation."""
    b_continue = True
    result = False
    for a_node in ast.walk(a_tree):
        if b_continue and isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if b_continue and a_node.returns is not None:
                a_ret_str = ast.dump(a_node.returns)
                if b_continue and "Result" in a_ret_str:
                    b_continue = False
                    result = True
    return result
