"""Style rules: a-prefix, function contracts, mutable defaults."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

if TYPE_CHECKING:
    from scripts.lint.core.visitor import VisitorContext


class APrefixRule(Rule):
    """All function arguments must start with a_ prefix."""

    @property
    def code(self) -> str:
        """Short rule identifier, e.g. 'SC001'.

        Precondition: None.
        Postcondition: Returns the rule code string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = "a-prefix"
        return b_result

    @property
    def description(self) -> str:
        """One-line human description.

        Precondition: None.
        Postcondition: Returns the rule description string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = "a_ prefix on all function arguments"
        return b_result

    _EXEMPT = frozenset({"self", "cls", "args", "kwargs"})

    def _check_args(
        self,
        a_args: ast.arguments,
        a_filepath: str,
        a_func_name: str,
    ) -> Result[list[Violation]]:
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
                if name in self._EXEMPT or name.startswith(("a_", "_a_", "*")):
                    continue
                violations.append(
                    Violation(
                        a_filepath,
                        arg.lineno,
                        arg.col_offset,
                        self.code,
                        f"Argument '{name}' in '{a_func_name}' must start with 'a_'",
                    )
                )
            for arg in a_args.kwonlyargs:
                name = arg.arg
                if name in self._EXEMPT or name.startswith(("a_", "_a_")):
                    continue
                violations.append(
                    Violation(
                        a_filepath,
                        arg.lineno,
                        arg.col_offset,
                        self.code,
                        f"Argument '{name}' in '{a_func_name}' must start with 'a_'",
                    )
                )
            result = Result.success(violations)
        return result

    def _check_function(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check that all function arguments have a_ prefix.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            is_dunder = a_node.name.startswith("__") and a_node.name.endswith("__")
            is_private = a_node.name.startswith("_")
            if not is_dunder and not is_private:
                args_result = self._check_args(a_node.args, a_filepath, a_node.name)
                if args_result.is_success().value:
                    violations = args_result.value
            result = Result.success(violations)
        return result

    def check_function_def(
        self,
        a_node: ast.FunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that all function arguments have a_ prefix.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        return self._check_function(a_node, a_filepath)

    def check_async_function_def(
        self,
        a_node: ast.AsyncFunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that all async function arguments have a_ prefix.

        Precondition: a_node is an AsyncFunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        return self._check_function(a_node, a_filepath)


class FunctionContractRule(Rule):
    """SC-013: Every function must have a docstring."""

    @property
    def code(self) -> str:
        """Short rule identifier, e.g. 'SC001'.

        Precondition: None.
        Postcondition: Returns the rule code string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = "SC013"
        return b_result

    @property
    def description(self) -> str:
        """One-line human description.

        Precondition: None.
        Postcondition: Returns the rule description string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = "Function docstring contracts"
        return b_result

    _REQUIRED_SECTIONS = frozenset(
        {
            "precondition",
            "postcondition",
            "side effect",
            "resource",
            "failure",
        }
    )

    @staticmethod
    def _is_exempt_decorator(
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> Result[bool]:
        """Check whether a function has an exempt decorator.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node.
        Postcondition: Returns Ok(True) if function has an exempt decorator.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result = False
        if b_continue:
            for dec in a_node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id in (
                    "property",
                    "staticmethod",
                    "classmethod",
                ):
                    b_result = True
                    break
                if isinstance(dec, ast.Attribute) and dec.attr in (
                    "setter",
                    "getter",
                    "deleter",
                ):
                    b_result = True
                    break
        return Result.success(b_result)

    def _check_docstring(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check that a function has a docstring with all required sections.

        Precondition: a_node is not a dunder and not an exempt decorator.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            docstring = ast.get_docstring(a_node)
            if not docstring:
                violations = [
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        self.code,
                        f"Function '{a_node.name}' missing docstring",
                    )
                ]
            else:
                doc_lower = docstring.lower()
                missing = [s for s in self._REQUIRED_SECTIONS if s not in doc_lower]
                if missing:
                    joined = ", ".join(missing)
                    violations = [
                        Violation(
                            a_filepath,
                            a_node.lineno,
                            a_node.col_offset,
                            self.code,
                            f"Function '{a_node.name}' "
                            "docstring missing contract "
                            f"sections: {joined}",
                        )
                    ]
        return Result.success(violations)

    def _check_function(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check that functions have docstrings with contract sections.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            is_dunder = a_node.name.startswith("__") and a_node.name.endswith("__")
            if not is_dunder:
                exempt_result = self._is_exempt_decorator(a_node)
                if not (exempt_result.is_success().value and exempt_result.value):
                    doc_result = self._check_docstring(a_node, a_filepath)
                    if doc_result.is_success().value:
                        violations = doc_result.value
            result = Result.success(violations)
        return result

    def check_function_def(
        self,
        a_node: ast.FunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that functions have docstrings with all 5 mandatory sections.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        return self._check_function(a_node, a_filepath)

    def check_async_function_def(
        self,
        a_node: ast.AsyncFunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that async functions have docstrings with all 5 sections.

        Precondition: a_node is an AsyncFunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        return self._check_function(a_node, a_filepath)


class NoMutableDefaultRule(Rule):
    """No mutable default arguments in function signatures."""

    @property
    def code(self) -> str:
        """Short rule identifier, e.g. 'SC001'.

        Precondition: None.
        Postcondition: Returns the rule code string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = "mutable-default"
        return b_result

    @property
    def description(self) -> str:
        """One-line human description.

        Precondition: None.
        Postcondition: Returns the rule description string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = "No mutable default arguments"
        return b_result

    def _check_function(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check that function defaults are not mutable.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]] = Result.success(violations)
        if b_continue:
            violations.extend(
                Violation(
                    a_filepath,
                    d.lineno,
                    d.col_offset,
                    self.code,
                    "Mutable default argument "
                    "forbidden; use None and "
                    "initialize inside function",
                )
                for d in (a_node.args.defaults + a_node.args.kw_defaults)
                if d is not None and isinstance(d, (ast.List, ast.Dict, ast.Set))
            )
            result = Result.success(violations)
        return result

    def check_function_def(
        self,
        a_node: ast.FunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that function defaults are not mutable.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        return self._check_function(a_node, a_filepath)

    def check_async_function_def(
        self,
        a_node: ast.AsyncFunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that async function defaults are not mutable.

        Precondition: a_node is an AsyncFunctionDef AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (always returns Ok).
        """
        return self._check_function(a_node, a_filepath)
