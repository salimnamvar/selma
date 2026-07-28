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
    if a_value is None:
        return []
    if isinstance(a_value, str):
        return [a_value]
    if isinstance(a_value, list):
        values = cast("list[Any]", a_value)
        return [str(values[i]) for i in range(len(values))]
    if isinstance(a_value, tuple):
        values_t = cast("tuple[Any, ...]", a_value)
        return [str(values_t[i]) for i in range(len(values_t))]
    return [str(a_value)]


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
    """Match AST nodes using target_node + declarative conditions from config."""

    def evaluate(
        self,
        a_tree: ast.AST,
        a_config: dict[str, Any],
        a_rule: dict[str, Any],
        a_source_code: str = "",
    ) -> Result[list[Finding]]:
        findings: list[Finding] = []
        target_node = str(a_config.get("target_node", ""))
        conditions = _as_cond_list(a_config.get("conditions", []))
        message_template = str(a_config.get("message_template", ""))
        params_obj: object = a_rule.get("parameters")
        exemptions = _as_dict(params_obj)
        lineage_id = str(a_rule.get("lineage_id", ""))
        ctx_base: dict[str, Any] = {"tree": a_tree, "parameters": exemptions}

        for node in ast.walk(a_tree):
            b_continue = True
            if b_continue and self.node_name(node) != target_node:
                b_continue = False
            if b_continue and self._is_node_excluded(node, exemptions):
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
    def _is_node_excluded(a_node: ast.AST, a_exemptions: dict[str, Any]) -> bool:
        b_continue = True
        result = False
        if b_continue and a_exemptions.get("exempt_dunders", False):
            name = getattr(a_node, "name", "")
            if b_continue and EvaluatorBase.is_dunder(str(name)):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_properties", False):
            if b_continue and EvaluatorBase.has_decorator(a_node, "property"):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_abstract", False):
            if b_continue and EvaluatorBase.has_decorator(a_node, "abstractmethod"):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_no_args", False):
            if b_continue and _has_no_non_self_args(a_node, a_exemptions):
                b_continue = False
                result = True
        if b_continue and a_exemptions.get("exempt_init", False):
            name = getattr(a_node, "name", "")
            init_names = a_exemptions.get(
                "init_names",
                ["__init__", "__post_init__", "__init_subclass__"],
            )
            if b_continue and name in init_names:
                b_continue = False
                result = True
        return result

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
    if a_depth >= a_max_depth:
        return False
    if "all_of" in a_cond:
        items = _as_cond_list(a_cond.get("all_of"))
        return all(
            _match_condition(
                a_node, c, a_ctx, a_depth=a_depth + 1, a_max_depth=a_max_depth
            )
            for c in items
        )
    if "any_of" in a_cond:
        items = _as_cond_list(a_cond.get("any_of"))
        return any(
            _match_condition(
                a_node, c, a_ctx, a_depth=a_depth + 1, a_max_depth=a_max_depth
            )
            for c in items
        )
    if "not" in a_cond:
        inner = a_cond.get("not")
        if not isinstance(inner, dict):
            return False
        return not _match_condition(
            a_node,
            _as_dict(cast("object", inner)),
            a_ctx,
            a_depth=a_depth + 1,
            a_max_depth=a_max_depth,
        )

    field = str(a_cond.get("field", ""))
    operator = str(a_cond.get("operator", ""))
    value: object = a_cond.get("value", "")
    field_value = _resolve_field(a_node, field)

    if operator == "exists":
        if field_value is None:
            return False
        sized = _collection_size(field_value)
        return True if sized is None else sized > 0
    if operator == "not_exists":
        if field_value is None:
            return True
        sized = _collection_size(field_value)
        return False if sized is None else sized == 0
    if operator in {"equals", "eq"}:
        return str(_ast_to_comparable(field_value)) == str(value)
    if operator in {"not_equals", "neq"}:
        return str(_ast_to_comparable(field_value)) != str(value)
    if operator == "matches":
        return bool(re.search(str(value), str(_ast_to_comparable(field_value))))
    if operator == "not_matches":
        return not bool(re.search(str(value), str(_ast_to_comparable(field_value))))
    if operator == "contains":
        return str(value) in str(_ast_to_comparable(field_value))
    if operator == "not_contains":
        return str(value) not in str(_ast_to_comparable(field_value))
    if operator == "contains_node":
        return _subtree_contains_node_type(
            a_node if field in ("", ".") else field_value, str(value)
        )
    if operator == "subtree_contains_node":
        target = a_node if field in ("", ".") else field_value
        if not isinstance(target, ast.AST):
            return False
        return _subtree_contains_node_type(target, str(value))
    if operator == "unparse_matches":
        return bool(re.search(str(value), _safe_unparse(field_value), re.IGNORECASE))
    if operator == "unparse_not_matches":
        return not bool(
            re.search(str(value), _safe_unparse(field_value), re.IGNORECASE)
        )
    if operator == "unparse_contains":
        return str(value) in _safe_unparse(field_value)
    if operator == "unparse_not_contains":
        return str(value) not in _safe_unparse(field_value)
    if operator == "unparse_in":
        return _safe_unparse(field_value) in set(_as_str_list(value))
    if operator == "unparse_not_in":
        return _safe_unparse(field_value) not in set(_as_str_list(value))
    if operator == "has_mutable_defaults":
        return _has_mutable_defaults(a_node, _as_str_set(value))
    if operator == "params_missing_prefix":
        return _params_missing_prefix(a_node, _as_dict(value), a_ctx.get("tree"))
    if operator == "params_any_unannotated":
        return _params_any_unannotated(a_node, _as_dict(value))
    if operator == "body_contains_any":
        return _body_contains_any(a_node, _as_str_list(value))
    if operator == "body_not_contains_any":
        return not _body_contains_any(a_node, _as_str_list(value))
    if operator == "calls_own_name":
        return _calls_own_name(a_node)
    if operator == "param_names_intersect":
        return bool(_param_names(a_node) & _as_str_set(value))
    if operator == "param_names_disjoint":
        return not bool(_param_names(a_node) & _as_str_set(value))
    if operator == "calls_any":
        return _calls_any(a_node, _as_dict(value))
    if operator == "has_decorator":
        return EvaluatorBase.has_decorator(a_node, str(value))
    if operator == "not_has_decorator":
        return not EvaluatorBase.has_decorator(a_node, str(value))
    if operator == "call_message_missing_or_empty":
        return _call_message_missing_or_empty(a_node, _as_dict(value))
    if operator == "attr_call_on_shared_state":
        tree = a_ctx.get("tree")
        if not isinstance(tree, ast.AST):
            return False
        return _attr_call_on_shared_state(a_node, tree, _as_dict(value))
    if operator == "except_type_names_intersect":
        return bool(_except_type_names(a_node) & _as_str_set(value))
    if operator == "except_type_names_disjoint":
        return not bool(_except_type_names(a_node) & _as_str_set(value))
    if operator == "except_bound_name_unused":
        return _except_bound_name_unused(a_node, _as_str_list(value))
    if operator == "name_not_matches_any":
        name = str(getattr(a_node, "name", ""))
        return not any(re.search(pattern, name) for pattern in _as_str_list(value))
    if operator == "star_import":
        return _is_star_import(field_value if field_value is not None else a_node)
    if operator == "not_empty":
        sized = _collection_size(field_value)
        return bool(sized is not None and sized > 0)
    return False


def _is_star_import(a_value: Any) -> bool:
    if isinstance(a_value, list):
        for alias in cast("list[object]", a_value):
            if isinstance(alias, ast.alias) and alias.name == "*":
                return True
        return False
    if isinstance(a_value, ast.ImportFrom):
        return any(alias.name == "*" for alias in a_value.names)
    return False


def _collection_size(a_value: object) -> int | None:
    if isinstance(a_value, (str, list, tuple, set, dict)):
        return len(cast("Sized", a_value))
    return None


def _ast_to_comparable(a_value: Any) -> Any:
    if isinstance(a_value, ast.Attribute):
        return a_value.attr
    if isinstance(a_value, ast.Name):
        return a_value.id
    if isinstance(a_value, ast.Constant):
        return a_value.value
    if isinstance(a_value, ast.AST):
        return ast.unparse(a_value)
    return a_value


def _safe_unparse(a_value: Any) -> str:
    if a_value is None:
        return ""
    if isinstance(a_value, ast.AST):
        return ast.unparse(a_value)
    return str(_ast_to_comparable(a_value))


def _resolve_field(a_node: ast.AST, a_field: str) -> Any:
    if a_field in ("", ".", "self"):
        return a_node
    current: Any = a_node
    for part in a_field.split("."):
        if current is None:
            return None
        if isinstance(current, ast.AST):
            current = getattr(current, part, None)
        else:
            return None
    return current


def _subtree_contains_node_type(a_node: Any, a_type_name: str) -> bool:
    if not isinstance(a_node, ast.AST):
        return False
    return any(type(child).__name__ == a_type_name for child in ast.walk(a_node))


def _skip_param_names(a_cfg: dict[str, Any]) -> set[str]:
    raw = a_cfg.get("skip_names", ["self", "cls"])
    names = _as_str_list(raw)
    if not names:
        return {"self", "cls"}
    return set(names)


def _iter_function_params(a_node: ast.AST) -> list[ast.arg]:
    args = getattr(a_node, "args", None)
    if args is None:
        return []
    params: list[ast.arg] = []
    params.extend(getattr(args, "posonlyargs", []) or [])
    params.extend(getattr(args, "args", []) or [])
    params.extend(getattr(args, "kwonlyargs", []) or [])
    if getattr(args, "vararg", None) is not None:
        params.append(args.vararg)
    if getattr(args, "kwarg", None) is not None:
        params.append(args.kwarg)
    return params


def _param_names(a_node: ast.AST) -> set[str]:
    return {p.arg for p in _iter_function_params(a_node)}


def _has_no_non_self_args(a_node: ast.AST, a_exemptions: dict[str, Any]) -> bool:
    skip = _skip_param_names(a_exemptions)
    non_self = [p for p in _iter_function_params(a_node) if p.arg not in skip]
    return len(non_self) == 0


def _has_mutable_defaults(a_node: ast.AST, a_types: set[str]) -> bool:
    args = getattr(a_node, "args", None)
    if args is None:
        return False
    defaults: list[ast.expr] = []
    defaults.extend(getattr(args, "defaults", []) or [])
    defaults.extend(
        [d for d in (getattr(args, "kw_defaults", []) or []) if d is not None]
    )
    type_to_ast = {
        "list": ast.List,
        "dict": ast.Dict,
        "set": ast.Set,
    }
    for default in defaults:
        for type_name, node_cls in type_to_ast.items():
            if type_name in a_types and isinstance(default, node_cls):
                return True
        if isinstance(default, ast.Call) and isinstance(default.func, ast.Name):
            if default.func.id in a_types:
                return True
    return False


def _find_enclosing_class(a_node: ast.AST, a_tree: ast.AST) -> ast.ClassDef | None:
    best: ast.ClassDef | None = None
    best_size = 10**12
    for parent in ast.walk(a_tree):
        if not isinstance(parent, ast.ClassDef):
            continue
        if not any(child is a_node for child in ast.walk(parent)):
            continue
        size = sum(1 for _ in ast.walk(parent))
        if size < best_size:
            best = parent
            best_size = size
    return best


def _is_method_in_subclass(a_node: ast.AST, a_tree: ast.AST) -> bool:
    if not isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    enclosing = _find_enclosing_class(a_node, a_tree)
    if enclosing is None:
        return False
    return bool(enclosing.bases)


def _params_missing_prefix(
    a_node: ast.AST, a_cfg: dict[str, Any], a_tree: ast.AST | None = None
) -> bool:
    if not isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    if a_cfg.get("exempt_overrides", False) and a_tree is not None:
        if _is_method_in_subclass(a_node, a_tree):
            return False
    prefix = str(a_cfg.get("prefix", "a_"))
    allow_private = bool(a_cfg.get("allow_private_underscore", True))
    skip = _skip_param_names(a_cfg)
    for param in _iter_function_params(a_node):
        name = param.arg
        if name in skip:
            continue
        if name.startswith(prefix):
            continue
        if allow_private and name.startswith("_"):
            continue
        return True
    return False


def _params_any_unannotated(a_node: ast.AST, a_cfg: dict[str, Any]) -> bool:
    if not isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    skip = _skip_param_names(a_cfg)
    for param in _iter_function_params(a_node):
        if param.arg in skip:
            continue
        if param.annotation is None:
            return True
    return False


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
    if not isinstance(a_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    name = a_node.name
    for child in ast.walk(a_node):
        if not isinstance(child, ast.Call):
            continue
        if isinstance(child.func, ast.Name) and child.func.id == name:
            return True
        if isinstance(child.func, ast.Attribute) and child.func.attr == name:
            if isinstance(child.func.value, ast.Name) and child.func.value.id in {
                "self",
                "cls",
            }:
                return True
    return False


def _calls_any(a_node: ast.AST, a_cfg: dict[str, Any]) -> bool:
    names = set(_as_str_list(a_cfg.get("names")))
    attrs = set(_as_str_list(a_cfg.get("attrs")))
    modules = set(_as_str_list(a_cfg.get("module_attrs")))
    for child in ast.walk(a_node):
        if not isinstance(child, ast.Call):
            continue
        if isinstance(child.func, ast.Name) and child.func.id in names:
            return True
        if isinstance(child.func, ast.Attribute):
            if child.func.attr in attrs:
                return True
            if child.func.attr in modules and isinstance(child.func.value, ast.Name):
                if f"{child.func.value.id}.{child.func.attr}" in modules:
                    return True
            if (
                child.func.attr == "run"
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id in names
            ):
                return True
    return False


def _call_message_missing_or_empty(a_node: ast.AST, a_cfg: dict[str, Any]) -> bool:
    if not isinstance(a_node, ast.Call):
        return False
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
    for kw in a_node.keywords:
        if kw.arg in keyword_names:
            return bool(
                isinstance(kw.value, ast.Constant) and kw.value.value in empty_values
            )
    if not a_node.args:
        return True
    first = a_node.args[0]
    return bool(isinstance(first, ast.Constant) and first.value in empty_values)


def _attr_call_on_shared_state(
    a_node: ast.AST,
    a_tree: ast.AST,
    a_cfg: dict[str, Any],
) -> bool:
    if not isinstance(a_node, ast.Call):
        return False
    if not isinstance(a_node.func, ast.Attribute):
        return False
    methods = _as_str_list(a_cfg.get("methods"))
    if methods and a_node.func.attr not in set(methods):
        return False
    lock_markers = _as_str_list(a_cfg.get("lock_markers", ["Lock", "RLock", "lock"]))
    if _call_protected_by_markers(a_node, a_tree, lock_markers):
        return False
    receiver = a_node.func.value
    self_set = set(_as_str_list(a_cfg.get("self_names", ["self"])))
    if isinstance(receiver, ast.Attribute):
        root: ast.AST = receiver
        while isinstance(root, ast.Attribute):
            root = root.value
        if isinstance(root, ast.Name) and root.id in self_set:
            return True
    if isinstance(receiver, ast.Name):
        enclosing = _find_enclosing_function(a_node, a_tree)
        if enclosing is None:
            return True
        if receiver.id not in _local_names(enclosing):
            return True
    return False


def _call_protected_by_markers(
    a_node: ast.AST,
    a_tree: ast.AST,
    a_markers: list[str],
) -> bool:
    for parent in ast.walk(a_tree):
        if not isinstance(parent, ast.With):
            continue
        if not any(child is a_node for child in ast.walk(parent)):
            continue
        for item in parent.items:
            src = ast.unparse(item.context_expr)
            if any(marker in src for marker in a_markers):
                return True
    return False


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
    if not isinstance(a_node, ast.ExceptHandler) or a_node.type is None:
        return set()
    names: set[str] = set()
    if isinstance(a_node.type, ast.Name):
        names.add(a_node.type.id)
        return names
    if isinstance(a_node.type, ast.Attribute):
        names.add(a_node.type.attr)
        return names
    if isinstance(a_node.type, ast.Tuple):
        for elt in a_node.type.elts:
            if isinstance(elt, ast.Name):
                names.add(elt.id)
            elif isinstance(elt, ast.Attribute):
                names.add(elt.attr)
    return names


def _except_bound_name_unused(a_node: ast.AST, a_markers: list[str]) -> bool:
    if not isinstance(a_node, ast.ExceptHandler):
        return False
    if a_node.name is None:
        return False
    body_src = "\n".join(ast.unparse(stmt) for stmt in a_node.body)
    if a_node.name in body_src:
        return False
    return not any(marker in body_src for marker in a_markers)
