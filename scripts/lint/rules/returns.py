"""SC-003, SC-005, SC-024, SC-025: Return type and result rules."""

from __future__ import annotations

import ast

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


class ResultReturnRule(Rule):
    """SC-003/005: Functions returning values must use Result[T], no tuple returns."""

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
            b_result = "SC003"
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
            b_result = "Result[T] returns, no tuples"
        return b_result

    def _is_result_type(self, a_node: ast.expr | None) -> Result[bool]:
        """Check whether an AST annotation node represents a Result type.

        Precondition: a_node is an optional AST expression node.
        Postcondition: Returns Result.success(True) if the annotation
            is Result or Result[T].
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: bool = False
        if b_continue:
            if a_node is None:
                b_result = False
            elif isinstance(a_node, ast.Name) and a_node.id == "Result":
                b_result = True
            elif isinstance(a_node, ast.Subscript) and isinstance(
                a_node.value, ast.Name
            ):
                b_result = a_node.value.id == "Result"
        return Result.success(b_result)

    def _is_none_annotation(self, a_node: ast.expr | None) -> Result[bool]:
        """Check whether an AST annotation node represents a None type.

        Precondition: a_node is an optional AST expression node.
        Postcondition: Returns Result.success(True) if the annotation
            is None or NoneType.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: bool = False
        if b_continue:
            b_result = (
                a_node is None
                or (isinstance(a_node, ast.Constant) and a_node.value is None)
                or (isinstance(a_node, ast.Name) and a_node.id == "None")
            )
        return Result.success(b_result)

    def _has_return_value(self, a_node: ast.FunctionDef) -> Result[bool]:
        """Check whether a function has any return statement with a value.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Result.success(True) if function has
            return with value.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: bool = False
        if b_continue:
            for child in ast.walk(a_node):
                if (
                    isinstance(
                        child,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    )
                    and child is not a_node
                ):
                    continue
                if isinstance(child, ast.Return) and child.value is not None:
                    b_result = True
                    break
        return Result.success(b_result)

    def _is_exempt(self, a_name: str) -> Result[bool]:
        """Check whether a function name is exempt from Result checks.

        Precondition: a_name is a function name string.
        Postcondition: Returns Result.success(True) if the name is
            a dunder.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: bool = False
        if b_continue and (a_name.startswith("__") and a_name.endswith("__")):
            b_result = True
        return Result.success(b_result)

    def _is_property_or_abstract(self, a_node: ast.FunctionDef) -> Result[bool]:
        """Check whether a function has exempt decorators.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Result.success(True) if the function
            has an exempt decorator.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: bool = False
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
                    "abstractmethod",
                ):
                    b_result = True
                    break
                if isinstance(dec, ast.Name) and dec.id == "abstractmethod":
                    b_result = True
                    break
        return Result.success(b_result)

    def _check_function(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check that functions do not return tuples and use Result[T].

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC003/SC005 violations.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        b_skip = False
        if b_continue:
            for child in ast.walk(a_node):
                if (
                    isinstance(
                        child,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    )
                    and child is not a_node
                ):
                    continue
                if (
                    isinstance(child, ast.Return)
                    and child.value is not None
                    and isinstance(child.value, ast.Tuple)
                ):
                    violations.append(
                        Violation(
                            a_filepath,
                            child.lineno,
                            child.col_offset,
                            "SC005",
                            f"Function '{a_node.name}' returns a tuple; use Result[T]",
                        )
                    )
        exempt_result = (
            self._is_exempt(a_node.name)
            if b_continue
            else Result.success(a_value=False)
        )
        if b_continue and exempt_result.is_success().value and exempt_result.value:
            b_skip = True
        prop_result = (
            self._is_property_or_abstract(a_node)  # type: ignore[arg-type]
            if b_continue and not b_skip
            else Result.success(a_value=False)
        )
        if (
            b_continue
            and not b_skip
            and prop_result.is_success().value
            and prop_result.value
        ):
            b_skip = True
        if b_continue and not b_skip:
            has_return_result = self._has_return_value(a_node)  # type: ignore[arg-type]
            has_return_value = (
                has_return_result.is_success().value and has_return_result.value
            )
            none_result = self._is_none_annotation(a_node.returns)
            is_none = none_result.is_success().value and none_result.value
            result_type_result = self._is_result_type(a_node.returns)
            is_result_type = (
                result_type_result.is_success().value and result_type_result.value
            )
            if not is_none:
                if is_result_type:
                    pass
                elif a_node.returns is not None and has_return_value:
                    violations.append(
                        Violation(
                            a_filepath,
                            a_node.lineno,
                            a_node.col_offset,
                            self.code,
                            f"Function '{a_node.name}' returns "
                            "values but type is not Result[T]",
                        )
                    )
                elif a_node.returns is None and has_return_value:
                    violations.append(
                        Violation(
                            a_filepath,
                            a_node.lineno,
                            a_node.col_offset,
                            self.code,
                            f"Function '{a_node.name}' missing "
                            "return type (must be Result[T])",
                        )
                    )
        return Result.success(violations)

    def check_FunctionDef(
        self, a_node: ast.FunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that functions do not return tuples and use Result[T].

        Precondition: a_node is a FunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC003/SC005 violations.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        if b_continue:
            return self._check_function(a_node, a_filepath)
        return Result.success([])

    def check_AsyncFunctionDef(
        self, a_node: ast.AsyncFunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that async functions do not return tuples and use Result[T].

        Precondition: a_node is an AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC003/SC005 violations.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        if b_continue:
            return self._check_function(a_node, a_filepath)
        return Result.success([])


class ExplicitReturnTypeRule(Rule):
    """SC-024: Every function must have an explicit return type annotation."""

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
            b_result = "SC024"
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
            b_result = "Explicit return type annotation"
        return b_result

    def _check_function(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check that functions have explicit return type annotations.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC024 violations.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        b_skip = False
        if b_continue and (a_node.name.startswith("__") and a_node.name.endswith("__")):
            b_skip = True
        if b_continue and not b_skip:
            for dec in a_node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == "abstractmethod":
                    b_skip = True
                    break
                if isinstance(dec, ast.Attribute) and dec.attr == "abstractmethod":
                    b_skip = True
                    break
        if b_continue and not b_skip and a_node.returns is None:
            violations = [
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    self.code,
                    f"Function '{a_node.name}' missing return type annotation",
                )
            ]
        return Result.success(violations)

    def check_FunctionDef(
        self, a_node: ast.FunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that functions have explicit return type annotations.

        Precondition: a_node is a FunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC024 violations.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        if b_continue:
            return self._check_function(a_node, a_filepath)
        return Result.success([])

    def check_AsyncFunctionDef(
        self, a_node: ast.AsyncFunctionDef, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that async functions have explicit return type annotations.

        Precondition: a_node is an AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC024 violations.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        if b_continue:
            return self._check_function(a_node, a_filepath)
        return Result.success([])


class NoStarImportRule(Rule):
    """SC-025: No wildcard imports."""

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
            b_result = "SC025"
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
            b_result = "No wildcard imports"
        return b_result

    def check_ImportFrom(
        self, a_node: ast.ImportFrom, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that no wildcard imports are used.

        Precondition: a_node is an ImportFrom AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC025 violations.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            for alias in a_node.names:
                if alias.name == "*":
                    module = a_node.module or ""
                    violations = [
                        Violation(
                            a_filepath,
                            a_node.lineno,
                            a_node.col_offset,
                            self.code,
                            f"Wildcard import from '{module}' forbidden",
                        )
                    ]
                    break
        return Result.success(violations)
