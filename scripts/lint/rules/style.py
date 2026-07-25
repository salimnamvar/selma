"""Style rules: a-prefix, function contracts, mutable defaults."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


class APrefixRule(Rule):
    """All function arguments must start with a_ prefix."""

    @property
    def code(self) -> str:
        return "a-prefix"

    @property
    def description(self) -> str:
        return "a_ prefix on all function arguments"

    _EXEMPT = frozenset({"self", "cls"})

    def _check_args(self, args: ast.arguments, filepath: str, func_name: str) -> list[Violation]:
        violations: list[Violation] = []
        for arg in args.args + args.posonlyargs:
            name = arg.arg
            if name in self._EXEMPT or name.startswith("a_") or name.startswith("_a_"):
                continue
            violations.append(Violation(
                filepath, arg.lineno, arg.col_offset,
                self.code,
                f"Argument '{name}' in '{func_name}' must start with 'a_'",
            ))
        for arg in args.kwonlyargs:
            name = arg.arg
            if name in self._EXEMPT or name.startswith("a_") or name.startswith("_a_"):
                continue
            violations.append(Violation(
                filepath, arg.lineno, arg.col_offset,
                self.code,
                f"Argument '{name}' in '{func_name}' must start with 'a_'",
            ))
        return violations

    def check_FunctionDef(self, node: ast.FunctionDef, filepath: str) -> list[Violation]:
        if node.name.startswith("__") and node.name.endswith("__"):
            return []
        return self._check_args(node.args, filepath, node.name)

    check_AsyncFunctionDef = check_FunctionDef


class FunctionContractRule(Rule):
    """SC-013: Every function must have a docstring."""

    @property
    def code(self) -> str:
        return "SC013"

    @property
    def description(self) -> str:
        return "Function docstring contracts"

    def check_FunctionDef(self, node: ast.FunctionDef, filepath: str) -> list[Violation]:
        if node.name.startswith("__") and node.name.endswith("__"):
            return []
        if not ast.get_docstring(node):
            return [Violation(
                filepath, node.lineno, node.col_offset,
                self.code,
                f"Function '{node.name}' missing docstring",
            )]
        return []

    check_AsyncFunctionDef = check_FunctionDef


class NoMutableDefaultRule(Rule):
    """No mutable default arguments in function signatures."""

    @property
    def code(self) -> str:
        return "mutable-default"

    @property
    def description(self) -> str:
        return "No mutable default arguments"

    def check_FunctionDef(self, node: ast.FunctionDef, filepath: str) -> list[Violation]:
        violations: list[Violation] = []
        for default in node.args.defaults + node.args.kw_defaults:
            if default is not None and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                violations.append(Violation(
                    filepath, default.lineno, default.col_offset,
                    self.code,
                    "Mutable default argument forbidden; use None and initialize inside function",
                ))
        return violations

    check_AsyncFunctionDef = check_FunctionDef
