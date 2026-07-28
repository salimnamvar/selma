"""AstWalkEvaluator — walk AST counting specific node types within root nodes."""

from __future__ import annotations

import ast
import re
from typing import Any
from typing import cast

from selma.domain.entities.finding import Finding
from selma.domain.value_objects.result import Result
from selma.infrastructure.evaluators.base import EvaluatorBase

# Nested scopes whose bodies must not count toward the enclosing root's walk.
_NESTED_SCOPE_TYPES: tuple[type[ast.AST], ...] = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
)


class AstWalkEvaluator(EvaluatorBase):
    """Evaluate rules by walking AST and counting node types.

    Used for: SC-001 (single exit), SC-002 (zero raise), SC-010 (function length).

    Config fields:
        root_node: Name of root node to iterate (e.g. "FunctionDef")
        root_nodes: Alternative list of root node names (e.g. FunctionDef + AsyncFunctionDef)
        walk_nodes: List of child node names to count (e.g. ["Return", "Raise"])
        walk_config: Additional configuration (e.g. exit_call_names)
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
    ) -> Result[list[Finding]]:
        """Walk AST counting specific node types within root nodes."""
        findings: list[Finding] = []
        root_names = self._resolve_root_names(a_config)
        walk_nodes_raw: object = a_config.get("walk_nodes", [])
        walk_nodes: list[str] = []
        if isinstance(walk_nodes_raw, list):
            walk_nodes = [str(item) for item in cast("list[object]", walk_nodes_raw)]
        walk_config_obj: object = a_config.get("walk_config", {})
        walk_config: dict[str, Any] = (
            cast("dict[str, Any]", walk_config_obj)
            if isinstance(walk_config_obj, dict)
            else {}
        )
        count_config_obj: object = a_config.get("count", {})
        count_config: dict[str, Any] = (
            cast("dict[str, Any]", count_config_obj)
            if isinstance(count_config_obj, dict)
            else {}
        )
        count_breakdown_obj: object = a_config.get("count_breakdown", {})
        count_breakdown: dict[str, str] = {}
        if isinstance(count_breakdown_obj, dict):
            raw_breakdown = cast("dict[Any, Any]", count_breakdown_obj)
            count_breakdown = {str(k): str(v) for k, v in raw_breakdown.items()}
        message_template = str(a_config.get("message_template", "") or "")
        threshold_value = count_config.get("value", 0)
        threshold_op = str(count_config.get("operator", "gt") or "gt")
        scope_filters = self._as_str_dict(a_config.get("scope_filters", {}))
        # Also accept scope filters nested under walk_config (legacy).
        for key, value in self._as_str_dict(walk_config.get("scope_filters", {})).items():
            if key not in scope_filters:
                scope_filters[key] = value
        for node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self.node_name(node) not in root_names:
                b_continue = False
            if b_continue and self._is_root_out_of_scope(node, scope_filters):
                b_continue = False
            if b_continue:
                count = self._count_child_nodes(node, walk_nodes, walk_config)
                if b_continue and self._check_operator(
                    count, threshold_op, threshold_value
                ):
                    breakdown = self._build_breakdown(node, walk_nodes, count_breakdown)
                    ctx = self._build_context(node, count, breakdown)
                    msg = self._render_message(message_template, ctx)
                    findings.append(
                        Finding(
                            rule_id=str(a_rule.get("lineage_id", "") or ""),
                            file="",
                            line=self._get_line(node),
                            col=self._get_col(node),
                            message=msg,
                        )
                    )
        return Result.success(findings)

    @staticmethod
    def _as_str_dict(a_value: object) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if isinstance(a_value, dict):
            mapping = cast("dict[Any, Any]", a_value)
            for key in mapping:
                result[str(key)] = mapping[key]
        return result

    @staticmethod
    def _is_root_out_of_scope(a_node: ast.AST, a_filters: dict[str, Any]) -> bool:
        """Universal language-scope filters (not project paths).

        Config keys (all optional lists/bools):
          exclude_name_matches: regexes for function names (e.g. dunders)
          exclude_name_equals: exact function names (language protocol methods)
          exclude_decorators: decorator simple names (property, abstractmethod, ...)
          exclude_if_contains_nodes: AST type names that mark generators etc.
        """
        b_continue = True
        result = False
        name = str(getattr(a_node, "name", "") or "")

        if b_continue:
            for pattern in _as_str_list(a_filters.get("exclude_name_matches")):
                if re.search(pattern, name):
                    b_continue = False
                    result = True

        if b_continue:
            equals = set(_as_str_list(a_filters.get("exclude_name_equals")))
            if name in equals:
                b_continue = False
                result = True

        if b_continue:
            for dec_name in _as_str_list(a_filters.get("exclude_decorators")):
                if EvaluatorBase.has_decorator(a_node, dec_name):
                    b_continue = False
                    result = True

        if b_continue:
            node_types = set(_as_str_list(a_filters.get("exclude_if_contains_nodes")))
            if node_types:
                for child in AstWalkEvaluator._iter_own_scope_nodes(a_node):
                    if EvaluatorBase.node_name(child) in node_types:
                        b_continue = False
                        result = True
                        break
        return result

    @staticmethod
    def _resolve_root_names(a_config: dict[str, Any]) -> set[str]:
        """Resolve root_node and/or root_nodes into a set of AST type names."""
        names: set[str] = set()
        single = a_config.get("root_node")
        if single is not None and str(single):
            names.add(str(single))
        multi_raw: object = a_config.get("root_nodes", [])
        if isinstance(multi_raw, list):
            for item in cast("list[object]", multi_raw):
                text = str(item)
                if text:
                    names.add(text)
        return names

    @staticmethod
    def _get_call_full_name(a_node: ast.Call) -> str:
        func = a_node.func
        b_continue = True
        result = ""
        if b_continue and isinstance(func, ast.Name):
            result = func.id
            b_continue = False
        if b_continue and isinstance(func, ast.Attribute):
            parts: list[str] = []
            current: ast.AST = func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            result = ".".join(reversed(parts))
        return result

    @staticmethod
    def _get_call_simple_name(a_node: ast.Call) -> str:
        func = a_node.func
        b_continue = True
        result = ""
        if b_continue and isinstance(func, ast.Name):
            result = func.id
            b_continue = False
        if b_continue and isinstance(func, ast.Attribute):
            result = func.attr
        return result

    @staticmethod
    def _iter_own_scope_nodes(a_root: ast.AST) -> list[ast.AST]:
        """Yield descendants of a_root excluding nested function/class/lambda bodies.

        Counts only control flow belonging to this root (single-exit / zero-raise
        semantics for the function under inspection). Nested defs are evaluated
        when they themselves are roots.
        """
        collected: list[ast.AST] = []
        stack: list[ast.AST] = list(ast.iter_child_nodes(a_root))
        while stack:
            child = stack.pop()
            collected.append(child)
            if isinstance(child, _NESTED_SCOPE_TYPES):
                continue
            stack.extend(list(ast.iter_child_nodes(child)))
        return collected

    @staticmethod
    def _count_child_nodes(
        a_node: ast.AST,
        a_walk_nodes: list[str],
        a_walk_config: dict[str, Any],
    ) -> int:
        """Count matching child nodes within a root node (own scope only)."""
        count = 0
        exit_call_names: list[str] = []
        raw_exit_calls: object = a_walk_config.get("exit_call_names", [])
        if isinstance(raw_exit_calls, list):
            for item in cast("list[object]", raw_exit_calls):
                exit_call_names.append(str(item))
        for child in AstWalkEvaluator._iter_own_scope_nodes(a_node):
            b_continue = True
            if b_continue and EvaluatorBase.node_name(child) in a_walk_nodes:
                count += 1
                b_continue = False
            if b_continue and exit_call_names and isinstance(child, ast.Call):
                full_name = AstWalkEvaluator._get_call_full_name(child)
                simple_name = AstWalkEvaluator._get_call_simple_name(child)
                if full_name in exit_call_names or simple_name in exit_call_names:
                    count += 1
        return count

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
            for child in AstWalkEvaluator._iter_own_scope_nodes(a_node):
                name = EvaluatorBase.node_name(child)
                if name in a_count_breakdown:
                    parts.append(a_count_breakdown[name])
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
        name = getattr(a_node, "name", "<unknown>")
        result: dict[str, Any] = {
            "root.name": name,
            "name": name,
            "count": a_count,
            "breakdown": a_breakdown,
        }
        return result


def _as_str_list(a_value: object) -> list[str]:
    result: list[str] = []
    if a_value is None:
        result = []
    elif isinstance(a_value, str):
        result = [a_value]
    elif isinstance(a_value, list):
        result = [str(item) for item in cast("list[object]", a_value)]
    elif isinstance(a_value, tuple):
        result = [str(item) for item in cast("tuple[object, ...]", a_value)]
    else:
        result = [str(a_value)]
    return result
