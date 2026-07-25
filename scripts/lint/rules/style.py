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

    _EXEMPT = frozenset({"self", "cls", "args", "kwargs"})

    def _check_args(self, a_args: ast.arguments, a_filepath: str, a_func_name: str) -> list[Violation]:
        violations: list[Violation] = []
        for arg in a_args.args + a_args.posonlyargs:
            name = arg.arg
            if name in self._EXEMPT or name.startswith("a_") or name.startswith("_a_") or name.startswith("*"):
                continue
            violations.append(Violation(
                a_filepath, arg.lineno, arg.col_offset,
                self.code,
                f"Argument '{name}' in '{a_func_name}' must start with 'a_'",
            ))
        for arg in a_args.kwonlyargs:
            name = arg.arg
            if name in self._EXEMPT or name.startswith("a_") or name.startswith("_a_"):
                continue
            violations.append(Violation(
                a_filepath, arg.lineno, arg.col_offset,
                self.code,
                f"Argument '{name}' in '{a_func_name}' must start with 'a_'",
            ))
        return violations

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that all function arguments have a_ prefix."""
        violations: list[Violation] = []
        if not (a_node.name.startswith("__") and a_node.name.endswith("__")):
            if not a_node.name.startswith("_"):
                violations = self._check_args(a_node.args, a_filepath, a_node.name)
        return violations

    check_AsyncFunctionDef = check_FunctionDef


class FunctionContractRule(Rule):
    """SC-013: Every function must have a docstring."""

    @property
    def code(self) -> str:
        return "SC013"

    @property
    def description(self) -> str:
        return "Function docstring contracts"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that public functions have docstrings."""
        violations: list[Violation] = []
        if not (a_node.name.startswith("__") and a_node.name.endswith("__")):
            if not a_node.name.startswith("_"):
                exempt = False
                for dec in a_node.decorator_list:
                    if isinstance(dec, ast.Name) and dec.id in ("property", "staticmethod", "classmethod"):
                        exempt = True
                        break
                    if isinstance(dec, ast.Attribute) and dec.attr in ("setter", "getter", "deleter"):
                        exempt = True
                        break
                if not exempt and not ast.get_docstring(a_node):
                    violations = [Violation(
                        a_filepath, a_node.lineno, a_node.col_offset,
                        self.code,
                        f"Function '{a_node.name}' missing docstring",
                    )]
        return violations

    check_AsyncFunctionDef = check_FunctionDef


class NoMutableDefaultRule(Rule):
    """No mutable default arguments in function signatures."""

    @property
    def code(self) -> str:
        return "mutable-default"

    @property
    def description(self) -> str:
        return "No mutable default arguments"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check that function defaults are not mutable."""
        violations: list[Violation] = []
        for default in a_node.args.defaults + a_node.args.kw_defaults:
            if default is not None and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                violations.append(Violation(
                    a_filepath, default.lineno, default.col_offset,
                    self.code,
                    "Mutable default argument forbidden; use None and initialize inside function",
                ))
        return violations

    check_AsyncFunctionDef = check_FunctionDef
