"""AstWalkEvaluator — walk AST counting specific node types within root nodes."""

from __future__ import annotations

import ast
from typing import Any
from typing import cast

from selma.domain.entities.finding import Finding
from selma.domain.value_objects.result import Result
from selma.infrastructure.evaluators.base import EvaluatorBase


class AstWalkEvaluator(EvaluatorBase):
    """Evaluate rules by walking AST and counting node types.

    Used for: SC-001 (single exit), SC-002 (zero raise), SC-010 (function length).

    Config fields:
        root_node: Name of root node to iterate (e.g. "FunctionDef")
        walk_nodes: List of child node names to count (e.g. ["Return", "Raise"])
        walk_config: Exclusion flags (exclude_nested_functions, exclude_dunders, etc.)
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
        b_continue = True
        findings: list[Finding] = []
        root_node = str(a_config.get("root_node", "") or "")
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
        # Merge rule parameters into config so exempt_* flags apply.
        exclusion_config: dict[str, Any] = dict(a_config)
        params_obj: object = a_rule.get("parameters", {})
        if isinstance(params_obj, dict):
            params_map = cast("dict[str, Any]", params_obj)
            exclusion_config["parameters"] = params_map
            for key, value in params_map.items():
                if key not in exclusion_config:
                    exclusion_config[key] = value
        for node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self.node_name(node) != root_node:
                b_continue = False
            if b_continue and self._is_excluded(node, walk_config, exclusion_config):
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
    def _flag_enabled(
        a_walk_config: dict[str, Any],
        a_config: dict[str, Any],
        a_walk_key: str,
        a_config_key: str,
    ) -> bool:
        """Resolve exclusion flag from walk_config, config, or parameters."""
        b_continue = True
        result = False
        if b_continue and a_walk_config.get(a_walk_key, False):
            b_continue = False
            result = True
        params_raw: object = a_config.get("parameters", {})
        params: dict[str, Any] = (
            cast("dict[str, Any]", params_raw) if isinstance(params_raw, dict) else {}
        )
        if b_continue and a_config.get(a_config_key, False):
            b_continue = False
            result = True
        if b_continue and params.get(a_config_key, False):
            b_continue = False
            result = True
        return result

    @staticmethod
    def _is_excluded(
        a_node: ast.AST,
        a_walk_config: dict[str, Any],
        a_config: dict[str, Any],
    ) -> bool:
        """Check if a root node should be excluded from evaluation.

        Honors walk_config keys (exclude_*) and rule-level / parameters
        keys (exempt_*) so directive JSON fields are applied consistently.
        """
        b_continue = True
        result = False
        name = getattr(a_node, "name", "")
        if b_continue and AstWalkEvaluator._flag_enabled(
            a_walk_config, a_config, "exclude_dunders", "exempt_dunders"
        ):
            if b_continue and EvaluatorBase.is_dunder(name):
                b_continue = False
                result = True
        if b_continue and AstWalkEvaluator._flag_enabled(
            a_walk_config, a_config, "exclude_generators", "exempt_generators"
        ):
            if b_continue and AstWalkEvaluator._is_generator(a_node):
                b_continue = False
                result = True
        # Structural: declarative validators via known decorator *patterns*
        # (not project-specific function-name allowlists).
        if b_continue and a_walk_config.get("exclude_decorator_names"):
            raw_names: object = a_walk_config.get("exclude_decorator_names", [])
            decorator_names: list[str] = []
            if isinstance(raw_names, list):
                for item in cast("list[object]", raw_names):
                    decorator_names.append(str(item))
            if (
                b_continue
                and decorator_names
                and isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ):
                for dec in a_node.decorator_list:
                    dec_name = ""
                    if isinstance(dec, ast.Name):
                        dec_name = dec.id
                    elif isinstance(dec, ast.Attribute):
                        dec_name = dec.attr
                    elif isinstance(dec, ast.Call):
                        if isinstance(dec.func, ast.Name):
                            dec_name = dec.func.id
                        elif isinstance(dec.func, ast.Attribute):
                            dec_name = dec.func.attr
                    if b_continue and dec_name in decorator_names:
                        b_continue = False
                        result = True
        return result

    @staticmethod
    def _is_generator(a_node: ast.AST) -> bool:
        """Check if a FunctionDef is a generator (contains yield)."""
        b_continue = True
        result = False
        if b_continue and not isinstance(
            a_node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            b_continue = False
            result = False
        if b_continue:
            for child in ast.walk(a_node):
                if b_continue and isinstance(child, (ast.Yield, ast.YieldFrom)):
                    b_continue = False
                    result = True
        return result

    @staticmethod
    def _count_child_nodes(
        a_node: ast.AST,
        a_walk_nodes: list[str],
        a_walk_config: dict[str, Any],
    ) -> int:
        """Count matching child nodes within a root node, respecting exclusions."""
        b_continue = True
        count = 0
        exclude_nested = a_walk_config.get("exclude_nested_functions", False)
        for child in ast.walk(a_node):
            b_continue = True
            if b_continue and exclude_nested and isinstance(child, ast.FunctionDef):
                b_continue = False
            if (
                b_continue
                and exclude_nested
                and isinstance(child, ast.AsyncFunctionDef)
            ):
                b_continue = False
            if b_continue and EvaluatorBase.node_name(child) in a_walk_nodes:
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
            for child in ast.walk(a_node):
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
