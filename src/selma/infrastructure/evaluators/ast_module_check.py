"""AstModuleCheckEvaluator — module-level checks (sentinels, imports, globals)."""

from __future__ import annotations

import ast
from typing import Any

from selma.domain.entities.finding import Finding
from selma.domain.value_objects.result import Result
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
    ) -> Result[list[Finding]]:
        """Run module-level checks."""
        b_continue = True
        findings: list[Finding] = []
        check = a_config.get("check", {})
        message_template = a_config.get("message_template", "")
        check_type = check.get("type", "")
        if b_continue and check_type == "sentinel_exists":
            sentinel_name = check.get("sentinel_name", "INVALID_RESULT")
            condition = check.get("condition", "")
            if b_continue and condition == "module_has_result_returning_functions":
                if b_continue and not _has_sentinel(a_tree, sentinel_name):
                    if b_continue and _has_result_returning_functions(a_tree):
                        ctx = {"sentinel": sentinel_name, "name": sentinel_name}
                        msg = self._render_message(message_template, ctx)
                        findings.append(
                            Finding(
                                rule_id=a_rule.get("lineage_id", ""),
                                file="",
                                line=1,
                                col=0,
                                message=msg,
                            )
                        )
        return Result.success(findings)


def _has_sentinel(a_tree: ast.AST, a_name: str) -> bool:
    """Check if a module-level assignment with the given name exists."""
    b_continue = True
    result = False
    for node in ast.iter_child_nodes(a_tree):
        if b_continue and isinstance(node, ast.Assign):
            for target in node.targets:
                if b_continue and isinstance(target, ast.Name) and target.id == a_name:
                    b_continue = False
                    result = True
        if b_continue and isinstance(node, ast.AnnAssign):
            if (
                b_continue
                and isinstance(node.target, ast.Name)
                and node.target.id == a_name
            ):
                b_continue = False
                result = True
    return result


def _has_result_returning_functions(a_tree: ast.AST) -> bool:
    """Check if any function in the module has a Result return type annotation."""
    b_continue = True
    result = False
    for node in ast.walk(a_tree):
        if b_continue and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if b_continue and node.returns is not None:
                ret_str = ast.dump(node.returns)
                if b_continue and "Result" in ret_str:
                    b_continue = False
                    result = True
    return result
