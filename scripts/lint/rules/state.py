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

    def check_Call(self, node: ast.Call, filepath: str) -> list[Violation]:
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            mod = node.func.value.id
            meth = node.func.attr
            if mod in self._forbidden and meth in self._forbidden[mod]:
                return [Violation(
                    filepath, node.lineno, node.col_offset,
                    self.code,
                    f"Non-deterministic call '{mod}.{meth}()' forbidden; inject time/random source",
                )]
        return []


class NoModuleLevelMutableRule(Rule):
    """SC-070: No module-level mutable state."""

    @property
    def code(self) -> str:
        return "SC070"

    @property
    def description(self) -> str:
        return "No module-level mutable state"

    def check_Module(self, node: ast.Module, filepath: str) -> list[Violation]:
        violations: list[Violation] = []
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.isupper() or name.startswith("_"):
                            continue
                        if isinstance(stmt.value, (ast.List, ast.Dict, ast.Set, ast.Call)):
                            violations.append(Violation(
                                filepath, stmt.lineno, stmt.col_offset,
                                self.code,
                                f"Module-level mutable state '{name}' forbidden; use frozen dataclass or constant",
                            ))
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                name = stmt.target.id
                if name.isupper() or name.startswith("_"):
                    continue
                if stmt.value is not None and isinstance(stmt.value, (ast.List, ast.Dict, ast.Set)):
                    violations.append(Violation(
                        filepath, stmt.lineno, stmt.col_offset,
                        self.code,
                        f"Module-level mutable state '{name}' forbidden",
                    ))
        return violations
