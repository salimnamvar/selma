"""AstCallCheckEvaluator — check function calls for forbidden or dangerous patterns."""

from __future__ import annotations

import ast
from typing import Any

from selma.domain.entities.finding import Finding
from selma.infrastructure.evaluators.base import EvaluatorBase


class AstCallCheckEvaluator(EvaluatorBase):
    """Evaluate rules by checking function calls.

    Used for: SC-071 (deterministic execution), SC-104 (no eval/exec),
    SC-101 (parameterized queries).

    Config fields:
        forbidden_calls: List of {module, method} dicts
        forbidden_functions: List of bare function names
        target_methods: Method names to check on cursor objects
        check_first_arg: Conditions on the first argument
        exempt_if: Conditions that exempt a violation
        message_template: Template string
    """

    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> list[Finding]:
        """Check function calls for forbidden patterns."""
        b_continue = True
        findings: list[Finding] = []
        a_forbidden_calls = a_config.get("forbidden_calls", [])
        a_forbidden_functions = a_config.get("forbidden_functions", [])
        a_target_methods = a_config.get("target_methods", [])
        a_check_first_arg = a_config.get("check_first_arg", {})
        a_exempt_if = a_config.get("exempt_if", {})
        a_message_template = a_config.get("message_template", "")
        for a_node in ast.walk(a_tree):
            b_continue = True
            if b_continue and not isinstance(a_node, ast.Call):
                b_continue = False
            if b_continue and self._is_exempt_call(a_node, a_exempt_if, a_tree):
                b_continue = False
            if b_continue and a_forbidden_calls:
                a_match = self._check_forbidden_module_call(a_node, a_forbidden_calls)
                if b_continue and a_match:
                    a_ctx = {"module": a_match[0], "method": a_match[1], "function": f"{a_match[0]}.{a_match[1]}"}
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
                    b_continue = False
            if b_continue and a_forbidden_functions:
                a_func_name = self._get_call_name(a_node)
                if b_continue and a_func_name in a_forbidden_functions:
                    a_ctx = {"function": a_func_name, "module": "", "method": a_func_name}
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
                    b_continue = False
            if b_continue and a_target_methods and a_check_first_arg:
                a_method = self._get_method_name(a_node)
                if b_continue and a_method in a_target_methods:
                    if b_continue and self._first_arg_violates(a_node, a_check_first_arg):
                        a_ctx = {"function": a_method, "module": "", "method": a_method}
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
    def _is_exempt_call(
        a_node: ast.Call,
        a_exempt_if: dict[str, Any],
        a_tree: ast.AST,
    ) -> bool:
        """Check if a call node is exempt based on exemption rules."""
        b_continue = True
        result = False
        a_param_names = a_exempt_if.get("function_has_parameter_named", [])
        if b_continue and a_param_names:
            a_enclosing = _find_enclosing_function(a_node, a_tree)
            if b_continue and a_enclosing is not None:
                a_args = _get_function_param_names(a_enclosing)
                for a_pname in a_args:
                    if b_continue and a_pname in a_param_names:
                        b_continue = False
                        result = True
        return result

    @staticmethod
    def _check_forbidden_module_call(
        a_node: ast.Call,
        a_forbidden_calls: list[dict[str, str]],
    ) -> tuple[str, str] | None:
        """Check if a call matches a forbidden module.method pattern."""
        b_continue = True
        result: tuple[str, str] | None = None
        if b_continue and isinstance(a_node.func, ast.Attribute):
            a_method = a_node.func.attr
            a_module = _resolve_module_name(a_node.func.value)
            if b_continue and a_module:
                for a_forbidden in a_forbidden_calls:
                    if b_continue and a_forbidden.get("module") == a_module and a_forbidden.get("method") == a_method:
                        b_continue = False
                        result = (a_module, a_method)
        return result

    @staticmethod
    def _get_call_name(a_node: ast.Call) -> str:
        """Get the bare function name from a Call node."""
        b_continue = True
        result = ""
        if b_continue and isinstance(a_node.func, ast.Name):
            b_continue = False
            result = a_node.func.id
        if b_continue and isinstance(a_node.func, ast.Attribute):
            b_continue = False
            result = a_node.func.attr
        return result

    @staticmethod
    def _get_method_name(a_node: ast.Call) -> str:
        """Get the method name from a Call node (obj.method())."""
        b_continue = True
        result = ""
        if b_continue and isinstance(a_node.func, ast.Attribute):
            b_continue = False
            result = a_node.func.attr
        return result

    @staticmethod
    def _first_arg_violates(
        a_node: ast.Call,
        a_check: dict[str, bool],
    ) -> bool:
        """Check if the first argument of a call violates safety rules."""
        b_continue = True
        result = False
        if b_continue and not a_node.args:
            b_continue = False
            result = False
        if b_continue:
            a_first = a_node.args[0]
            if b_continue and a_check.get("forbid_fstring", False):
                if b_continue and isinstance(a_first, ast.JoinedStr):
                    b_continue = False
                    result = True
            if b_continue and a_check.get("forbid_format_call", False):
                if b_continue and isinstance(a_first, ast.Call) and isinstance(a_first.func, ast.Attribute):
                    if b_continue and a_first.func.attr == "format":
                        b_continue = False
                        result = True
            if b_continue and a_check.get("forbid_percent_format", False):
                if b_continue and isinstance(a_first, ast.BinOp) and isinstance(a_first.op, ast.Mod):
                    b_continue = False
                    result = True
            if b_continue and a_check.get("forbid_string_concat", False):
                if b_continue and isinstance(a_first, ast.BinOp) and isinstance(a_first.op, ast.Add):
                    b_continue = False
                    result = True
        return result


def _resolve_module_name(a_node: ast.AST) -> str:
    """Resolve the module name from an attribute chain (e.g. datetime.datetime.now -> datetime)."""
    b_continue = True
    result = ""
    if b_continue and isinstance(a_node, ast.Name):
        b_continue = False
        result = a_node.id
    if b_continue and isinstance(a_node, ast.Attribute):
        b_continue = False
        parts = []
        current: ast.AST = a_node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        parts.reverse()
        if len(parts) >= 2:
            result = parts[0]
        else:
            result = parts[0] if parts else ""
    return result


def _find_enclosing_function(a_node: ast.AST, a_tree: ast.AST) -> ast.FunctionDef | None:
    """Find the enclosing FunctionDef for a given node by walking parent references."""
    b_continue = True
    result: ast.FunctionDef | None = None
    for a_parent in ast.walk(a_tree):
        if b_continue and isinstance(a_parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for a_child in ast.walk(a_parent):
                if b_continue and a_child is a_node:
                    b_continue = False
                    result = a_parent
    return result


def _get_function_param_names(a_func: ast.FunctionDef) -> list[str]:
    """Get the parameter names of a FunctionDef."""
    b_continue = True
    result: list[str] = []
    if b_continue:
        for a_arg in a_func.args.args:
            result.append(a_arg.arg)
        for a_arg in a_func.args.posonlyargs:
            result.append(a_arg.arg)
        if a_func.args.vararg:
            result.append(a_func.args.vararg.arg)
        for a_arg in a_func.args.kwonlyargs:
            result.append(a_arg.arg)
        if a_func.args.kwarg:
            result.append(a_func.args.kwarg.arg)
    return result
