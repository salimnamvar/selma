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
    ret_str = ast.dump(node.returns)
    return "Result" in ret_str


class BContinueRule(Rule):
    """SC-011: b_continue must be function-local, init True, transition True->False only."""

    @property
    def code(self) -> str:
        return "SC011"

    @property
    def description(self) -> str:
        return "b_continue one-way transition rules"

    def check_FunctionDef(self, node: ast.FunctionDef, filepath: str) -> list[Violation]:
        if _is_dunder(node.name):
            return []

        has_result_return = _returns_result(node)
        if not has_result_return:
            return []

        violations: list[Violation] = []
        assignments: list[ast.Assign] = []
        guards: list[ast.If | ast.While] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == "b_continue":
                        assignments.append(child)
            elif isinstance(child, (ast.If, ast.While)):
                if "b_continue" in ast.dump(child.test):
                    guards.append(child)

        if not assignments:
            return [Violation(
                filepath, node.lineno, node.col_offset,
                f"{self.code}-missing",
                f"Function '{node.name}' lacks b_continue",
            )]

        first = assignments[0]
        if not (isinstance(first.value, ast.Constant) and first.value.value is True):
            violations.append(Violation(
                filepath, first.lineno, first.col_offset,
                f"{self.code}-init",
                "b_continue must be initialized to True",
            ))

        for assign in assignments[1:]:
            if isinstance(assign.value, ast.Constant) and assign.value.value is True:
                violations.append(Violation(
                    filepath, assign.lineno, assign.col_offset,
                    f"{self.code}-reset",
                    "b_continue reset to True forbidden",
                ))

        if assignments and not guards:
            violations.append(Violation(
                filepath, node.lineno, node.col_offset,
                f"{self.code}-unused",
                "b_continue initialized but never used as guard",
            ))

        return violations

    check_AsyncFunctionDef = check_FunctionDef
