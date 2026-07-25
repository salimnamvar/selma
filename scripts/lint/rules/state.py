"""SC-070, SC-071: State and determinism rules."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.config import DeterminismConfig


_MUTABLE_VALUE_NODES = (ast.Dict, ast.List, ast.Set)

_CONTEXTVAR_CALL_NAMES = frozenset({"ContextVar"})


def _is_contextvar_assignment(a_node: ast.Assign | ast.AnnAssign) -> bool:
    """Check if an assignment creates a ContextVar (language context propagation, not mutable state)."""
    value = getattr(a_node, "value", None)
    if value is None or not isinstance(value, ast.Call):
        return False
    func = value.func
    if isinstance(func, ast.Name):
        return func.id in _CONTEXTVAR_CALL_NAMES
    if isinstance(func, ast.Attribute):
        return func.attr in _CONTEXTVAR_CALL_NAMES
    return False


def _is_frozen_dataclass_instantiation(a_node: ast.Assign | ast.AnnAssign) -> bool:
    """Check if an assignment is a frozen dataclass constructor call (uppercase name = class)."""
    value = getattr(a_node, "value", None)
    if value is None or not isinstance(value, ast.Call):
        return False
    func = value.func
    if isinstance(func, ast.Name):
        return func.id[0:1].isupper()
    if isinstance(func, ast.Attribute):
        return func.attr[0:1].isupper()
    return False


def _is_mutable_value(a_node: ast.expr | None) -> bool:
    if a_node is None:
        return False
    if isinstance(a_node, _MUTABLE_VALUE_NODES):
        return True
    if isinstance(a_node, ast.Call):
        if isinstance(a_node.func, ast.Name):
            return a_node.func.id in ("dict", "list", "set", "defaultdict", "Counter", "OrderedDict")
        if isinstance(a_node.func, ast.Attribute):
            return a_node.func.attr in ("fromkeys", "copy")
    return False


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

    def _resolve_module(self, a_node: ast.expr) -> str | None:
        if isinstance(a_node, ast.Name):
            return a_node.id
        if isinstance(a_node, ast.Attribute):
            return self._resolve_module(a_node.value)
        return None

    def check_Call(self, a_node: ast.Call, a_filepath: str) -> list[Violation]:
        """Check for non-deterministic function calls."""
        violations: list[Violation] = []
        if isinstance(a_node.func, ast.Attribute):
            if isinstance(a_node.func.value, ast.Name):
                mod = a_node.func.value.id
                meth = a_node.func.attr
                if mod in self._forbidden and meth in self._forbidden[mod]:
                    violations = [Violation(
                        a_filepath, a_node.lineno, a_node.col_offset,
                        self.code,
                        f"Non-deterministic call '{mod}.{meth}()' forbidden; inject time/random source",
                    )]
            elif isinstance(a_node.func.value, ast.Attribute):
                outer_mod = self._resolve_module(a_node.func.value.value)
                if outer_mod and outer_mod in self._forbidden:
                    if a_node.func.attr in self._forbidden[outer_mod]:
                        violations = [Violation(
                            a_filepath, a_node.lineno, a_node.col_offset,
                            self.code,
                            f"Non-deterministic call '{outer_mod}.{a_node.func.attr}()' forbidden; inject time/random source",
                        )]
        elif isinstance(a_node.func, ast.Name):
            for mod, methods in self._forbidden.items():
                if a_node.func.id in methods:
                    violations = [Violation(
                        a_filepath, a_node.lineno, a_node.col_offset,
                        self.code,
                        f"Non-deterministic call '{a_node.func.id}()' forbidden; inject time/random source",
                    )]
                    break
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
                if _is_contextvar_assignment(stmt) or _is_frozen_dataclass_instantiation(stmt):
                    continue
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.isupper() or name == "__all__":
                            continue
                        if not _is_mutable_value(stmt.value):
                            continue
                        violations.append(Violation(
                            a_filepath, stmt.lineno, stmt.col_offset,
                            self.code,
                            f"Module-level variable '{name}' forbidden; move into function or class",
                        ))
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if _is_contextvar_assignment(stmt) or _is_frozen_dataclass_instantiation(stmt):
                    continue
                name = stmt.target.id
                if name.isupper() or name == "__all__":
                    continue
                if not _is_mutable_value(stmt.value):
                    continue
                violations.append(Violation(
                    a_filepath, stmt.lineno, stmt.col_offset,
                    self.code,
                    f"Module-level variable '{name}' forbidden; move into function or class",
                ))
        return violations
