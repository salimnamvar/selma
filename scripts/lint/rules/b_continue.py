"""SC-011: b_continue error-gating rules."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation



def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _returns_result(node: ast.FunctionDef) -> bool:
    if node.returns is None:
        return False
    if isinstance(node.returns, ast.Name) and node.returns.id == "Result":
        return True
    if isinstance(node.returns, ast.Subscript) and isinstance(node.returns.value, ast.Name):
        return node.returns.value.id == "Result"
    return False


class BContinueRule(Rule):
    """SC-011: b_continue must be function-local, init True, transition True->False only."""

    @property
    def code(self) -> str:
        return "SC011"

    @property
    def description(self) -> str:
        return "b_continue one-way transition rules"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> list[Violation]:
        """Check b_continue usage rules in a function."""
        if _is_dunder(a_node.name):
            return []
        requires_b_continue = _returns_result(a_node)
        if not requires_b_continue:
            for child in ast.walk(a_node):
                if isinstance(child, ast.Try):
                    requires_b_continue = True
                    break
        if not requires_b_continue:
            return []

        violations: list[Violation] = []
        assignments: list[ast.Assign] = []
        guards: list[ast.If | ast.While] = []

        param_names = {arg.arg for arg in a_node.args.args + a_node.args.posonlyargs + a_node.args.kwonlyargs}
        if "b_continue" in param_names:
            violations.append(Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                f"{self.code}-param",
                "b_continue must not be a function parameter",
            ))

        for child in ast.walk(a_node):
            if isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name) and child.value.id == "self" and child.attr == "b_continue":
                    violations.append(Violation(
                        a_filepath, child.lineno, child.col_offset,
                        f"{self.code}-attr",
                        "b_continue must not be accessed as an instance attribute",
                    ))
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == "b_continue":
                        assignments.append(child)
            elif isinstance(child, (ast.If, ast.While)):
                if "b_continue" in ast.dump(child.test):
                    guards.append(child)

        if not assignments:
            violations.append(Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                f"{self.code}-missing",
                f"Function '{a_node.name}' lacks b_continue",
            ))
        else:
            first = assignments[0]
            if not (isinstance(first.value, ast.Constant) and first.value.value is True):
                violations.append(Violation(
                    a_filepath, first.lineno, first.col_offset,
                    f"{self.code}-init",
                    "b_continue must be initialized to True",
                ))

            for assign in assignments[1:]:
                if isinstance(assign.value, ast.Constant) and assign.value.value is True:
                    violations.append(Violation(
                        a_filepath, assign.lineno, assign.col_offset,
                        f"{self.code}-reset",
                        "b_continue reset to True forbidden",
                    ))

            if assignments and not guards:
                violations.append(Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    f"{self.code}-unused",
                    "b_continue initialized but never used as guard",
                ))

        return violations

    check_AsyncFunctionDef = check_FunctionDef
