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
        root_node = a_config.get("root_node", "FunctionDef")
        check = a_config.get("check", {})
        message_template = a_config.get("message_template", "")
        exemptions = a_rule.get("parameters", {})
        for node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self.node_name(node) != root_node:
                b_continue = False
            if b_continue and exemptions.get("exempt_dunders", False):
                name = getattr(node, "name", "")
                if b_continue and self.is_dunder(name):
                    b_continue = False
            if b_continue:
                violations = self._check_variable_rules(node, check)
                for violation in violations:
                    ctx = {
                        "root.name": getattr(node, "name", "<unknown>"),
                        "name": getattr(node, "name", "<unknown>"),
                        "violation_type": violation,
                    }
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
    def _check_variable_rules(
        a_node: ast.AST,
        a_check: dict[str, Any],
    ) -> list[str]:
        """Run all variable pattern rules and return list of violation types."""
        b_continue = True
        violations: list[str] = []
        target_name = a_check.get("target_name", "")
        rules = a_check.get("rules", [])
        if b_continue and not target_name:
            b_continue = False
        if b_continue:
            assignments = _find_assignments(a_node, target_name)
            globals_used = _find_global_usage(a_node, target_name)
            deletes = _find_deletes(a_node, target_name)
            for rule_def in rules:
                b_continue_inner = True
                rule_name = rule_def.get("rule", "")
                if b_continue_inner and rule_name == "must_exist":
                    b_continue_inner = False
                    if not assignments:
                        violations.append("must_exist")
                if b_continue_inner and rule_name == "first_value_is_true":
                    b_continue_inner = False
                    if assignments and not _first_value_is_true(assignments):
                        violations.append("first_value_is_true")
                if b_continue_inner and rule_name == "no_reset_to_true":
                    b_continue_inner = False
                    if not _no_reset_to_true(assignments):
                        violations.append("no_reset_to_true")
                if b_continue_inner and rule_name == "used_in_guard":
                    b_continue_inner = False
                    if assignments and not _used_in_guard(a_node, target_name):
                        violations.append("used_in_guard")
                if b_continue_inner and rule_name == "not_as_parameter":
                    b_continue_inner = False
                    if _used_as_parameter(a_node, target_name):
                        violations.append("not_as_parameter")
                if b_continue_inner and rule_name == "not_global":
                    b_continue_inner = False
                    if globals_used:
                        violations.append("not_global")
                if b_continue_inner and rule_name == "not_attribute":
                    b_continue_inner = False
                    if _used_as_attribute(a_node, target_name):
                        violations.append("not_attribute")
                if b_continue_inner and rule_name == "not_deleted":
                    b_continue_inner = False
                    if deletes:
                        violations.append("not_deleted")
                if b_continue_inner and rule_name == "bool_assignment_only":
                    b_continue_inner = False
                    if not _all_bool_assignments(assignments):
                        violations.append("bool_assignment_only")
        return violations


def _find_assignments(a_node: ast.AST, a_name: str) -> list[ast.AST]:
    """Find all assignments to a target name within a node."""
    b_continue = True
    result: list[ast.AST] = []
    if b_continue:
        for child in ast.walk(a_node):
            b_continue_inner = True
            if b_continue_inner and isinstance(child, ast.Assign):
                for target in child.targets:
                    if (
                        b_continue_inner
                        and isinstance(target, ast.Name)
                        and target.id == a_name
                    ):
                        b_continue_inner = False
                        result.append(child)
            if b_continue_inner and isinstance(child, ast.AugAssign):
                if (
                    b_continue_inner
                    and isinstance(child.target, ast.Name)
                    and child.target.id == a_name
                ):
                    b_continue_inner = False
                    result.append(child)
    return result


def _find_global_usage(a_node: ast.AST, a_name: str) -> bool:
    """Check if target name is declared as global."""
    b_continue = True
    result = False
    for child in ast.walk(a_node):
        if b_continue and isinstance(child, ast.Global):
            if b_continue and a_name in child.names:
                b_continue = False
                result = True
    return result


def _find_deletes(a_node: ast.AST, a_name: str) -> list[ast.AST]:
    """Find all del statements targeting a name."""
    b_continue = True
    result: list[ast.AST] = []
    for child in ast.walk(a_node):
        if b_continue and isinstance(child, ast.Delete):
            for target in child.targets:
                if b_continue and isinstance(target, ast.Name) and target.id == a_name:
                    result.append(child)
    return result


def _first_value_is_true(a_assignments: list[ast.AST]) -> bool:
    """Check if the first assignment value is True or a true-like expression."""
    b_continue = True
    result = False
    if b_continue and not a_assignments:
        b_continue = False
        result = False
    if b_continue:
        first = a_assignments[0]
        value = None
        if isinstance(first, ast.Assign) and first.value:
            value = first.value
        if b_continue and isinstance(value, ast.Constant):
            b_continue = False
            result = value.value is True
    return result


def _no_reset_to_true(a_assignments: list[ast.AST]) -> bool:
    """Check that b_continue is never reset to True after first assignment."""
    b_continue = True
    result = True
    seen_false = False
    for assign in a_assignments:
        if b_continue and isinstance(assign, ast.Assign):
            value = assign.value
            if b_continue and isinstance(value, ast.Constant) and value.value is False:
                seen_false = True
            if (
                b_continue
                and seen_false
                and isinstance(value, ast.Constant)
                and value.value is True
            ):
                b_continue = False
                result = False
    return result


def _used_in_guard(a_node: ast.AST, a_name: str) -> bool:
    """Check if target name is used in an if statement guard."""
    b_continue = True
    result = False
    for child in ast.iter_child_nodes(a_node):
        if b_continue and isinstance(child, (ast.If, ast.While)):
            test = child.test
            if b_continue and isinstance(test, ast.Name) and test.id == a_name:
                b_continue = False
                result = True
            if b_continue and isinstance(test, ast.BoolOp):
                for val in test.values:
                    if b_continue and isinstance(val, ast.Name) and val.id == a_name:
                        b_continue = False
                        result = True
    return result


def _used_as_parameter(a_node: ast.AST, a_name: str) -> bool:
    """Check if target name is passed as a function argument."""
    b_continue = True
    result = False
    for child in ast.walk(a_node):
        if b_continue and isinstance(child, ast.Call):
            for arg in child.args:
                if b_continue and isinstance(arg, ast.Name) and arg.id == a_name:
                    b_continue = False
                    result = True
    return result


def _used_as_attribute(a_node: ast.AST, a_name: str) -> bool:
    """Check if target name is used as obj.attr."""
    b_continue = True
    result = False
    for child in ast.walk(a_node):
        if b_continue and isinstance(child, ast.Attribute):
            if (
                b_continue
                and isinstance(child.value, ast.Name)
                and child.value.id == a_name
            ):
                b_continue = False
                result = True
    return result


def _all_bool_assignments(a_assignments: list[ast.AST]) -> bool:
    """Check if all assignments are boolean literals or boolean expressions."""
    b_continue = True
    result = True
    for assign in a_assignments:
        if b_continue and isinstance(assign, ast.Assign):
            value = assign.value
            if b_continue and isinstance(value, ast.Constant):
                if b_continue and not isinstance(value.value, bool):
                    b_continue = False
                    result = False
            if b_continue and isinstance(value, ast.BoolOp):
                pass
            if (
                b_continue
                and isinstance(value, ast.UnaryOp)
                and isinstance(value.op, ast.Not)
            ):
                pass
    return result
