"""CLI interface — command-line entry point.

Minimal composition root. All logic in use cases.
Selma lints its own source code.
"""

from __future__ import annotations

import ast
import argparse
import sys
from pathlib import Path

from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result


def main() -> int:
    """CLI entry point.

    Parses arguments, wires dependencies, runs lint, outputs results.
    """
    b_continue = True
    result = 0
    parser = argparse.ArgumentParser(
        prog="selma",
        description="Selma — Schema-driven AST linter enforcing Safe Coding Doctrine",
    )
    parser.add_argument("--version", action="version", version="Selma v0.1.0")
    parser.add_argument("paths", nargs="*", help="Files or directories to lint")
    parser.add_argument(
        "-f", "--format",
        choices=["default", "json", "gcc", "guidance"],
        default="default",
    )
    parser.add_argument("--guide", action="store_true", help="Include guidance in output")
    parser.add_argument("--skip-tools", action="store_true", help="Skip external tools")
    parser.add_argument("--skip-ast", action="store_true", help="Skip AST rules")
    parser.add_argument("--only", help="Run only one check")
    parser.add_argument("--codes", nargs="*", help="Only run rules with these codes")
    parser.add_argument("--exclude-codes", nargs="*", help="Exclude rules with these codes")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if b_continue and not args.paths:
        b_continue = False
        parser.print_help()
        result = 0

    if b_continue:
        # Load JSON rules from schema/rules/
        import selma as _selma_pkg
        from selma.infrastructure.config.models import SelmaConfig

        _pkg_dir = Path(_selma_pkg.__file__).parent
        rules_dir = _pkg_dir.parent.parent / "schema" / "rules"
        json_rules = _load_json_rules(rules_dir)

        # Filter disabled rules from config
        _config = SelmaConfig()
        disabled_codes = set(_config.rules_filter.disabled)
        if args.exclude_codes:
            disabled_codes.update(args.exclude_codes)
        if args.codes:
            json_rules = [r for r in json_rules if r.get("lineage_id") in args.codes]
        else:
            json_rules = [r for r in json_rules if r.get("lineage_id") not in disabled_codes]

        # Lint each path
        total_violations = 0
        for path_str in args.paths:
            path = Path(path_str)
            if path.is_file() and path.suffix == ".py":
                violations = _lint_file(path, json_rules)
                for v in violations:
                    print(v)
                total_violations += len(violations)
            elif path.is_dir():
                for py_file in sorted(path.rglob("*.py")):
                    violations = _lint_file(py_file, json_rules)
                    for v in violations:
                        print(v)
                    total_violations += len(violations)

        if total_violations > 0:
            result = 1

    return result


def _load_json_rules(a_rules_dir: Path) -> list[dict]:
    """Load JSON rule files from directory."""
    import json

    rules: list[dict] = []
    if not a_rules_dir.exists():
        return rules

    for json_file in sorted(a_rules_dir.glob("*.json")):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "evaluator_type" in data:
                rules.append(data)
            elif isinstance(data, dict) and "rules" in data:
                for rule_data in data["rules"]:
                    if "evaluator_type" in rule_data:
                        rules.append(rule_data)
        except (json.JSONDecodeError, OSError):
            continue

    return rules


def _lint_file(a_path: Path, a_rules: list[dict]) -> list[str]:
    """Lint a single Python file against all JSON rules."""
    b_continue = True
    violations: list[str] = []

    try:
        source = a_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(a_path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        b_continue = False
        violations.append(f"{a_path}:0: error: {exc}")

    if b_continue:
        for rule in a_rules:
            try:
                violations_data = _evaluate_rule(tree, rule, source)
                for vd in violations_data:
                    violations.append(
                        f"{a_path}:{vd['line']}:{vd['col']}: "
                        f"{rule.get('weight', 'medium')}: "
                        f"{vd['message']} ({rule.get('lineage_id', 'UNKNOWN')})"
                    )
            except Exception as exc:
                code = rule.get("lineage_id", "UNKNOWN")
                violations.append(f"{a_path}:0: error: Rule {code} failed: {exc}")

    return violations


def _evaluate_rule(a_tree: ast.AST, a_rule: dict, a_source: str) -> list[dict]:
    """Evaluate a JSON rule against an AST."""
    evaluator_type = a_rule.get("evaluator_type", "")
    config = a_rule.get("evaluator_config", {})

    match evaluator_type:
        case "ast_walk":
            return _eval_ast_walk(a_tree, config)
        case "ast_node_match":
            return _eval_ast_node_match(a_tree, config)
        case "ast_call_check":
            return _eval_ast_call_check(a_tree, config)
        case "ast_context_check":
            return _eval_ast_context_check(a_tree, config)
        case "ast_module_check":
            return _eval_ast_module_check(a_tree, config)
        case "regex":
            return _eval_regex(a_source, config)
        case _:
            return []


def _eval_ast_node_match(a_tree: ast.AST, a_config: dict) -> list[dict]:
    """Match AST nodes with conditions."""
    violations: list[dict] = []
    target_node = a_config.get("target_node", "FunctionDef")
    conditions = a_config.get("conditions", [])
    msg_template = a_config.get("message_template", "")

    for node in ast.walk(a_tree):
        if type(node).__name__ != target_node:
            continue
        if _check_conditions(node, conditions):
            name = getattr(node, "name", getattr(node, "module", ""))
            msg = msg_template.replace("{name}", str(name))
            violations.append({
                "line": getattr(node, "lineno", 0),
                "col": getattr(node, "col_offset", 0),
                "message": msg,
            })

    return violations


def _check_conditions(a_node: ast.AST, a_conditions: list[dict]) -> bool:
    """Check if node matches all conditions."""
    for cond in a_conditions:
        field = cond.get("field", "")
        op = cond.get("operator", "")

        if op == "star_import":
            # Special case: check if ImportFrom has wildcard import
            if isinstance(a_node, ast.ImportFrom):
                for alias in a_node.names:
                    if alias.name == "*":
                        return True
            return False

        actual = getattr(a_node, field, None)
        if actual is None:
            return False

        match op:
            case "eq":
                if str(actual) != str(cond.get("value", "")):
                    return False
            case "neq":
                if str(actual) == str(cond.get("value", "")):
                    return False
            case "exists":
                pass
            case "not_exists":
                return False

    return True


def _eval_ast_walk(a_tree: ast.AST, a_config: dict) -> list[dict]:
    """Walk AST counting specific node types."""
    violations: list[dict] = []
    root_node = a_config.get("root_node", "FunctionDef")
    walk_nodes = a_config.get("walk_nodes", [])
    count_config = a_config.get("count", {})
    msg_template = a_config.get("message_template", "")
    exempt_dunders = a_config.get("exempt_dunders", True)
    exempt_generators = a_config.get("exempt_generators", True)

    for node in ast.walk(a_tree):
        if type(node).__name__ != root_node:
            continue
        if exempt_dunders and _is_dunder(node):
            continue
        if exempt_generators and _has_yield(node):
            continue

        count = _count_child_nodes(node, walk_nodes)
        if _check_threshold(count, count_config):
            name = getattr(node, "name", "")
            msg = msg_template.replace("{name}", name).replace("{count}", str(count))
            violations.append({
                "line": getattr(node, "lineno", 0),
                "col": getattr(node, "col_offset", 0),
                "message": msg,
            })

    return violations


def _eval_ast_call_check(a_tree: ast.AST, a_config: dict) -> list[dict]:
    """Check function calls."""
    violations: list[dict] = []
    forbidden_functions = a_config.get("forbidden_functions", [])
    forbidden_calls = a_config.get("forbidden_calls", [])
    msg_template = a_config.get("message_template", "")

    for node in ast.walk(a_tree):
        if not isinstance(node, ast.Call):
            continue

        # Check forbidden functions
        if isinstance(node.func, ast.Name) and node.func.id in forbidden_functions:
            func_name = node.func.id
            msg = msg_template.replace("{function}", func_name)
            violations.append({
                "line": getattr(node, "lineno", 0),
                "col": getattr(node, "col_offset", 0),
                "message": msg,
            })

        # Check forbidden calls (module.method)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            mod = node.func.value.id
            method = node.func.attr
            for fc in forbidden_calls:
                if fc.get("module") == mod and fc.get("method") == method:
                    msg = msg_template.replace("{function}", f"{mod}.{method}")
                    violations.append({
                        "line": getattr(node, "lineno", 0),
                        "col": getattr(node, "col_offset", 0),
                        "message": msg,
                    })

    return violations


def _eval_ast_context_check(a_tree: ast.AST, a_config: dict) -> list[dict]:
    """Check parent context (with/try)."""
    violations: list[dict] = []
    target_functions = a_config.get("target_functions", [])
    msg_template = a_config.get("message_template", "")

    for node in ast.walk(a_tree):
        if not isinstance(node, ast.Call):
            continue
        func_name = _get_call_name(node)
        if func_name not in target_functions:
            continue
        if not _is_in_with_context(node, a_tree):
            msg = msg_template.replace("{function}", func_name)
            violations.append({
                "line": getattr(node, "lineno", 0),
                "col": getattr(node, "col_offset", 0),
                "message": msg,
            })

    return violations


def _eval_ast_module_check(a_tree: ast.AST, a_config: dict) -> list[dict]:
    """Module-level checks."""
    violations: list[dict] = []
    sentinel_name = a_config.get("sentinel_name", "INVALID_RESULT")
    condition = a_config.get("condition", "")
    msg_template = a_config.get("message_template", "")

    if condition == "module_has_result_returning_functions":
        has_sentinel = _check_sentinel_exists(a_tree, sentinel_name)
        has_result_return = _check_module_has_result_return(a_tree)
        if has_result_return and not has_sentinel:
            violations.append({
                "line": 1,
                "col": 0,
                "message": msg_template,
            })

    return violations


def _eval_regex(a_source: str, a_config: dict) -> list[dict]:
    """Text pattern matching."""
    import re

    violations: list[dict] = []
    pattern = a_config.get("pattern", "")
    if not pattern:
        return violations

    try:
        compiled = re.compile(pattern)
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


# --- Helpers ---

def _is_dunder(a_node: ast.AST) -> bool:
    name = getattr(a_node, "name", "")
    return name.startswith("__") and name.endswith("__")


def _has_yield(a_node: ast.AST) -> bool:
    for child in ast.walk(a_node):
        if isinstance(child, (ast.Yield, ast.YieldFrom)):
            return True
    return False


def _count_child_nodes(a_node: ast.AST, a_types: list[str]) -> int:
    count = 0
    for child in ast.walk(a_node):
        if child is a_node:
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if type(child).__name__ in a_types:
            count += 1
    return count


def _check_threshold(a_count: int, a_config: dict) -> bool:
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


def _get_call_name(a_node: ast.Call) -> str:
    if isinstance(a_node.func, ast.Name):
        return a_node.func.id
    if isinstance(a_node.func, ast.Attribute):
        return a_node.func.attr
    return ""


def _is_in_with_context(a_node: ast.Call, a_tree: ast.AST) -> bool:
    for parent in ast.walk(a_tree):
        if isinstance(parent, ast.With):
            for item in parent.items:
                for child in ast.walk(item.context_expr):
                    if child is a_node:
                        return True
    return False


def _check_sentinel_exists(a_tree: ast.AST, a_name: str) -> bool:
    for node in ast.walk(a_tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == a_name:
                    return True
    return False


def _check_module_has_result_return(a_tree: ast.AST) -> bool:
    for node in ast.walk(a_tree):
        if isinstance(node, ast.FunctionDef):
            if node.returns:
                ret_str = ast.dump(node.returns)
                if "Result" in ret_str:
                    return True
    return False


if __name__ == "__main__":
    sys.exit(main())
