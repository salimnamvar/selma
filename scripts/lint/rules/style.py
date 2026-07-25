"""Style rules: a-prefix, function contracts, mutable defaults."""
from __future__ import annotations

import ast

from scripts.lint.core.result import Result
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

    def _check_args(self, a_args: ast.arguments, a_filepath: str, a_func_name: str) -> Result[list[Violation]]:
        """Check individual argument names for a_ prefix compliance.

        Precondition: a_args is a valid ast.arguments node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
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
            result = Result.success(violations)
        return result

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> Result[list[Violation]]:
        """Check that all function arguments have a_ prefix.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            if not (a_node.name.startswith("__") and a_node.name.endswith("__")):
                if not a_node.name.startswith("_"):
                    args_result = self._check_args(a_node.args, a_filepath, a_node.name)
                    if args_result.is_success():
                        violations = args_result.value
            result = Result.success(violations)
        return result

    check_AsyncFunctionDef = check_FunctionDef


class FunctionContractRule(Rule):
    """SC-013: Every function must have a docstring."""

    @property
    def code(self) -> str:
        return "SC013"

    @property
    def description(self) -> str:
        return "Function docstring contracts"

    _REQUIRED_SECTIONS = frozenset({
        "precondition", "postcondition", "side effect", "resource", "failure",
    })

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> Result[list[Violation]]:
        """Check that functions have docstrings with all 5 mandatory contract sections.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            if not (a_node.name.startswith("__") and a_node.name.endswith("__")):
                exempt = False
                for dec in a_node.decorator_list:
                    if isinstance(dec, ast.Name) and dec.id in ("property", "staticmethod", "classmethod"):
                        exempt = True
                        break
                    if isinstance(dec, ast.Attribute) and dec.attr in ("setter", "getter", "deleter"):
                        exempt = True
                        break
                if not exempt:
                    docstring = ast.get_docstring(a_node)
                    if not docstring:
                        violations = [Violation(
                            a_filepath, a_node.lineno, a_node.col_offset,
                            self.code,
                            f"Function '{a_node.name}' missing docstring",
                        )]
                    else:
                        doc_lower = docstring.lower()
                        missing = [s for s in self._REQUIRED_SECTIONS if s not in doc_lower]
                        if missing:
                            violations = [Violation(
                                a_filepath, a_node.lineno, a_node.col_offset,
                                self.code,
                                f"Function '{a_node.name}' docstring missing contract sections: {', '.join(missing)}",
                            )]
            result = Result.success(violations)
        return result

    check_AsyncFunctionDef = check_FunctionDef


class NoMutableDefaultRule(Rule):
    """No mutable default arguments in function signatures."""

    @property
    def code(self) -> str:
        return "mutable-default"

    @property
    def description(self) -> str:
        return "No mutable default arguments"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> Result[list[Violation]]:
        """Check that function defaults are not mutable.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            for default in a_node.args.defaults + a_node.args.kw_defaults:
                if default is not None and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    violations.append(Violation(
                        a_filepath, default.lineno, default.col_offset,
                        self.code,
                        "Mutable default argument forbidden; use None and initialize inside function",
                    ))
            result = Result.success(violations)
        return result

    check_AsyncFunctionDef = check_FunctionDef
