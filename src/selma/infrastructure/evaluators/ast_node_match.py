"""AstNodeMatchEvaluator — generic AST node matching from JSON conditions.

The engine evaluates declarative conditions only. Rule identity, thresholds,
skip lists, and type names live exclusively in rule JSON files.
"""

from __future__ import annotations

import ast
from collections.abc import Sized
import re
from typing import Any
from typing import cast

from selma.domain.entities.finding import Finding
from selma.domain.value_objects.result import Result
from selma.infrastructure.evaluators.base import EvaluatorBase


def _as_str_list(a_value: object) -> list[str]:
    b_continue = True
    result: list[str] = []
    if b_continue and a_value is None:
        b_continue = False
        result = []
    if b_continue and isinstance(a_value, str):
        b_continue = False
        result = [a_value]
    if b_continue and isinstance(a_value, list):
        b_continue = False
        values = cast("list[Any]", a_value)
        result = [str(values[i]) for i in range(len(values))]
    if b_continue and isinstance(a_value, tuple):
        b_continue = False
        values_t = cast("tuple[Any, ...]", a_value)
        result = [str(values_t[i]) for i in range(len(values_t))]
    if b_continue:
        result = [str(cast("object", a_value))]
    return result


def _as_str_set(a_value: object) -> set[str]:
    return set(_as_str_list(a_value))


def _as_dict(a_value: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(a_value, dict):
        mapping = cast("dict[Any, Any]", a_value)
        for key in mapping:
            result[str(key)] = mapping[key]
    return result


def _as_cond_list(a_value: object) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if isinstance(a_value, list):
        values = cast("list[Any]", a_value)
        for i in range(len(values)):
            result.append(_as_dict(values[i]))
    elif isinstance(a_value, tuple):
        values_t = cast("tuple[Any, ...]", a_value)
        for i in range(len(values_t)):
            result.append(_as_dict(values_t[i]))
    return [entry for entry in result if entry]


class AstNodeMatchEvaluator(EvaluatorBase):
    """Match AST nodes using target_node(s) + declarative conditions from config.

    Universal rules: no engine-side exemptions for dunders, properties, tests,
    or any other code section. Rule JSON alone defines match conditions.
    """

    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> Result[list[Finding]]:
        findings: list[Finding] = []
        target_names = self._resolve_target_names(a_config)
        conditions = _as_cond_list(a_config.get("conditions", []))
        message_template = str(a_config.get("message_template", ""))
        params_obj: object = a_rule.get("parameters")
        parameters = _as_dict(params_obj)
        lineage_id = str(a_rule.get("lineage_id", ""))
        ctx_base: dict[str, Any] = {"tree": a_tree, "parameters": parameters}

        for node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self.node_name(node) not in target_names:
                b_continue = False
            if b_continue and not self._all_conditions_match(
                node, conditions, ctx_base, a_depth=0, a_max_depth=64
            ):
                b_continue = False
            if b_continue:
                ctx = self._build_context(node)
                msg = self._render_message(message_template, ctx)
                findings.append(
                    Finding(
                        rule_id=lineage_id,
                        file="",
                        line=self._get_line(node),
                        col=self._get_col(node),
                        message=msg,
                    )
                )
        return Result.success(findings)

    @staticmethod
    def _resolve_target_names(a_config: dict[str, Any]) -> set[str]:
        """Resolve target_node and/or target_nodes into a set of AST type names."""
        names: set[str] = set()
        single = a_config.get("target_node")
        if single is not None and str(single):
            names.add(str(single))
        multi_raw: object = a_config.get("target_nodes", [])
        if isinstance(multi_raw, list):
            for item in cast("list[object]", multi_raw):
                text = str(item)
                if text:
                    names.add(text)
        return names

    @staticmethod
    def _all_conditions_match(
        a_node: ast.AST,
        a_conditions: list[dict[str, Any]],
        a_ctx: dict[str, Any],
        a_depth: int = 0,
        a_max_depth: int = 64,
    ) -> bool:
        b_continue = True
        result = True
        if a_depth >= a_max_depth:
            b_continue = False
            result = False
        for cond in a_conditions:
            if b_continue and not _match_condition(
                a_node,
                cond,
                a_ctx,
                a_depth=a_depth,
                a_max_depth=a_max_depth,
            ):
                b_continue = False
                result = False
        return result

    @staticmethod
    def _build_context(a_node: ast.AST) -> dict[str, Any]:
        name = getattr(a_node, "name", "<unknown>")
        return {
            "name": name,
            "root.name": name,
        }


def _match_condition(
    a_node: ast.AST,
    a_cond: dict[str, Any],
    a_ctx: dict[str, Any],
    a_depth: int = 0,
    a_max_depth: int = 64,
) -> bool:
    b_continue = True
    result = False

    if b_continue and a_depth >= a_max_depth:
        b_continue = False
        result = False

    if b_continue and "all_of" in a_cond:
        b_continue = False
        items = _as_cond_list(a_cond.get("all_of"))
        result = all(
            _match_condition(
                a_node, c, a_ctx, a_depth=a_depth + 1, a_max_depth=a_max_depth
            )
            for c in items
        )
    if b_continue and "any_of" in a_cond:
        b_continue = False
        items = _as_cond_list(a_cond.get("any_of"))
        result = any(
            _match_condition(
                a_node, c, a_ctx, a_depth=a_depth + 1, a_max_depth=a_max_depth
            )
            for c in items
        )
    if b_continue and "not" in a_cond:
        b_continue = False
        inner = a_cond.get("not")
        if not isinstance(inner, dict):
            result = False
        else:
            result = not _match_condition(
                a_node,
                _as_dict(cast("object", inner)),
                a_ctx,
                a_depth=a_depth + 1,
                a_max_depth=a_max_depth,
            )

    field = ""
    operator = ""
    value: object = ""
    field_value: Any = None
    if b_continue:
        field = str(a_cond.get("field", ""))
        operator = str(a_cond.get("operator", ""))
        value = a_cond.get("value", "")
        field_value = _resolve_field(a_node, field)

    if b_continue and operator == "exists":
        b_continue = False
        if field_value is None:
            result = False
        else:
            sized = _collection_size(field_value)
            result = True if sized is None else sized > 0
    if b_continue and operator == "not_exists":
        b_continue = False
        if field_value is None:
            result = True
        else:
            sized = _collection_size(field_value)
            result = False if sized is None else sized == 0
    if b_continue and operator in {"equals", "eq"}:
        b_continue = False
        result = str(_ast_to_comparable(field_value)) == str(value)
    if b_continue and operator in {"not_equals", "neq"}:
        b_continue = False
        result = str(_ast_to_comparable(field_value)) != str(value)
    if b_continue and operator == "matches":
        b_continue = False
        result = bool(re.search(str(value), str(_ast_to_comparable(field_value))))
    if b_continue and operator == "not_matches":
        b_continue = False
        result = not bool(re.search(str(value), str(_ast_to_comparable(field_value))))
    if b_continue and operator == "contains":
        b_continue = False
        result = str(value) in str(_ast_to_comparable(field_value))
    if b_continue and operator == "not_contains":
        b_continue = False
        result = str(value) not in str(_ast_to_comparable(field_value))
    if b_continue and operator == "contains_node":
        b_continue = False
        result = _subtree_contains_node_type(
            a_node if field in ("", ".") else field_value, str(value)
        )
    if b_continue and operator == "subtree_contains_node":
        b_continue = False
        target = a_node if field in ("", ".") else field_value
        if not isinstance(target, ast.AST):
            result = False
        else:
            result = _subtree_contains_node_type(target, str(value))
    if b_continue and operator == "unparse_matches":
        b_continue = False
        result = bool(re.search(str(value), _safe_unparse(field_value), re.IGNORECASE))
    if b_continue and operator == "unparse_not_matches":
        b_continue = False
        result = not bool(
            re.search(str(value), _safe_unparse(field_value), re.IGNORECASE)
        )
    if b_continue and operator == "unparse_contains":
        b_continue = False
        result = str(value) in _safe_unparse(field_value)
    if b_continue and operator == "unparse_not_contains":
        b_continue = False
        result = str(value) not in _safe_unparse(field_value)
    if b_continue and operator == "unparse_in":
        b_continue = False
        result = _safe_unparse(field_value) in set(_as_str_list(value))
    if b_continue and operator == "unparse_not_in":
        b_continue = False
        result = _safe_unparse(field_value) not in set(_as_str_list(value))
    if b_continue and operator == "has_mutable_defaults":
        b_continue = False
        result = _has_mutable_defaults(a_node, _as_str_set(value))
    if b_continue and operator == "params_missing_prefix":
        b_continue = False
        result = _params_missing_prefix(a_node, _as_dict(value), a_ctx.get("tree"))
    if b_continue and operator == "params_any_unannotated":
        b_continue = False
        result = _params_any_unannotated(a_node, _as_dict(value))
    if b_continue and operator == "body_contains_any":
        b_continue = False
        result = _body_contains_any(a_node, _as_str_list(value))
    if b_continue and operator == "body_not_contains_any":
        b_continue = False
        result = not _body_contains_any(a_node, _as_str_list(value))
    if b_continue and operator == "calls_own_name":
        b_continue = False
        result = _calls_own_name(a_node)
    if b_continue and operator == "param_names_intersect":
        b_continue = False
        result = bool(_param_names(a_node) & _as_str_set(value))
    if b_continue and operator == "param_names_disjoint":
        b_continue = False
        result = not bool(_param_names(a_node) & _as_str_set(value))
    if b_continue and operator == "calls_any":
        b_continue = False
        result = _calls_any(a_node, _as_dict(value))
    if b_continue and operator == "has_decorator":
        b_continue = False
        result = EvaluatorBase.has_decorator(a_node, str(value))
    if b_continue and operator == "not_has_decorator":
        b_continue = False
        result = not EvaluatorBase.has_decorator(a_node, str(value))
    if b_continue and operator == "call_message_missing_or_empty":
        b_continue = False
        result = _call_message_missing_or_empty(a_node, _as_dict(value))
    if b_continue and operator == "attr_call_on_shared_state":
        b_continue = False
        tree = a_ctx.get("tree")
        if not isinstance(tree, ast.AST):
            result = False
        else:
            result = _attr_call_on_shared_state(a_node, tree, _as_dict(value))
    if b_continue and operator == "except_type_names_intersect":
        b_continue = False
        result = bool(_except_type_names(a_node) & _as_str_set(value))
    if b_continue and operator == "except_type_names_disjoint":
        b_continue = False
        result = not bool(_except_type_names(a_node) & _as_str_set(value))
    if b_continue and operator == "except_bound_name_unused":
        b_continue = False
        result = _except_bound_name_unused(a_node, _as_str_list(value))
    if b_continue and operator == "name_not_matches_any":
        b_continue = False
        name = str(getattr(a_node, "name", ""))
        result = not any(re.search(pattern, name) for pattern in _as_str_list(value))
    if b_continue and operator == "star_import":
        b_continue = False
        result = _is_star_import(field_value if field_value is not None else a_node)
    if b_continue and operator == "not_empty":
        b_continue = False
        sized = _collection_size(field_value)
        result = bool(sized is not None and sized > 0)
    return result


def _is_star_import(a_value: Any) -> bool:
    b_continue = True
    result = False
    if b_continue and isinstance(a_value, list):
        b_continue = False
        result = False
        for alias in cast("list[object]", a_value):
            if isinstance(alias, ast.alias) and alias.name == "*":
                result = True
    if b_continue and isinstance(a_value, ast.ImportFrom):
        b_continue = False
        result = any(alias.name == "*" for alias in a_value.names)
    if b_continue:
        result = False
    return result


def _collection_size(a_value: object) -> int | None:
    b_continue = True
    result: int | None = None
    if b_continue and isinstance(a_value, (str, list, tuple, set, dict)):
        b_continue = False
        result = len(cast("Sized", a_value))
    if b_continue:
        result = None
    return result


def _ast_to_comparable(a_value: Any) -> Any:
    b_continue = True
    result: Any = a_value
    if b_continue and isinstance(a_value, ast.Attribute):
        b_continue = False
        result = a_value.attr
    if b_continue and isinstance(a_value, ast.Name):
        b_continue = False
        result = a_value.id
    if b_continue and isinstance(a_value, ast.Constant):
        b_continue = False
        result = a_value.value
    if b_continue and isinstance(a_value, ast.AST):
        b_continue = False
        result = ast.unparse(a_value)
    if b_continue:
        result = a_value
    return result


def _safe_unparse(a_value: Any) -> str:
    b_continue = True
    result = ""
    if b_continue and a_value is None:
        b_continue = False
        result = ""
    if b_continue and isinstance(a_value, ast.AST):
        b_continue = False
        result = ast.unparse(a_value)
    if b_continue:
        result = str(_ast_to_comparable(a_value))
    return result


def _resolve_field(a_node: ast.AST, a_field: str) -> Any:
    b_continue = True
    result: Any = None
    if b_continue and a_field in ("", ".", "self"):
        b_continue = False
        result = a_node
    if b_continue:
        current: Any = a_node
        for part in a_field.split("."):
            if b_continue and current is None:
                b_continue = False
                result = None
            if b_continue and isinstance(current, ast.AST):
                current = getattr(current, part, None)
            elif b_continue:
                b_continue = False
                result = None
        if b_continue:
            result = current
    return result


def _subtree_contains_node_type(a_node: Any, a_type_name: str) -> bool:
    b_continue = True
    result = False
    if b_continue and not isinstance(a_node, ast.AST):
        b_continue = False
        result = False
    if b_continue:
        result = any(type(child).__name__ == a_type_name for child in ast.walk(a_node))
    return result


def _skip_param_names(a_cfg: dict[str, Any]) -> set[str]:
    b_continue = True
    result: set[str] = {"self", "cls"}
    raw = a_cfg.get("skip_names", ["self", "cls"])
    names = _as_str_list(raw)
    if b_continue and not names:
        b_continue = False
        result = {"self", "cls"}
    if b_continue:
        result = set(names)
    return result


def _iter_function_params(a_node: ast.AST) -> list[ast.arg]:
    b_continue = True
    result: list[ast.arg] = []
    args_obj: object = getattr(a_node, "args", None)
    if b_continue and args_obj is None:
        b_continue = False
        result = []
    if b_continue and isinstance(args_obj, ast.arguments):
        params: list[ast.arg] = []
        params.extend(list(args_obj.posonlyargs))
        params.extend(list(args_obj.args))
        params.extend(list(args_obj.kwonlyargs))
        if args_obj.vararg is not None:
            params.append(args_obj.vararg)
        if args_obj.kwarg is not None:
            params.append(args_obj.kwarg)
        result = params
    return result


def _param_names(a_node: ast.AST) -> set[str]:
    return {p.arg for p in _iter_function_params(a_node)}


def _has_mutable_defaults(a_node: ast.AST, a_types: set[str]) -> bool:
    b_continue = True
    result = False
    args_obj: object = getattr(a_node, "args", None)
    if b_continue and not isinstance(args_obj, ast.arguments):
        b_continue = False
        result = False
    if b_continue and isinstance(args_obj, ast.arguments):
        defaults: list[ast.expr] = []
        defaults.extend(list(args_obj.defaults))
        defaults.extend([d for d in args_obj.kw_defaults if d is not None])
        type_to_ast: dict[str, type[ast.AST]] = {
            "list": ast.List,
            "dict": ast.Dict,
            "set": ast.Set,
        }
        for default in defaults:
            if b_continue:
                for type_name, node_cls in type_to_ast.items():
                    if (
                        b_continue
                        and type_name in a_types
                        and isinstance(default, node_cls)
                    ):
                        b_continue = False
                        result = True
            if (
                b_continue
                and isinstance(default, ast.Call)
                and isinstance(default.func, ast.Name)
            ):
                if default.func.id in a_types:
                    b_continue = False
                    result = True
    return result


def _params_missing_prefix(a_node: ast.AST, a_cfg: dict[str, Any]) -> bool:
    """True when application parameters lack the configured prefix.

    Language receivers (self/cls) and *args/**kwargs may be listed in skip_names
    as naming conventions for those slots — not as function-level rule exemptions.
    """
    b_continue = True
    result = False
    if b_continue and not isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        b_continue = False
        result = False
    if b_continue:
        prefix = str(a_cfg.get("prefix", "a_"))
        allow_private = bool(a_cfg.get("allow_private_underscore", True))
        skip = _skip_param_names(a_cfg)
        found_missing = False
        for param in _iter_function_params(a_node):
            name = param.arg
            check = True
            if check and name in skip:
                check = False
            if check and name.startswith(prefix):
                check = False
            if check and allow_private and name.startswith("_"):
                check = False
            if check:
                found_missing = True
        result = found_missing
    return result


def _params_any_unannotated(a_node: ast.AST, a_cfg: dict[str, Any]) -> bool:
    b_continue = True
    result = False
    if b_continue and not isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        b_continue = False
        result = False
    if b_continue:
        skip = _skip_param_names(a_cfg)
        found = False
        for param in _iter_function_params(a_node):
            if not found and param.arg not in skip and param.annotation is None:
                found = True
        result = found
    return result


def _body_contains_any(a_node: ast.AST, a_needles: list[str]) -> bool:
    body = getattr(a_node, "body", None)
    if not isinstance(body, list):
        src = _safe_unparse(a_node)
    else:
        parts: list[str] = []
        for stmt in cast("list[object]", body):
            if isinstance(stmt, ast.AST):
                parts.append(ast.unparse(stmt))
        src = "\n".join(parts)
    return any(needle in src for needle in a_needles)


def _calls_own_name(a_node: ast.AST) -> bool:
    b_continue = True
    result = False
    if b_continue and not isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        b_continue = False
        result = False
    if b_continue and isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name = a_node.name
        for child in ast.walk(a_node):
            if b_continue and isinstance(child, ast.Call):
                if (
                    b_continue
                    and isinstance(child.func, ast.Name)
                    and child.func.id == name
                ):
                    b_continue = False
                    result = True
                if (
                    b_continue
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == name
                ):
                    if isinstance(
                        child.func.value, ast.Name
                    ) and child.func.value.id in {"self", "cls"}:
                        b_continue = False
                        result = True
    return result


def _calls_any(a_node: ast.AST, a_cfg: dict[str, Any]) -> bool:
    b_continue = True
    result = False
    names = set(_as_str_list(a_cfg.get("names")))
    attrs = set(_as_str_list(a_cfg.get("attrs")))
    modules = set(_as_str_list(a_cfg.get("module_attrs")))
    for child in ast.walk(a_node):
        if b_continue and isinstance(child, ast.Call):
            if (
                b_continue
                and isinstance(child.func, ast.Name)
                and child.func.id in names
            ):
                b_continue = False
                result = True
            if b_continue and isinstance(child.func, ast.Attribute):
                if b_continue and child.func.attr in attrs:
                    b_continue = False
                    result = True
                if (
                    b_continue
                    and child.func.attr in modules
                    and isinstance(child.func.value, ast.Name)
                ):
                    if f"{child.func.value.id}.{child.func.attr}" in modules:
                        b_continue = False
                        result = True
                if (
                    b_continue
                    and child.func.attr == "run"
                    and isinstance(child.func.value, ast.Name)
                    and child.func.value.id in names
                ):
                    b_continue = False
                    result = True
    return result


def _call_message_missing_or_empty(a_node: ast.AST, a_cfg: dict[str, Any]) -> bool:
    b_continue = True
    result = False
    if b_continue and not isinstance(a_node, ast.Call):
        b_continue = False
        result = False
    if b_continue and isinstance(a_node, ast.Call):
        call_node = a_node
        keyword_names = set(
            _as_str_list(a_cfg.get("keyword_names", ["a_message", "message"]))
        )
        empty_values_raw: object = a_cfg.get("empty_values", ["", None])
        empty_values: list[object]
        if isinstance(empty_values_raw, list):
            empty_values = cast("list[object]", cast("list[Any]", empty_values_raw))
        elif isinstance(empty_values_raw, tuple):
            empty_values = list(cast("tuple[Any, ...]", empty_values_raw))
        else:
            empty_values = ["", None]
        found_kw = False
        for kw in call_node.keywords:
            if b_continue and kw.arg in keyword_names:
                b_continue = False
                found_kw = True
                result = bool(
                    isinstance(kw.value, ast.Constant)
                    and kw.value.value in empty_values
                )
        if b_continue and not call_node.args:
            b_continue = False
            result = True
        if b_continue and not found_kw:
            first = call_node.args[0]
            result = bool(
                isinstance(first, ast.Constant) and first.value in empty_values
            )
    return result


def _attr_call_on_shared_state(
    a_node: ast.AST,
    a_tree: ast.AST,
    a_cfg: dict[str, Any],
) -> bool:
    b_continue = True
    result = False
    if b_continue and not isinstance(a_node, ast.Call):
        b_continue = False
        result = False
    if (
        b_continue
        and isinstance(a_node, ast.Call)
        and not isinstance(a_node.func, ast.Attribute)
    ):
        b_continue = False
        result = False
    if (
        b_continue
        and isinstance(a_node, ast.Call)
        and isinstance(a_node.func, ast.Attribute)
    ):
        call_node = a_node
        func_attr = a_node.func
        methods = _as_str_list(a_cfg.get("methods"))
        if methods and func_attr.attr not in set(methods):
            b_continue = False
            result = False
        if b_continue:
            lock_markers = _as_str_list(
                a_cfg.get("lock_markers", ["Lock", "RLock", "lock"])
            )
            if _call_protected_by_markers(call_node, a_tree, lock_markers):
                b_continue = False
                result = False
        if b_continue:
            receiver = func_attr.value
            self_set = set(_as_str_list(a_cfg.get("self_names", ["self"])))
            if isinstance(receiver, ast.Attribute):
                root: ast.expr = receiver
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name) and root.id in self_set:
                    b_continue = False
                    result = True
            if b_continue and isinstance(receiver, ast.Name):
                enclosing = _find_enclosing_function(call_node, a_tree)
                if enclosing is None:
                    b_continue = False
                    result = True
                if b_continue and enclosing is not None:
                    if receiver.id not in _local_names(enclosing):
                        b_continue = False
                        result = True
    return result


def _call_protected_by_markers(
    a_node: ast.AST,
    a_tree: ast.AST,
    a_markers: list[str],
) -> bool:
    b_continue = True
    result = False
    for parent in ast.walk(a_tree):
        if b_continue and isinstance(parent, ast.With):
            if any(child is a_node for child in ast.walk(parent)):
                for item in parent.items:
                    if b_continue:
                        src = ast.unparse(item.context_expr)
                        if any(marker in src for marker in a_markers):
                            b_continue = False
                            result = True
    return result


def _local_names(a_func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names = {p.arg for p in _iter_function_params(a_func)}
    for node in ast.walk(a_func):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        if isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def _find_enclosing_function(
    a_node: ast.AST, a_tree: ast.AST
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    best: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    best_size = 10**12
    for parent in ast.walk(a_tree):
        if not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(child is a_node for child in ast.walk(parent)):
            continue
        size = sum(1 for _ in ast.walk(parent))
        if size < best_size:
            best = parent
            best_size = size
    return best


def _except_type_names(a_node: ast.AST) -> set[str]:
    b_continue = True
    names: set[str] = set()
    if b_continue and (
        not isinstance(a_node, ast.ExceptHandler) or a_node.type is None
    ):
        b_continue = False
        names = set()
    if b_continue and isinstance(a_node, ast.ExceptHandler) and a_node.type is not None:
        exc_type = a_node.type
        if isinstance(exc_type, ast.Name):
            b_continue = False
            names = {exc_type.id}
        if b_continue and isinstance(exc_type, ast.Attribute):
            b_continue = False
            names = {exc_type.attr}
        if b_continue and isinstance(exc_type, ast.Tuple):
            b_continue = False
            for elt in exc_type.elts:
                if isinstance(elt, ast.Name):
                    names.add(elt.id)
                elif isinstance(elt, ast.Attribute):
                    names.add(elt.attr)
    return names


def _except_bound_name_unused(a_node: ast.AST, a_markers: list[str]) -> bool:
    b_continue = True
    result = False
    if b_continue and not isinstance(a_node, ast.ExceptHandler):
        b_continue = False
        result = False
    if b_continue and isinstance(a_node, ast.ExceptHandler) and a_node.name is None:
        b_continue = False
        result = False
    if b_continue and isinstance(a_node, ast.ExceptHandler) and a_node.name is not None:
        bound_name = a_node.name
        body_src = "\n".join(ast.unparse(stmt) for stmt in a_node.body)
        if bound_name in body_src:
            b_continue = False
            result = False
        if b_continue:
            result = not any(marker in body_src for marker in a_markers)
    return result
