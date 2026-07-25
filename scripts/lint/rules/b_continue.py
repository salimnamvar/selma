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
            dunder_result = _is_dunder(a_node.name)
            if not (dunder_result.is_success().value and dunder_result.value):
                b_requires = True
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
        return Result.success(violations)

    def check_function_def(
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
        return Result.success([])

    def check_async_function_def(
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
        return Result.success([])
