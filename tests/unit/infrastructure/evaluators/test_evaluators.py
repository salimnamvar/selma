"""Tests for AST evaluator strategies."""

from __future__ import annotations

import ast

from selma.infrastructure.evaluators.ast_call_check import AstCallCheckEvaluator
from selma.infrastructure.evaluators.ast_context_check import AstContextCheckEvaluator
from selma.infrastructure.evaluators.ast_module_check import AstModuleCheckEvaluator
from selma.infrastructure.evaluators.ast_node_match import AstNodeMatchEvaluator
from selma.infrastructure.evaluators.ast_scope_check import AstScopeCheckEvaluator
from selma.infrastructure.evaluators.ast_walk import AstWalkEvaluator


def _parse(source: str) -> ast.AST:
    return ast.parse(source)


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
