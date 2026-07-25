"""JSON-driven lint rule: reads behavior from JSON config, not Python code.

This is the bridge between JSON rule files and the existing Rule ABC.
The engine loads JSON files, creates JsonRule instances, and the visitor
dispatches to them just like Python rules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import ast

from scripts.lint.core.ast_evaluator import AstEvaluator
from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


class JsonRule(Rule):
    """A lint rule defined entirely by JSON configuration.

    Reads evaluator_type, evaluator_config, message, weight from JSON.
    Uses AstEvaluator to interpret the config against AST nodes.
    """

    def __init__(self, a_config: dict[str, Any]) -> None:
        self._config = a_config
        self._evaluator = AstEvaluator()
        self._code = a_config.get("lineage_id", a_config.get("id", "UNKNOWN"))
        self._description = a_config.get("message", "")
        self._evaluator_type = a_config.get("evaluator_type", "")
        self._evaluator_config = a_config.get("evaluator_config", {})
        self._weight = a_config.get("weight", "medium")
        self._parameters = a_config.get("parameters", {})

    @property
    def code(self) -> str:
        return self._code

    @property
    def description(self) -> str:
        return self._description

    def check_function_def(
        self, a_node: ast.FunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check a FunctionDef node against this JSON rule."""
        return self._check_node(a_node, a_filepath)

    def check_async_function_def(
        self, a_node: ast.AsyncFunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check an AsyncFunctionDef node against this JSON rule."""
        return self._check_node(a_node, a_filepath)

    def check_module(
        self, a_node: ast.Module, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check a Module node against this JSON rule."""
        if self._evaluator_type != "ast_module_check":
            return Result.success([])

        violations_data = self._evaluator.evaluate(
            a_node, self._evaluator_type, self._evaluator_config
        )
        violations = [
            v for vd in violations_data
            for v in [Violation(
                filepath=a_filepath,
                line=vd["line"],
                col=vd["col"],
                code=self._code,
                message=vd["message"],
                severity=self._weight,
            )]
        ]
        return Result.success(violations)

    def check_call(
        self, a_node: ast.Call, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check a Call node against this JSON rule."""
        if self._evaluator_type not in ("ast_call_check", "ast_context_check"):
            return Result.success([])

        violations_data = self._evaluator.evaluate(
            a_node, self._evaluator_type, self._evaluator_config
        )
        violations = [
            v for vd in violations_data
            for v in [Violation(
                filepath=a_filepath,
                line=vd["line"],
                col=vd["col"],
                code=self._code,
                message=vd["message"],
                severity=self._weight,
            )]
        ]
        return Result.success(violations)

    def check_import_from(
        self, a_node: ast.ImportFrom, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check an ImportFrom node against this JSON rule."""
        if self._evaluator_type != "ast_node_match":
            return Result.success([])

        violations_data = self._evaluator.evaluate(
            a_node, self._evaluator_type, self._evaluator_config
        )
        violations = [
            v for vd in violations_data
            for v in [Violation(
                filepath=a_filepath,
                line=vd["line"],
                col=vd["col"],
                code=self._code,
                message=vd["message"],
                severity=self._weight,
            )]
        ]
        return Result.success(violations)

    def _check_node(
        self, a_node: ast.FunctionDef | ast.AsyncFunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Generic node check — delegates to evaluator."""
        if self._evaluator_type in ("ast_walk", "ast_node_match", "ast_scope_check"):
            violations_data = self._evaluator.evaluate(
                a_node, self._evaluator_type, self._evaluator_config
            )
            violations = [
                v for vd in violations_data
                for v in [Violation(
                    filepath=a_filepath,
                    line=vd["line"],
                    col=vd["col"],
                    code=self._code,
                    message=vd["message"],
                    severity=self._weight,
                )]
            ]
            return Result.success(violations)
        return Result.success([])


def load_json_rules(a_rules_dir: str | Path) -> list[JsonRule]:
    """Load all JSON rule files from a directory.

    Each JSON file must be a valid rule conforming to rule_schema.json.
    """
    rules_dir = Path(a_rules_dir)
    if not rules_dir.exists():
        return []

    rules: list[JsonRule] = []
    for json_file in sorted(rules_dir.glob("*.json")):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "evaluator_type" in data:
                rules.append(JsonRule(data))
            elif isinstance(data, dict) and "rules" in data:
                for rule_data in data["rules"]:
                    if "evaluator_type" in rule_data:
                        rules.append(JsonRule(rule_data))
        except (json.JSONDecodeError, OSError):
            continue

    return rules
