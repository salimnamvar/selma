"""Tests for AST evaluator strategies."""

from __future__ import annotations

import ast
from pathlib import Path

from selma.infrastructure.evaluators.ast_call_check import AstCallCheckEvaluator
from selma.infrastructure.evaluators.ast_context_check import AstContextCheckEvaluator
from selma.infrastructure.evaluators.ast_module_check import AstModuleCheckEvaluator
from selma.infrastructure.evaluators.ast_node_match import AstNodeMatchEvaluator
from selma.infrastructure.evaluators.ast_scope_check import AstScopeCheckEvaluator
from selma.infrastructure.evaluators.ast_walk import AstWalkEvaluator
from selma.infrastructure.rule_repository.json_rule_repository import JsonRuleRepository


def _parse(a_source: str) -> ast.AST:
    return ast.parse(a_source)


class TestAstWalkEvaluator:
    """Tests for AstWalkEvaluator (SC-001, SC-002, SC-010)."""

    def test_single_return_no_findings(self) -> None:
        source = """
def foo():
    result = 1
    return result
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "walk_nodes": ["Return"],
            "count": {"operator": "gt", "value": 1},
            "message_template": "Function '{name}' has multiple returns",
        }
        evaluator = AstWalkEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-001"})
        assert findings == []

    def test_multiple_returns_detected(self) -> None:
        source = """
def foo(x):
    if x:
        return 1
    return 0
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "walk_nodes": ["Return"],
            "count": {"operator": "gt", "value": 1},
            "message_template": "Function '{name}' has {count} returns",
        }
        evaluator = AstWalkEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-001"})
        assert len(findings) == 1
        assert "foo" in findings[0].message

    def test_raise_detection(self) -> None:
        source = """
def foo():
    raise ValueError("bad")
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "walk_nodes": ["Raise"],
            "count": {"operator": "gt", "value": 0},
            "message_template": "Function '{name}' raises exceptions",
        }
        evaluator = AstWalkEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-002"})
        assert len(findings) == 1

    def test_dunder_excluded(self) -> None:
        source = """
class Foo:
    def __str__(self):
        return "foo"
    def __repr__(self):
        return "Foo()"
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "walk_nodes": ["Return"],
            "walk_config": {"exclude_dunders": True},
            "count": {"operator": "gt", "value": 1},
            "message_template": "Function '{name}' has multiple returns",
        }
        evaluator = AstWalkEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-001"})
        assert findings == []

    def test_generator_excluded(self) -> None:
        source = """
def gen():
    yield 1
    yield 2
    yield 3
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "walk_nodes": ["Yield"],
            "walk_config": {"exclude_generators": True},
            "count": {"operator": "gt", "value": 0},
            "message_template": "Function '{name}' yields",
        }
        evaluator = AstWalkEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-001"})
        assert findings == []


class TestAstNodeMatchEvaluator:
    """Tests for AstNodeMatchEvaluator (SC-003, SC-024, etc.)."""

    def test_function_without_return_type(self) -> None:
        source = """
def foo():
    pass
"""
        tree = _parse(source)
        config = {
            "target_node": "FunctionDef",
            "conditions": [{"field": "returns", "operator": "not_exists"}],
            "message_template": "Function '{name}' missing return type",
        }
        evaluator = AstNodeMatchEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-024"})
        assert len(findings) == 1

    def test_function_with_return_type(self) -> None:
        source = """
def foo() -> int:
    return 1
"""
        tree = _parse(source)
        config = {
            "target_node": "FunctionDef",
            "conditions": [{"field": "returns", "operator": "not_exists"}],
            "message_template": "Function '{name}' missing return type",
        }
        evaluator = AstNodeMatchEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-024"})
        assert findings == []

    def test_function_with_args_detected(self) -> None:
        source = """
def foo(x, y):
    pass
"""
        tree = _parse(source)
        config = {
            "target_node": "FunctionDef",
            "conditions": [{"field": "args", "operator": "exists"}],
            "message_template": "Function '{name}' has args",
        }
        evaluator = AstNodeMatchEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-009"})
        assert len(findings) == 1

    def test_dunder_exemption(self) -> None:
        source = """
class Foo:
    def __init__(self):
        pass
"""
        tree = _parse(source)
        config = {
            "target_node": "FunctionDef",
            "conditions": [{"field": "returns", "operator": "not_exists"}],
            "message_template": "Function '{name}' missing return type",
        }
        rule = {
            "lineage_id": "SC-024",
            "parameters": {"exempt_dunders": True},
        }
        evaluator = AstNodeMatchEvaluator()
        findings = evaluator.evaluate(tree, config, rule)
        assert findings == []

    def test_style2_only_mutable_defaults(self) -> None:
        source = """
def safe(a_x: int = 1) -> int:
    return a_x

def bad(a_items: list = []) -> int:
    return len(a_items)
"""
        tree = _parse(source)
        config = {
            "target_node": "FunctionDef",
            "conditions": [
                {"field": "name", "operator": "not_matches", "value": "^__.*__$"},
                {
                    "field": ".",
                    "operator": "has_mutable_defaults",
                    "value": ["list", "dict", "set"],
                },
            ],
            "message_template": "Function '{name}' has mutable default",
        }
        evaluator = AstNodeMatchEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "R1"})
        assert len(findings) == 1
        assert "bad" in findings[0].message

    def test_style1_requires_a_prefix(self) -> None:
        source = """
def ok(a_x: int) -> int:
    return a_x

def bad(x: int) -> int:
    return x

def skip_builtin(self, cls, args, kwargs, a_value: int) -> int:
    return a_value
"""
        tree = _parse(source)
        config = {
            "target_node": "FunctionDef",
            "conditions": [
                {"field": "name", "operator": "not_matches", "value": "^__.*__$"},
                {
                    "field": ".",
                    "operator": "params_missing_prefix",
                    "value": {
                        "prefix": "a_",
                        "allow_private_underscore": True,
                        "skip_names": ["self", "cls", "args", "kwargs"],
                    },
                },
            ],
            "message_template": "Function '{name}' arguments must use a_ prefix",
        }
        evaluator = AstNodeMatchEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "R1"})
        assert len(findings) == 1
        assert "bad" in findings[0].message

    def test_sc003_tuple_return_flagged(self) -> None:
        source = """
def bad(a_x: int) -> tuple[int, str]:
    return (a_x, "ok")

def ok(a_x: int) -> int:
    return a_x
"""
        tree = _parse(source)
        config = {
            "target_node": "FunctionDef",
            "conditions": [
                {"field": "name", "operator": "not_matches", "value": "^__.*__$"},
                {"field": "returns", "operator": "exists"},
                {
                    "field": "returns",
                    "operator": "unparse_not_contains",
                    "value": "Result",
                },
                {
                    "any_of": [
                        {
                            "field": "returns",
                            "operator": "unparse_matches",
                            "value": "tuple",
                        },
                        {
                            "field": ".",
                            "operator": "subtree_contains_node",
                            "value": "Raise",
                        },
                    ]
                },
            ],
            "message_template": "Function '{name}' returns values but type is not Result[T]",
        }
        evaluator = AstNodeMatchEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "R1"})
        assert len(findings) == 1
        assert "bad" in findings[0].message

    def test_sc114_only_unbounded_recursion(self) -> None:
        source = """
def total(a_n: int) -> int:
    return a_n + 1

def recurse(a_n: int) -> int:
    if a_n <= 0:
        return 0
    return recurse(a_n - 1)

def guarded(a_n: int, a_depth: int = 0, a_max_depth: int = 10) -> int:
    if a_depth >= a_max_depth:
        return 0
    if a_n <= 0:
        return 0
    return guarded(a_n - 1, a_depth + 1, a_max_depth)
"""
        tree = _parse(source)
        config = {
            "target_node": "FunctionDef",
            "conditions": [
                {"field": "name", "operator": "not_matches", "value": "^__.*__$"},
                {"field": ".", "operator": "calls_own_name"},
                {
                    "field": ".",
                    "operator": "param_names_disjoint",
                    "value": ["a_depth", "a_max_depth", "depth", "max_depth"],
                },
                {
                    "field": ".",
                    "operator": "body_not_contains_any",
                    "value": [
                        "a_depth",
                        "a_max_depth",
                        "max_depth",
                        "sys.getrecursionlimit",
                    ],
                },
            ],
            "message_template": "Recursive function '{name}' missing depth limit",
        }
        evaluator = AstNodeMatchEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "R1"})
        assert len(findings) == 1
        assert "recurse" in findings[0].message

    def test_sc065_empty_failure_message(self) -> None:
        source = """
def bad() -> object:
    return Result.failure("")

def ok() -> object:
    return Result.failure("missing file")
"""
        tree = _parse(source)
        config = {
            "target_node": "Call",
            "conditions": [
                {"field": "func", "operator": "exists"},
                {"field": "func.attr", "operator": "equals", "value": "failure"},
                {
                    "field": ".",
                    "operator": "call_message_missing_or_empty",
                    "value": {
                        "keyword_names": ["a_message", "message"],
                        "empty_values": ["", None],
                    },
                },
            ],
            "message_template": "Result.failure() called without descriptive message",
        }
        evaluator = AstNodeMatchEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "R1"})
        assert len(findings) == 1

    def test_deprecated_rules_not_loaded(self) -> None:
        repo = JsonRuleRepository(
            a_rules_dir=Path("directive/rule"),
            a_schema_path=Path("schema/rule_schema.json"),
        )
        result = repo.find_all()
        assert result.is_success()
        ids = {rule.lineage_id for rule in result.unwrap()}
        assert "SC-121" not in ids
        assert "STYLE-1" in ids


class TestAstScopeCheckEvaluator:
    """Tests for AstScopeCheckEvaluator (SC-011 b_continue rules)."""

    def test_b_continue_must_exist(self) -> None:
        source = """
def foo():
    result = 1
    return result
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "check": {
                "target_name": "b_continue",
                "rules": [{"rule": "must_exist"}],
            },
            "message_template": "Function '{name}' missing b_continue",
        }
        evaluator = AstScopeCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-011"})
        assert len(findings) == 1

    def test_b_continue_exists_no_finding(self) -> None:
        source = """
def foo():
    b_continue = True
    if b_continue:
        pass
    return None
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "check": {
                "target_name": "b_continue",
                "rules": [{"rule": "must_exist"}],
            },
            "message_template": "Function '{name}' missing b_continue",
        }
        evaluator = AstScopeCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-011"})
        assert findings == []

    def test_b_continue_first_value_is_true(self) -> None:
        source = """
def foo():
    b_continue = False
    return None
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "check": {
                "target_name": "b_continue",
                "rules": [{"rule": "first_value_is_true"}],
            },
            "message_template": "Function '{name}' b_continue not initialized to True",
        }
        evaluator = AstScopeCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-011"})
        assert len(findings) == 1

    def test_b_continue_no_reset_to_true(self) -> None:
        source = """
def foo():
    b_continue = True
    b_continue = False
    b_continue = True
    return None
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "check": {
                "target_name": "b_continue",
                "rules": [{"rule": "no_reset_to_true"}],
            },
            "message_template": "Function '{name}' b_continue reset to True",
        }
        evaluator = AstScopeCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-011"})
        assert len(findings) == 1

    def test_b_continue_not_global(self) -> None:
        source = """
def foo():
    global b_continue
    b_continue = True
    return None
"""
        tree = _parse(source)
        config = {
            "root_node": "FunctionDef",
            "check": {
                "target_name": "b_continue",
                "rules": [{"rule": "not_global"}],
            },
            "message_template": "Function '{name}' uses global b_continue",
        }
        evaluator = AstScopeCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-011"})
        assert len(findings) == 1


class TestAstCallCheckEvaluator:
    """Tests for AstCallCheckEvaluator (SC-071, SC-104, etc.)."""

    def test_eval_detected(self) -> None:
        source = """
def foo():
    x = eval("1+1")
"""
        tree = _parse(source)
        config = {
            "forbidden_functions": ["eval", "exec"],
            "message_template": "Forbidden function '{function}'",
        }
        evaluator = AstCallCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-104"})
        assert len(findings) == 1
        assert "eval" in findings[0].message

    def test_exec_detected(self) -> None:
        source = """
def foo():
    exec("x = 1")
"""
        tree = _parse(source)
        config = {
            "forbidden_functions": ["eval", "exec"],
            "message_template": "Forbidden function '{function}'",
        }
        evaluator = AstCallCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-104"})
        assert len(findings) == 1

    def test_datetime_now_detected(self) -> None:
        source = """
import datetime
def foo():
    now = datetime.datetime.now()
"""
        tree = _parse(source)
        config = {
            "forbidden_calls": [{"module": "datetime", "method": "now"}],
            "message_template": "Non-deterministic call: {function}",
        }
        evaluator = AstCallCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-071"})
        assert len(findings) == 1

    def test_safe_function_no_finding(self) -> None:
        source = """
def foo():
    x = len([1, 2, 3])
"""
        tree = _parse(source)
        config = {
            "forbidden_functions": ["eval", "exec"],
            "message_template": "Forbidden function '{function}'",
        }
        evaluator = AstCallCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-104"})
        assert findings == []


class TestAstContextCheckEvaluator:
    """Tests for AstContextCheckEvaluator (SC-080)."""

    def test_open_without_context_manager(self) -> None:
        source = """
def foo():
    f = open("file.txt")
"""
        tree = _parse(source)
        config = {
            "target_functions": ["open"],
            "context": {
                "must_be_inside": ["With"],
                "or_try_finally": True,
            },
            "message_template": "Function '{function}' used without context manager",
        }
        evaluator = AstContextCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-080"})
        assert len(findings) == 1

    def test_open_with_context_manager(self) -> None:
        source = """
def foo():
    with open("file.txt") as f:
        pass
"""
        tree = _parse(source)
        config = {
            "target_functions": ["open"],
            "context": {
                "must_be_inside": ["With"],
                "or_try_finally": True,
            },
            "message_template": "Function '{function}' used without context manager",
        }
        evaluator = AstContextCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-080"})
        assert findings == []

    def test_open_in_try_finally(self) -> None:
        source = """
def foo():
    try:
        f = open("file.txt")
    finally:
        f.close()
"""
        tree = _parse(source)
        config = {
            "target_functions": ["open"],
            "context": {
                "must_be_inside": ["With"],
                "or_try_finally": True,
            },
            "message_template": "Function '{function}' used without context manager",
        }
        evaluator = AstContextCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-080"})
        assert findings == []


class TestAstModuleCheckEvaluator:
    """Tests for AstModuleCheckEvaluator (SC-004)."""

    def test_missing_sentinel(self) -> None:
        source = """
from typing import Optional

def foo() -> Result[int]:
    return Result.success(1)
"""
        tree = _parse(source)
        config = {
            "check": {
                "type": "sentinel_exists",
                "sentinel_name": "INVALID_RESULT",
                "condition": "module_has_result_returning_functions",
            },
            "message_template": "Module missing {sentinel} sentinel",
        }
        evaluator = AstModuleCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-004"})
        assert len(findings) == 1

    def test_sentinel_present(self) -> None:
        source = """
INVALID_RESULT = Result.failure("Invalid")

def foo() -> Result[int]:
    return Result.success(1)
"""
        tree = _parse(source)
        config = {
            "check": {
                "type": "sentinel_exists",
                "sentinel_name": "INVALID_RESULT",
                "condition": "module_has_result_returning_functions",
            },
            "message_template": "Module missing {sentinel} sentinel",
        }
        evaluator = AstModuleCheckEvaluator()
        findings = evaluator.evaluate(tree, config, {"lineage_id": "SC-004"})
        assert findings == []
