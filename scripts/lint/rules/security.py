"""SC-100, SC-101, SC-104: Security rules."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from scripts.lint.config import SecurityConfig
from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

if TYPE_CHECKING:
    from scripts.lint.core.visitor import VisitorContext


class NoEvalExecRule(Rule):
    """SC-104: No eval() or exec() in production code."""

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
            b_result = "SC104"
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
            b_result = "No eval() or exec()"
        return b_result

    def check_call(
        self,
        a_node: ast.Call,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that eval/exec/compile are not called.

        Precondition: a_node is a valid Call AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or
            Ok([]) if compliant.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue and (
            isinstance(a_node.func, ast.Name)
            and a_node.func.id in ("eval", "exec", "compile")
        ):
            violations = [
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    self.code,
                    f"Forbidden call to '{a_node.func.id}()'",
                )
            ]
        return Result.success(violations)


class ParameterizedQueryRule(Rule):
    """SC-101: All database queries must use parameterized queries."""

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
            b_result = "SC101"
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
            b_result = "Parameterized queries (no SQL injection)"
        return b_result

    def check_call(
        self,
        a_node: ast.Call,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that .execute() uses parameterized queries.

        Precondition: a_node is a valid Call AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or
            Ok([]) if compliant.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue and (
            isinstance(a_node.func, ast.Attribute) and a_node.func.attr == "execute"
        ):
            if a_node.args and isinstance(a_node.args[0], (ast.JoinedStr, ast.Call)):
                violations = [
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        self.code,
                        "Possible SQL injection: use parameterized queries",
                    )
                ]
            elif a_node.args and isinstance(a_node.args[0], ast.BinOp):
                if isinstance(a_node.args[0].op, ast.Mod):
                    violations = [
                        Violation(
                            a_filepath,
                            a_node.lineno,
                            a_node.col_offset,
                            self.code,
                            "Possible SQL injection: use parameterized queries",
                        )
                    ]
            elif (
                a_node.args
                and isinstance(a_node.args[0], ast.Call)
                and isinstance(a_node.args[0].func, ast.Attribute)
                and a_node.args[0].func.attr == "format"
            ):
                violations = [
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        self.code,
                        "Possible SQL injection: use parameterized queries",
                    )
                ]
        return Result.success(violations)


class NoSecretsRule(Rule):
    """SC-100: No hardcoded secrets in source code."""

    def __init__(self, config: SecurityConfig | None = None) -> None:
        self._patterns = frozenset((config or SecurityConfig()).secret_patterns)

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
            b_result = "SC100"
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
            b_result = "No hardcoded secrets"
        return b_result

    def _check_name(
        self,
        a_name: str,
        node: ast.AST,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check whether a named assignment contains a hardcoded secret.

        Precondition: a_name is a valid identifier; node is an Assign
            or AnnAssign AST node.
        Postcondition: Returns Ok containing a violation if a secret
            pattern matches, or Ok([]) otherwise.
        Side effect: None.
        Resource: Reads self._patterns.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            name_lower = a_name.lower()
            if any(p in name_lower for p in self._patterns):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id == a_name
                            and isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, str)
                        ):
                            violations = [
                                Violation(
                                    a_filepath,
                                    node.lineno,
                                    node.col_offset,
                                    self.code,
                                    f"Possible hardcoded "
                                    f"secret in '{a_name}'; "
                                    "use environment variable",
                                )
                            ]
                            break
                elif (
                    isinstance(node, ast.AnnAssign)
                    and isinstance(node.target, ast.Name)
                    and node.target.id == a_name
                    and node.value
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    violations = [
                        Violation(
                            a_filepath,
                            node.lineno,
                            node.col_offset,
                            self.code,
                            f"Possible hardcoded "
                            f"secret in '{a_name}'; "
                            "use environment variable",
                        )
                    ]
        return Result.success(violations)

    def check_assign(
        self,
        a_node: ast.Assign,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check assignments for hardcoded secrets.

        Precondition: a_node is a valid Assign AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or
            Ok([]) if compliant.
        Side effect: None.
        Resource: Reads self._patterns via _check_name.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            for target in a_node.targets:
                if isinstance(target, ast.Name):
                    name_result = self._check_name(target.id, a_node, a_filepath)
                    name_violations = (
                        name_result.value if name_result.is_success().value else []
                    )
                    if name_violations:
                        violations = name_violations
                        break
        return Result.success(violations)

    def check_ann_assign(
        self,
        a_node: ast.AnnAssign,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check annotated assignments for hardcoded secrets.

        Precondition: a_node is a valid AnnAssign AST node in the
            file at a_filepath.
        Postcondition: Returns Ok containing violations found, or
            Ok([]) if compliant.
        Side effect: None.
        Resource: Reads self._patterns via _check_name.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue and isinstance(a_node.target, ast.Name):
            name_result = self._check_name(a_node.target.id, a_node, a_filepath)
            violations = name_result.value if name_result.is_success().value else []
        return Result.success(violations)
