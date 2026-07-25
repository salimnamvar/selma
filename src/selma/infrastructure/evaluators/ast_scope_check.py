"""AstScopeCheckEvaluator — check variable patterns within function scope."""

from __future__ import annotations

import ast
from typing import Any

from selma.domain.entities.finding import Finding
from selma.infrastructure.evaluators.base import EvaluatorBase


class AstScopeCheckEvaluator(EvaluatorBase):
    """Evaluate rules by checking variable patterns in function scope.

    Used for: SC-011 (b_continue rules).

    Config fields:
        root_node: Node type to iterate (e.g. "FunctionDef")
        check: Variable pattern check configuration
        message_template: Template string
    """

    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> list[Finding]:
        """Check variable patterns within function scope."""
        b_continue = True
        findings: list[Finding] = []
        a_root_node = a_config.get("root_node", "FunctionDef")
        a_check = a_config.get("check", {})
        a_message_template = a_config.get("message_template", "")
        a_exemptions = a_rule.get("parameters", {})
        for a_node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self._node_name(a_node) != a_root_node:
                b_continue = False
            if b_continue and a_exemptions.get("exempt_dunders", False):
                a_name = getattr(a_node, "name", "")
                if b_continue and self._is_dunder(a_name):
                    b_continue = False
            if b_continue:
                violations = self._check_variable_rules(a_node, a_check)
                for a_violation in violations:
                    a_ctx = {
                        "root.name": getattr(a_node, "name", "<unknown>"),
                        "name": getattr(a_node, "name", "<unknown>"),
                        "violation_type": a_violation,
                    }
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
    def _check_variable_rules(
        a_node: ast.AST,
        a_check: dict[str, Any],
    ) -> list[str]:
        """Run all variable pattern rules and return list of violation types."""
        b_continue = True
        violations: list[str] = []
        a_target_name = a_check.get("target_name", "")
        a_rules = a_check.get("rules", [])
        if b_continue and not a_target_name:
            b_continue = False
        if b_continue:
            assignments = _find_assignments(a_node, a_target_name)
            usages = _find_usages(a_node, a_target_name)
            globals_used = _find_global_usage(a_node, a_target_name)
            deletes = _find_deletes(a_node, a_target_name)
            for a_rule_def in a_rules:
                b_continue_inner = True
                a_rule_name = a_rule_def.get("rule", "")
                if b_continue_inner and a_rule_name == "must_exist":
                    b_continue_inner = False
                    if not assignments:
                        violations.append("must_exist")
                if b_continue_inner and a_rule_name == "first_value_is_true":
                    b_continue_inner = False
                    if assignments and not _first_value_is_true(assignments):
                        violations.append("first_value_is_true")
                if b_continue_inner and a_rule_name == "no_reset_to_true":
                    b_continue_inner = False
                    if not _no_reset_to_true(assignments):
                        violations.append("no_reset_to_true")
                if b_continue_inner and a_rule_name == "used_in_guard":
                    b_continue_inner = False
                    if assignments and not _used_in_guard(a_node, a_target_name):
                        violations.append("used_in_guard")
                if b_continue_inner and a_rule_name == "not_as_parameter":
                    b_continue_inner = False
                    if _used_as_parameter(a_node, a_target_name):
                        violations.append("not_as_parameter")
                if b_continue_inner and a_rule_name == "not_global":
                    b_continue_inner = False
                    if globals_used:
                        violations.append("not_global")
                if b_continue_inner and a_rule_name == "not_attribute":
                    b_continue_inner = False
                    if _used_as_attribute(a_node, a_target_name):
                        violations.append("not_attribute")
                if b_continue_inner and a_rule_name == "not_deleted":
                    b_continue_inner = False
                    if deletes:
                        violations.append("not_deleted")
                if b_continue_inner and a_rule_name == "bool_assignment_only":
                    b_continue_inner = False
                    if not _all_bool_assignments(assignments):
                        violations.append("bool_assignment_only")
        return violations


def _find_assignments(a_node: ast.AST, a_name: str) -> list[ast.AST]:
    """Find all assignments to a target name within a node."""
    b_continue = True
    result: list[ast.AST] = []
    if b_continue:
        for a_child in ast.walk(a_node):
            b_continue_inner = True
            if b_continue_inner and isinstance(a_child, ast.Assign):
                for a_target in a_child.targets:
                    if b_continue_inner and isinstance(a_target, ast.Name) and a_target.id == a_name:
                        b_continue_inner = False
                        result.append(a_child)
            if b_continue_inner and isinstance(a_child, ast.AugAssign):
                if b_continue_inner and isinstance(a_child.target, ast.Name) and a_child.target.id == a_name:
                    b_continue_inner = False
                    result.append(a_child)
    return result


def _find_usages(a_node: ast.AST, a_name: str) -> list[ast.AST]:
    """Find all Name loads of a target name within a node."""
    b_continue = True
    result: list[ast.AST] = []
    if b_continue:
        for a_child in ast.walk(a_node):
            if b_continue and isinstance(a_child, ast.Name) and a_child.id == a_name and isinstance(a_child.ctx, ast.Load):
                result.append(a_child)
    return result


def _find_global_usage(a_node: ast.AST, a_name: str) -> bool:
    """Check if target name is declared as global."""
    b_continue = True
    result = False
    for a_child in ast.walk(a_node):
        if b_continue and isinstance(a_child, ast.Global):
            if b_continue and a_name in a_child.names:
                b_continue = False
                result = True
    return result


def _find_deletes(a_node: ast.AST, a_name: str) -> list[ast.AST]:
    """Find all del statements targeting a name."""
    b_continue = True
    result: list[ast.AST] = []
    for a_child in ast.walk(a_node):
        if b_continue and isinstance(a_child, ast.Delete):
            for a_target in a_child.targets:
                if b_continue and isinstance(a_target, ast.Name) and a_target.id == a_name:
                    result.append(a_child)
    return result


def _first_value_is_true(a_assignments: list[ast.AST]) -> bool:
    """Check if the first assignment value is True or a true-like expression."""
    b_continue = True
    result = False
    if b_continue and not a_assignments:
        b_continue = False
        result = False
    if b_continue:
        a_first = a_assignments[0]
        a_value = None
        if isinstance(a_first, ast.Assign) and a_first.value:
            a_value = a_first.value
        if b_continue and isinstance(a_value, ast.Constant):
            b_continue = False
            result = a_value.value is True
        if b_continue and isinstance(a_value, ast.NameConstant):
            b_continue = False
            result = a_value.value is True
    return result


def _no_reset_to_true(a_assignments: list[ast.AST]) -> bool:
    """Check that b_continue is never reset to True after first assignment."""
    b_continue = True
    result = True
    a_seen_false = False
    for a_assign in a_assignments:
        if b_continue and isinstance(a_assign, ast.Assign):
            a_value = a_assign.value
            if b_continue and isinstance(a_value, ast.Constant) and a_value.value is False:
                a_seen_false = True
            if b_continue and a_seen_false and isinstance(a_value, ast.Constant) and a_value.value is True:
                b_continue = False
                result = False
    return result


def _used_in_guard(a_node: ast.AST, a_name: str) -> bool:
    """Check if target name is used in an if statement guard."""
    b_continue = True
    result = False
    for a_child in ast.iter_child_nodes(a_node):
        if b_continue and isinstance(a_child, (ast.If, ast.While)):
            a_test = a_child.test
            if b_continue and isinstance(a_test, ast.Name) and a_test.id == a_name:
                b_continue = False
                result = True
            if b_continue and isinstance(a_test, ast.BoolOp):
                for a_val in a_test.values:
                    if b_continue and isinstance(a_val, ast.Name) and a_val.id == a_name:
                        b_continue = False
                        result = True
    return result


def _used_as_parameter(a_node: ast.AST, a_name: str) -> bool:
    """Check if target name is passed as a function argument."""
    b_continue = True
    result = False
    for a_child in ast.walk(a_node):
        if b_continue and isinstance(a_child, ast.Call):
            for a_arg in a_child.args:
                if b_continue and isinstance(a_arg, ast.Name) and a_arg.id == a_name:
                    b_continue = False
                    result = True
    return result


def _used_as_attribute(a_node: ast.AST, a_name: str) -> bool:
    """Check if target name is used as obj.attr."""
    b_continue = True
    result = False
    for a_child in ast.walk(a_node):
        if b_continue and isinstance(a_child, ast.Attribute):
            if b_continue and isinstance(a_child.value, ast.Name) and a_child.value.id == a_name:
                b_continue = False
                result = True
    return result


def _all_bool_assignments(a_assignments: list[ast.AST]) -> bool:
    """Check if all assignments are boolean literals or boolean expressions."""
    b_continue = True
    result = True
    for a_assign in a_assignments:
        if b_continue and isinstance(a_assign, ast.Assign):
            a_value = a_assign.value
            if b_continue and isinstance(a_value, (ast.Constant, ast.NameConstant)):
                if b_continue and not isinstance(a_value.value, bool):
                    b_continue = False
                    result = False
            if b_continue and isinstance(a_value, ast.BoolOp):
                pass
            if b_continue and isinstance(a_value, ast.UnaryOp) and isinstance(a_value.op, ast.Not):
                pass
    return result
