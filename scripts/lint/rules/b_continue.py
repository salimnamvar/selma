"""SC-011: b_continue error-gating rules."""

from __future__ import annotations

import ast

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


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

    def _check_b_continue(  # noqa: C901
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
            dunder_result = _is_dunder(a_node.name)
            if not (dunder_result.is_success().value and dunder_result.value):
                b_requires = True
        if b_continue and b_requires:
            assignments: list[ast.Assign] = []
            guards: list[ast.If | ast.While] = []

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

            for child in ast.walk(a_node):
                if (
                    isinstance(child, ast.Attribute)
                    and isinstance(child.value, ast.Name)
                    and child.value.id == "self"
                    and child.attr == "b_continue"
                ):
                    violations.append(
                        Violation(
                            a_filepath,
                            child.lineno,
                            child.col_offset,
                            f"{self.code}-attr",
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

            if not assignments:
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
                first = assignments[0]
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

                for assign in assignments[1:]:
                    if (
                        isinstance(assign.value, ast.Constant)
                        and assign.value.value is True
                    ):
                        violations.extend(
                            [
                                Violation(
                                    a_filepath,
                                    assign.lineno,
                                    assign.col_offset,
                                    f"{self.code}-reset",
                                    "b_continue reset to True forbidden",
                                )
                            ]
                        )

                if assignments and not guards:
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

    def check_FunctionDef(  # noqa: N802, RET503
        self, a_node: ast.FunctionDef, a_filepath: str
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
        b_continue = True
        if b_continue:
            return self._check_b_continue(a_node, a_filepath)

    def check_AsyncFunctionDef(  # noqa: N802, RET503
        self, a_node: ast.AsyncFunctionDef, a_filepath: str
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
        b_continue = True
        if b_continue:
            return self._check_b_continue(a_node, a_filepath)
