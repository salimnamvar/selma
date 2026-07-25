"""AST evaluator: interprets JSON rule configs against Python AST nodes.

This is the core engine that translates JSON rule definitions into
AST operations. Each evaluator type knows how to walk/match/count
specific AST patterns.
"""

from __future__ import annotations

import ast
import re
from typing import Any


class AstEvaluator:
    """Interpret JSON evaluator_config against a Python AST.

    Supports evaluator types:
    - ast_walk: Walk AST counting specific node types
    - ast_node_match: Match AST nodes with conditions
    - ast_scope_check: Check variable patterns in scope
    - ast_call_check: Check function calls
    - ast_context_check: Check parent context
    - ast_module_check: Module-level checks
    - regex: Text pattern matching on source
    """

    def evaluate(
        self,
        a_tree: ast.AST,
        a_evaluator_type: str,
        a_config: dict[str, Any],
        a_source: str = "",
    ) -> list[dict[str, Any]]:
        """Evaluate a rule config against an AST.

        Returns list of violation dicts: {line, col, message}
        """
        match a_evaluator_type:
            case "ast_walk":
                return self._eval_ast_walk(a_tree, a_config)
            case "ast_node_match":
                return self._eval_ast_node_match(a_tree, a_config)
            case "ast_scope_check":
                return self._eval_ast_scope_check(a_tree, a_config)
            case "ast_call_check":
                return self._eval_ast_call_check(a_tree, a_config)
            case "ast_context_check":
                return self._eval_ast_context_check(a_tree, a_config)
            case "ast_module_check":
                return self._eval_ast_module_check(a_tree, a_config)
            case "regex":
                return self._eval_regex(a_source, a_config)
            case _:
                return []

    def _eval_ast_walk(
        self, a_tree: ast.AST, a_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Walk AST counting specific node types.

        Config:
            root_node: "FunctionDef" (node type to enter)
            walk_nodes: ["Return", "Raise"] (child types to count)
            count: {"operator": "gt", "value": 1} (threshold)
            message_template: "Function '{name}' has {count} exit doors"
            exempt_dunders: true
            exempt_generators: true
        """
        violations: list[dict[str, Any]] = []
        root_node = a_config.get("root_node", "FunctionDef")
        walk_nodes = a_config.get("walk_nodes", [])
        count_config = a_config.get("count", {})
        msg_template = a_config.get("message_template", "")
        exempt_dunders = a_config.get("exempt_dunders", True)
        exempt_generators = a_config.get("exempt_generators", True)

        for node in ast.walk(a_tree):
            if type(node).__name__ != root_node:
                continue

            if exempt_dunders and self._is_dunder(node):
                continue

            if exempt_generators and self._has_yield(node):
                continue

            count = self._count_child_nodes(node, walk_nodes)

            if self._check_threshold(count, count_config):
                msg = self._render_message(msg_template, node, count)
                violations.append({
                    "line": getattr(node, "lineno", 0),
                    "col": getattr(node, "col_offset", 0),
                    "message": msg,
                })

        return violations

    def _eval_ast_node_match(
        self, a_tree: ast.AST, a_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Match AST nodes with conditions.

        Config:
            target_node: "FunctionDef"
            conditions: [{"field": "name", "operator": "not_matches", "value": "^__.*__$"}]
            message_template: "..."
        """
        violations: list[dict[str, Any]] = []
        target_node = a_config.get("target_node", "FunctionDef")
        conditions = a_config.get("conditions", [])
        msg_template = a_config.get("message_template", "")

        for node in ast.walk(a_tree):
            if type(node).__name__ != target_node:
                continue

            if self._check_conditions(node, conditions):
                msg = self._render_message(msg_template, node, 0)
                violations.append({
                    "line": getattr(node, "lineno", 0),
                    "col": getattr(node, "col_offset", 0),
                    "message": msg,
                })

        return violations

    def _eval_ast_scope_check(
        self, a_tree: ast.AST, a_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Check variable patterns in function scope.

        Config:
            root_node: "FunctionDef"
            variable: "b_continue"
            rules: ["must_exist", "first_value_is_true", "used_in_guard"]
            message_template: "..."
        """
        violations: list[dict[str, Any]] = []
        root_node = a_config.get("root_node", "FunctionDef")
        variable = a_config.get("variable", "")
        rules = a_config.get("rules", [])
        msg_template = a_config.get("message_template", "")

        for node in ast.walk(a_tree):
            if type(node).__name__ != root_node:
                continue

            if self._is_dunder(node):
                continue

            scope_violations = self._check_variable_scope(
                node, variable, rules, msg_template
            )
            violations.extend(scope_violations)

        return violations

    def _eval_ast_call_check(
        self, a_tree: ast.AST, a_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Check function calls.

        Config:
            forbidden_functions: ["eval", "exec", "compile"]
            forbidden_calls: [{"module": "datetime", "method": "now"}]
            target_methods: ["execute"]
            check_first_arg: {"forbid_fstring": true}
            message_template: "..."
        """
        violations: list[dict[str, Any]] = []
        forbidden_functions = a_config.get("forbidden_functions", [])
        forbidden_calls = a_config.get("forbidden_calls", [])
        target_methods = a_config.get("target_methods", [])
        check_first_arg = a_config.get("check_first_arg", {})
        msg_template = a_config.get("message_template", "")

        for node in ast.walk(a_tree):
            if not isinstance(node, ast.Call):
                continue

            if self._check_forbidden_function(node, forbidden_functions, msg_template):
                violations.append(self._make_violation(node, msg_template))

            if self._check_forbidden_call(node, forbidden_calls, msg_template):
                violations.append(self._make_violation(node, msg_template))

            if self._check_target_method(node, target_methods, check_first_arg, msg_template):
                violations.append(self._make_violation(node, msg_template))

        return violations

    def _eval_ast_context_check(
        self, a_tree: ast.AST, a_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Check parent context (with/try).

        Config:
            target_functions: ["open", "Popen", "Lock"]
            must_be_inside: ["With"]
            or_try_finally: true
            message_template: "..."
        """
        violations: list[dict[str, Any]] = []
        target_functions = a_config.get("target_functions", [])
        msg_template = a_config.get("message_template", "")

        for node in ast.walk(a_tree):
            if not isinstance(node, ast.Call):
                continue

            func_name = self._get_call_name(node)
            if func_name not in target_functions:
                continue

            if not self._is_in_with_context(node, a_tree):
                violations.append(self._make_violation(node, msg_template))

        return violations

    def _eval_ast_module_check(
        self, a_tree: ast.AST, a_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Module-level checks.

        Config:
            sentinel_name: "INVALID_RESULT"
            condition: "module_has_result_returning_functions"
            message_template: "..."
        """
        violations: list[dict[str, Any]] = []
        sentinel_name = a_config.get("sentinel_name", "INVALID_RESULT")
        condition = a_config.get("condition", "")
        msg_template = a_config.get("message_template", "")

        if condition == "module_has_result_returning_functions":
            has_sentinel = self._check_sentinel_exists(a_tree, sentinel_name)
            has_result_return = self._check_module_has_result_return(a_tree)

            if has_result_return and not has_sentinel:
                violations.append({
                    "line": 1,
                    "col": 0,
                    "message": self._render_message(msg_template, None, 0),
                })

        return violations

    def _eval_regex(
        self, a_source: str, a_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Text pattern matching on source."""
        violations: list[dict[str, Any]] = []
        pattern = a_config.get("pattern", "")
        flags = a_config.get("flags", "")

        if not pattern:
            return violations

        re_flags = 0
        if "i" in flags:
            re_flags |= re.IGNORECASE
        if "m" in flags:
            re_flags |= re.MULTILINE

        try:
            compiled = re.compile(pattern, re_flags)
            for i, line in enumerate(a_source.split("\n"), 1):
                if compiled.search(line):
                    violations.append({
                        "line": i,
                        "col": 0,
                        "message": f"Pattern match: {pattern}",
                    })
        except re.error:
            pass

        return violations

    # --- Helper methods ---

    def _is_dunder(self, a_node: ast.AST) -> bool:
        name = getattr(a_node, "name", "")
        return name.startswith("__") and name.endswith("__")

    def _has_yield(self, a_node: ast.AST) -> bool:
        for child in ast.walk(a_node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _count_child_nodes(
        self, a_node: ast.AST, a_types: list[str]
    ) -> int:
        count = 0
        for child in ast.walk(a_node):
            if child is a_node:
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if type(child).__name__ in a_types:
                count += 1
        return count

    def _check_threshold(
        self, a_count: int, a_config: dict[str, Any]
    ) -> bool:
        op = a_config.get("operator", "gt")
        value = a_config.get("value", 0)
        match op:
            case "gt":
                return a_count > value
            case "gte":
                return a_count >= value
            case "lt":
                return a_count < value
            case "lte":
                return a_count <= value
            case "eq":
                return a_count == value
            case "neq":
                return a_count != value
        return False

    def _render_message(
        self, a_template: str, a_node: ast.AST | None, a_count: int
    ) -> str:
        if not a_template:
            return f"Violation at line {getattr(a_node, 'lineno', '?')}"
        name = getattr(a_node, "name", "")
        return a_template.replace("{name}", name).replace("{count}", str(a_count))

    def _check_conditions(
        self, a_node: ast.AST, a_conditions: list[dict[str, Any]]
    ) -> bool:
        for cond in a_conditions:
            field = cond.get("field", "")
            op = cond.get("operator", "")
            value = cond.get("value", "")

            actual = getattr(a_node, field, None)
            if actual is None:
                return False

            match op:
                case "eq":
                    if str(actual) != str(value):
                        return False
                case "neq":
                    if str(actual) == str(value):
                        return False
                case "matches":
                    if not re.search(str(value), str(actual)):
                        return False
                case "not_matches":
                    if re.search(str(value), str(actual)):
                        return False
                case "exists":
                    pass
                case "not_exists":
                    return False
        return True

    def _check_variable_scope(
        self,
        a_node: ast.FunctionDef,
        a_variable: str,
        a_rules: list[str],
        a_msg_template: str,
    ) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        assignments = []
        guards = []

        for child in ast.walk(a_node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == a_variable:
                        assignments.append(child)
            elif isinstance(child, (ast.If, ast.While)):
                if a_variable in ast.dump(child.test):
                    guards.append(child)

        if "must_exist" in a_rules and not assignments:
            violations.append({
                "line": a_node.lineno,
                "col": a_node.col_offset,
                "message": self._render_message(
                    a_msg_template or f"Function lacks {a_variable}",
                    a_node, 0,
                ),
            })

        if "first_value_is_true" in a_rules and assignments:
            first = assignments[0]
            if not (
                isinstance(first.value, ast.Constant)
                and first.value.value is True
            ):
                violations.append({
                    "line": first.lineno,
                    "col": first.col_offset,
                    "message": f"{a_variable} must be initialized to True",
                })

        if "used_in_guard" in a_rules and assignments and not guards:
            violations.append({
                "line": a_node.lineno,
                "col": a_node.col_offset,
                "message": f"{a_variable} initialized but never used as guard",
            })

        return violations

    def _check_forbidden_function(
        self,
        a_node: ast.Call,
        a_forbidden: list[str],
        a_msg_template: str,
    ) -> bool:
        if isinstance(a_node.func, ast.Name):
            return a_node.func.id in a_forbidden
        return False

    def _check_forbidden_call(
        self,
        a_node: ast.Call,
        a_forbidden: list[dict[str, str]],
        a_msg_template: str,
    ) -> bool:
        if not isinstance(a_node.func, ast.Attribute):
            return False
        if not isinstance(a_node.func.value, ast.Name):
            return False
        mod = a_node.func.value.id
        method = a_node.func.attr
        for fc in a_forbidden:
            if fc.get("module") == mod and fc.get("method") == method:
                return True
        return False

    def _check_target_method(
        self,
        a_node: ast.Call,
        a_methods: list[str],
        a_check_first_arg: dict[str, bool],
        a_msg_template: str,
    ) -> bool:
        if not isinstance(a_node.func, ast.Attribute):
            return False
        if a_node.func.attr not in a_methods:
            return False
        if not a_node.args:
            return False
        first_arg = a_node.args[0]
        if a_check_first_arg.get("forbid_fstring") and isinstance(first_arg, ast.JoinedStr):
            return True
        if a_check_first_arg.get("forbid_format_call"):
            if isinstance(first_arg, ast.Call) and isinstance(first_arg.func, ast.Attribute):
                if first_arg.func.attr == "format":
                    return True
        if a_check_first_arg.get("forbid_percent"):
            if isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Mod):
                return True
        return False

    def _get_call_name(self, a_node: ast.Call) -> str:
        if isinstance(a_node.func, ast.Name):
            return a_node.func.id
        if isinstance(a_node.func, ast.Attribute):
            return a_node.func.attr
        return ""

    def _is_in_with_context(
        self, a_node: ast.Call, a_tree: ast.AST
    ) -> bool:
        for parent in ast.walk(a_tree):
            if isinstance(parent, ast.With):
                for item in parent.items:
                    for child in ast.walk(item.context_expr):
                        if child is a_node:
                            return True
        return False

    def _check_sentinel_exists(
        self, a_tree: ast.AST, a_name: str
    ) -> bool:
        for node in ast.walk(a_tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == a_name:
                        return True
        return False

    def _check_module_has_result_return(self, a_tree: ast.AST) -> bool:
        for node in ast.walk(a_tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns:
                    ret_str = ast.dump(node.returns)
                    if "Result" in ret_str:
                        return True
        return False

    def _make_violation(
        self, a_node: ast.Call, a_msg_template: str
    ) -> dict[str, Any]:
        func_name = self._get_call_name(a_node)
        msg = a_msg_template.replace("{function}", func_name) if a_msg_template else f"Forbidden call: {func_name}()"
        return {
            "line": getattr(a_node, "lineno", 0),
            "col": getattr(a_node, "col_offset", 0),
            "message": msg,
        }
