"""SC-070, SC-071: State and determinism rules."""
from __future__ import annotations

import ast

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.config import DeterminismConfig


_MUTABLE_VALUE_NODES = (ast.Dict, ast.List, ast.Set)

_CONTEXTVAR_CALL_NAMES = frozenset({"ContextVar"})


def _is_contextvar_assignment(a_node: ast.Assign | ast.AnnAssign) -> Result[bool]:
    """Check if an assignment creates a ContextVar (language context propagation, not mutable state).

    Precondition: a_node is a valid Assign or AnnAssign AST node.
    Postcondition: Returns Ok(True) if the assignment creates a ContextVar; Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never returns Failure.
    """
    result: Result[bool] = Result.success(False)
    value = getattr(a_node, "value", None)
    if value is not None and isinstance(value, ast.Call):
        func = value.func
        if isinstance(func, ast.Name) and func.id in _CONTEXTVAR_CALL_NAMES:
            result = Result.success(True)
        elif isinstance(func, ast.Attribute) and func.attr in _CONTEXTVAR_CALL_NAMES:
            result = Result.success(True)
    return result


def _is_frozen_dataclass_instantiation(a_node: ast.Assign | ast.AnnAssign) -> Result[bool]:
    """Check if an assignment is a frozen dataclass constructor call (uppercase name = class).

    Precondition: a_node is a valid Assign or AnnAssign AST node.
    Postcondition: Returns Ok(True) if the assignment calls an uppercase-named constructor; Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never returns Failure.
    """
    result: Result[bool] = Result.success(False)
    value = getattr(a_node, "value", None)
    if value is not None and isinstance(value, ast.Call):
        func = value.func
        if isinstance(func, ast.Name) and func.id[0:1].isupper():
            result = Result.success(True)
        elif isinstance(func, ast.Attribute) and func.attr[0:1].isupper():
            result = Result.success(True)
    return result


def _is_mutable_value(a_node: ast.expr | None) -> Result[bool]:
    """Check whether an AST expression node represents a mutable value.

    Precondition: a_node is an optional AST expression node.
    Postcondition: Returns Ok(True) if the node is a mutable literal or constructor; Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never returns Failure.
    """
    result: Result[bool] = Result.success(False)
    if a_node is not None:
        if isinstance(a_node, _MUTABLE_VALUE_NODES):
            result = Result.success(True)
        elif isinstance(a_node, ast.Call):
            if isinstance(a_node.func, ast.Name) and a_node.func.id in ("dict", "list", "set", "defaultdict", "Counter", "OrderedDict"):
                result = Result.success(True)
            elif isinstance(a_node.func, ast.Attribute) and a_node.func.attr in ("fromkeys", "copy"):
                result = Result.success(True)
    return result


def _unwrap_bool(a_result: Result[bool]) -> Result[bool]:
    """Unwrap a Result[bool] to a plain bool wrapped in Result.

    Precondition: a_result is a Result[bool] value.
    Postcondition: Returns Result with the inner bool if success; returns Result.success(False) if failure.
    Side effect: None.
    Resource: None.
    Failure: Never returns Failure.
    """
    result: Result[bool] = Result.success(False)
    if a_result.is_success():
        result = Result.success(a_result.value)
    return result


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

    def _resolve_module(self, a_node: ast.expr) -> Result[str | None]:
        """Resolve a dotted attribute chain to its leftmost module name.

        Precondition: a_node is a valid AST expression node (Name or Attribute).
        Postcondition: Returns Ok with the leftmost name string, or Ok(None) if unresolvable.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure.
        """
        result: Result[str | None] = Result.success(None)
        if isinstance(a_node, ast.Name):
            result = Result.success(a_node.id)
        elif isinstance(a_node, ast.Attribute):
            result = self._resolve_module(a_node.value)
        return result

    def check_Call(self, a_node: ast.Call, a_filepath: str) -> Result[list[Violation]]:
        """Check for non-deterministic function calls.

        Precondition: a_node is a valid Call AST node in the file at a_filepath.
        Postcondition: Returns Ok containing violations found, or Ok([]) if compliant.
        Side effect: None.
        Resource: Reads self._forbidden dictionary.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
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
                outer_result = self._resolve_module(a_node.func.value.value)
                outer_mod = outer_result.value if outer_result.is_success() else None
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
        return Result.success(violations)


class NoModuleLevelMutableRule(Rule):
    """SC-070: No module-level variable assignments."""

    @property
    def code(self) -> str:
        return "SC070"

    @property
    def description(self) -> str:
        return "No module-level variables"

    def check_Module(self, a_node: ast.Module, a_filepath: str) -> Result[list[Violation]]:
        """Check that no mutable module-level variables are defined.

        Precondition: a_node is a valid Module AST node in the file at a_filepath.
        Postcondition: Returns Ok containing violations found, or Ok([]) if compliant.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        violations: list[Violation] = []
        for stmt in a_node.body:
            if isinstance(stmt, ast.Assign):
                if _unwrap_bool(_is_contextvar_assignment(stmt)).value or _unwrap_bool(_is_frozen_dataclass_instantiation(stmt)).value:
                    continue
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.isupper() or name == "__all__":
                            continue
                        if not _unwrap_bool(_is_mutable_value(stmt.value)).value:
                            continue
                        violations.append(Violation(
                            a_filepath, stmt.lineno, stmt.col_offset,
                            self.code,
                            f"Module-level variable '{name}' forbidden; move into function or class",
                        ))
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if _unwrap_bool(_is_contextvar_assignment(stmt)).value or _unwrap_bool(_is_frozen_dataclass_instantiation(stmt)).value:
                    continue
                name = stmt.target.id
                if name.isupper() or name == "__all__":
                    continue
                if not _unwrap_bool(_is_mutable_value(stmt.value)).value:
                    continue
                violations.append(Violation(
                    a_filepath, stmt.lineno, stmt.col_offset,
                    self.code,
                    f"Module-level variable '{name}' forbidden; move into function or class",
                ))
        return Result.success(violations)
