"""SC-070, SC-071: State and determinism rules."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.config import DeterminismConfig



class DeterminismRule(Rule):
    """SC-071: No non-deterministic calls in business logic."""

    def __init__(self, config: DeterminismConfig | None = None) -> None:
        raw = (config or DeterminismConfig()).forbidden
        self._forbidden: dict[str, set[str]] = {}
        for entry in raw:
            if "." in entry:
                mod, method = entry.split(".", 1)
                self._forbidden.setdefault(mod, set()).add(method)

    @property
    def code(self) -> str:
        return "SC071"

    @property
    def description(self) -> str:
        return "Deterministic execution (no datetime.now/random/etc.)"

    def check_Call(self, a_node: ast.Call, a_filepath: str) -> list[Violation]:
        """Check for non-deterministic function calls."""
        violations: list[Violation] = []
        if isinstance(a_node.func, ast.Attribute) and isinstance(a_node.func.value, ast.Name):
            mod = a_node.func.value.id
            meth = a_node.func.attr
            if mod in self._forbidden and meth in self._forbidden[mod]:
                violations = [Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    f"Non-deterministic call '{mod}.{meth}()' forbidden; inject time/random source",
                )]
        return violations


class NoModuleLevelMutableRule(Rule):
    """SC-070: No module-level variable assignments."""

    @property
    def code(self) -> str:
        return "SC070"

    @property
    def description(self) -> str:
        return "No module-level variables"

    def check_Module(self, a_node: ast.Module, a_filepath: str) -> list[Violation]:
        """Check that no mutable module-level variables are defined."""
        violations: list[Violation] = []
        for stmt in a_node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.isupper() or name.startswith("_"):
                            continue
                        violations.append(Violation(
                            a_filepath, stmt.lineno, stmt.col_offset,
                            self.code,
                            f"Module-level variable '{name}' forbidden; move into function or class",
                        ))
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                name = stmt.target.id
                if name.isupper() or name.startswith("_"):
                    continue
                if stmt.value is not None:
                    violations.append(Violation(
                        a_filepath, stmt.lineno, stmt.col_offset,
                        self.code,
                        f"Module-level variable '{name}' forbidden; move into function or class",
                    ))
        return violations
