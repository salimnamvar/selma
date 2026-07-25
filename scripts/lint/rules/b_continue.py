"""SC-011: b_continue error-gating rules."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

if TYPE_CHECKING:
    from scripts.lint.core.visitor import VisitorContext


def _is_dunder(name: str) -> Result[bool]:
    """Check whether name is a dunder identifier.

    Precondition: name is a non-empty string.
    Postcondition: Returns Ok(True) if name starts and ends with
        '__', Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    b_result: bool = False
    if b_continue:
        b_result = name.startswith("__") and name.endswith("__")
    return Result.success(b_result)


class BContinueRule(Rule):
    """SC-011: All non-dunder functions must have b_continue."""

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
            b_result = "SC011"
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
            b_result = "b_continue one-way transition rules"
        return b_result

    @staticmethod
    def _collect_children(
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> Result[tuple[list[ast.Assign], list[ast.If | ast.While], list[Violation]]]:
        """Walk function body collecting assignments, guards, and attribute violations.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node.
        Postcondition: Returns Ok with (assignments, guards, attribute_violations).
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        assignments: list[ast.Assign] = []
        guards: list[ast.If | ast.While] = []
        attr_violations: list[Violation] = []
        if b_continue:
            for child in ast.walk(a_node):
                if (
                    isinstance(child, ast.Attribute)
                    and isinstance(child.value, ast.Name)
                    and child.value.id == "self"
                    and child.attr == "b_continue"
                ):
                    attr_violations.append(
                        Violation(
                            "",
                            child.lineno,
                            child.col_offset,
                            "SC011-attr",
                            "b_continue must not be accessed as an instance attribute",
                        )
                    )
                if isinstance(child, ast.Assign):
                    assignments.extend(
                        child
                        for target in child.targets
                        if isinstance(target, ast.Name) and target.id == "b_continue"
                    )
                elif isinstance(
                    child, (ast.If, ast.While)
                ) and "b_continue" in ast.dump(child.test):
                    guards.append(child)
        return Result.success((assignments, guards, attr_violations))

    def _check_assignments(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_assignments: list[ast.Assign],
        a_guards: list[ast.If | ast.While],
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check b_continue assignment and guard usage rules.

        Precondition: a_assignments and a_guards are pre-collected from the function.
        Postcondition: Returns Result with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            if not a_assignments:
                violations.append(
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        f"{self.code}-missing",
                        f"Function '{a_node.name}' lacks b_continue",
                    )
                )
            else:
                first = a_assignments[0]
                if not (
                    isinstance(first.value, ast.Constant) and first.value.value is True
                ):
                    violations.append(
                        Violation(
                            a_filepath,
                            first.lineno,
                            first.col_offset,
                            f"{self.code}-init",
                            "b_continue must be initialized to True",
                        )
                    )
                violations.extend(
                    Violation(
                        a_filepath,
                        assign.lineno,
                        assign.col_offset,
                        f"{self.code}-reset",
                        "b_continue reset to True forbidden",
                    )
                    for assign in a_assignments[1:]
                    if (
                        isinstance(assign.value, ast.Constant)
                        and assign.value.value is True
                    )
                )
                if not a_guards:
                    violations.append(
                        Violation(
                            a_filepath,
                            a_node.lineno,
                            a_node.col_offset,
                            f"{self.code}-unused",
                            "b_continue initialized but never used as guard",
                        )
                    )
        return Result.success(violations)

    def _has_false_assignment(
        self,
        a_assignments: list[ast.Assign],
    ) -> Result[bool]:
        """Check whether b_continue is ever assigned False.

        Precondition: a_assignments are collected b_continue Assign nodes.
        Postcondition: Returns Ok(True) if any assignment is = False.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result = False
        if b_continue:
            for assign in a_assignments:
                b_is_false = (
                    isinstance(assign.value, ast.Constant)
                    and assign.value.value is False
                )
                if b_is_false:
                    b_result = True
                    break
        return Result.success(b_result)

    @staticmethod
    def _is_b_continue_guard(a_stmt: ast.If) -> Result[bool]:
        """Check if statement is an if b_continue: guard with no else.

        Precondition: a_stmt is an If AST node.
        Postcondition: Returns Ok(True) if it is a b_continue guard.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result = False
        if b_continue:
            b_result = (
                isinstance(a_stmt.test, ast.Name)
                and a_stmt.test.id == "b_continue"
                and not a_stmt.orelse
            )
        return Result.success(b_result)

    def _check_unreachable_after_guard(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_assignments: list[ast.Assign],
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check for unreachable code after always-true b_continue guard.

        Detects: b_continue = True; if b_continue: return X; return Y
        where Y is unreachable because b_continue is never False.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node;
            a_assignments are collected b_continue assignments.
        Postcondition: Returns Result with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        b_has_false = False
        if b_continue:
            false_result = self._has_false_assignment(a_assignments)
            if false_result.is_success().value and false_result.value:
                b_has_false = True
        if b_continue and not b_has_false:
            body = a_node.body
            for i, stmt in enumerate(body):
                if not isinstance(stmt, ast.If):
                    continue
                guard_result = self._is_b_continue_guard(stmt)
                if not (guard_result.is_success().value and guard_result.value):
                    continue
                has_return = any(isinstance(s, ast.Return) for s in ast.walk(stmt))
                if has_return and i < len(body) - 1:
                    violations.append(
                        Violation(
                            a_filepath,
                            body[i + 1].lineno,
                            body[i + 1].col_offset,
                            f"{self.code}-unreachable",
                            "Unreachable code after always-true "
                            "b_continue guard; remove the "
                            "b_continue pattern and return "
                            "directly",
                        )
                    )
        return Result.success(violations)

    @staticmethod
    def _is_pure_delegation(
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> Result[bool]:
        """Check if function is a single-return delegation.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef.
        Postcondition: Returns Ok(True) if the function body is exactly
            one return statement (optionally preceded by a docstring).
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result = False
        if b_continue:
            body = a_node.body
            b_two_stmt_docstring = (
                len(body) == 2
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[1], ast.Return)
                and isinstance(body[1].value, ast.Call)
                and isinstance(body[1].value.func, ast.Attribute)
                and isinstance(body[1].value.func.value, ast.Name)
                and body[1].value.func.value.id == "self"
            )
            b_one_stmt_return = (
                len(body) == 1
                and isinstance(body[0], ast.Return)
                and isinstance(body[0].value, ast.Call)
                and isinstance(body[0].value.func, ast.Attribute)
                and isinstance(body[0].value.func.value, ast.Name)
                and body[0].value.func.value.id == "self"
            )
            if b_two_stmt_docstring or b_one_stmt_return:
                b_result = True
        return Result.success(b_result)

    def _requires_b_continue(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> Result[bool]:
        """Check whether function requires b_continue pattern.

        Exempts dunders and pure delegation functions.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef.
        Postcondition: Returns Ok(True) if function requires b_continue.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result = False
        b_is_delegation = False
        if b_continue:
            delegation_result = self._is_pure_delegation(a_node)
            if delegation_result.is_success().value and delegation_result.value:
                b_is_delegation = True
        if b_continue and not b_is_delegation:
            dunder_result = _is_dunder(a_node.name)
            if not (dunder_result.is_success().value and dunder_result.value):
                b_result = True
        return Result.success(b_result)

    def _check_b_continue(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check b_continue usage rules in a function.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC011 violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        b_requires = False
        if b_continue:
            req_result = self._requires_b_continue(a_node)
            if req_result.is_success().value:
                b_requires = req_result.value
        if b_continue and b_requires:
            param_names = {
                arg.arg
                for arg in (
                    a_node.args.args + a_node.args.posonlyargs + a_node.args.kwonlyargs
                )
            }
            if "b_continue" in param_names:
                violations.append(
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        f"{self.code}-param",
                        "b_continue must not be a function parameter",
                    )
                )
            children_result = self._collect_children(a_node)
            if children_result.is_success().value:
                assignments, guards, attr_viols = children_result.value
                violations.extend(attr_viols)
                check_result = self._check_assignments(
                    a_node, assignments, guards, a_filepath
                )
                if check_result.is_success().value:
                    violations.extend(check_result.value)
                unreach_result = self._check_unreachable_after_guard(
                    a_node, assignments, a_filepath
                )
                if unreach_result.is_success().value:
                    violations.extend(unreach_result.value)
        return Result.success(violations)

    def check_function_def(
        self,
        a_node: ast.FunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check b_continue usage rules in a function.

        Precondition: a_node is a FunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC011 violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        return self._check_b_continue(a_node, a_filepath)

    def check_async_function_def(
        self,
        a_node: ast.AsyncFunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check b_continue usage rules in an async function.

        Precondition: a_node is an AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC011 violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        return self._check_b_continue(a_node, a_filepath)
