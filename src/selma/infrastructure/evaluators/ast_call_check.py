"""AstCallCheckEvaluator — check function calls for forbidden or dangerous patterns."""

from __future__ import annotations

import ast
from typing import Any

from selma.domain.entities.finding import Finding
from selma.domain.value_objects.result import Result
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
        message_template: Template string

    No call-site exemptions: every matching call is a finding.
    """

    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> Result[list[Finding]]:
        """Check function calls for forbidden patterns."""
        findings: list[Finding] = []
        forbidden_calls = a_config.get("forbidden_calls", [])
        forbidden_functions = a_config.get("forbidden_functions", [])
        target_methods = a_config.get("target_methods", [])
        check_first_arg = a_config.get("check_first_arg", {})
        message_template = a_config.get("message_template", "")
        for node in ast.walk(a_tree):
            if not isinstance(node, ast.Call):
                continue
            b_continue = True
            if b_continue and forbidden_calls:
                match = self._check_forbidden_module_call(node, forbidden_calls)
                if b_continue and match is not None:
                    module_name, method_name = match.split(".", 1)
                    ctx = {
                        "module": module_name,
                        "method": method_name,
                        "function": match,
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
                    b_continue = False
            if b_continue and forbidden_functions:
                func_name = self._get_call_name(node)
                if b_continue and func_name in forbidden_functions:
                    ctx = {
                        "function": func_name,
                        "module": "",
                        "method": func_name,
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
                    b_continue = False
            if b_continue and target_methods and check_first_arg:
                method = self._get_method_name(node)
                if b_continue and method in target_methods:
                    if b_continue and self._first_arg_violates(node, check_first_arg):
                        ctx = {"function": method, "module": "", "method": method}
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
        return Result.success(findings)

    @staticmethod
    def _check_forbidden_module_call(
        a_node: ast.Call,
        a_forbidden_calls: list[dict[str, str]],
    ) -> str | None:
        """Check if a call matches a forbidden module.method pattern.

        Returns 'module.method' on match, else None.
        """
        b_continue = True
        result: str | None = None
        if b_continue and isinstance(a_node.func, ast.Attribute):
            method = a_node.func.attr
            module = _resolve_module_name(a_node.func.value)
            if b_continue and module:
                for forbidden in a_forbidden_calls:
                    if (
                        b_continue
                        and forbidden.get("module") == module
                        and forbidden.get("method") == method
                    ):
                        b_continue = False
                        result = f"{module}.{method}"
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
    def _get_module_method_name(a_node: ast.Call) -> str:
        """Get the module.method name from a Call node (e.g. 're.compile')."""
        b_continue = True
        result = ""
        if b_continue and isinstance(a_node.func, ast.Attribute):
            method = a_node.func.attr
            module = _resolve_module_name(a_node.func.value)
            if b_continue and module:
                b_continue = False
                result = f"{module}.{method}"
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
            first = a_node.args[0]
            if b_continue and a_check.get("forbid_fstring", False):
                if b_continue and isinstance(first, ast.JoinedStr):
                    b_continue = False
                    result = True
            if b_continue and a_check.get("forbid_format_call", False):
                if (
                    b_continue
                    and isinstance(first, ast.Call)
                    and isinstance(first.func, ast.Attribute)
                ):
                    if b_continue and first.func.attr == "format":
                        b_continue = False
                        result = True
            if b_continue and a_check.get("forbid_percent_format", False):
                if (
                    b_continue
                    and isinstance(first, ast.BinOp)
                    and isinstance(first.op, ast.Mod)
                ):
                    b_continue = False
                    result = True
            if b_continue and a_check.get("forbid_string_concat", False):
                if (
                    b_continue
                    and isinstance(first, ast.BinOp)
                    and isinstance(first.op, ast.Add)
                ):
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
        parts: list[str] = []
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
