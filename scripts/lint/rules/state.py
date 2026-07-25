"""SC-070, SC-071: State and determinism rules."""

from __future__ import annotations

import ast

from scripts.lint.config import DeterminismConfig
from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

_MUTABLE_VALUE_NODES = (ast.Dict, ast.List, ast.Set)

_CONTEXTVAR_CALL_NAMES = frozenset({"ContextVar"})


def _is_contextvar_assignment(
    a_node: ast.Assign | ast.AnnAssign,
) -> Result[bool]:
    """Check if an assignment creates a ContextVar.

    Precondition: a_node is a valid Assign or AnnAssign AST node.
    Postcondition: Returns Ok(True) if the assignment creates a
        ContextVar; Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never returns Failure.
    """
    b_continue = True
    result: Result[bool] = Result.success(a_value=False)
    if b_continue:
        value = getattr(a_node, "value", None)
        if value is not None and isinstance(value, ast.Call):
            func = value.func
            is_cv = isinstance(func, ast.Name) and func.id in _CONTEXTVAR_CALL_NAMES
            is_cv_attr = (
                isinstance(func, ast.Attribute) and func.attr in _CONTEXTVAR_CALL_NAMES
            )
            if is_cv or is_cv_attr:
                result = Result.success(a_value=True)
    return result


def _is_frozen_dataclass_instantiation(
    a_node: ast.Assign | ast.AnnAssign,
) -> Result[bool]:
    """Check if an assignment is a frozen dataclass constructor.

    Precondition: a_node is a valid Assign or AnnAssign AST node.
    Postcondition: Returns Ok(True) if the assignment calls an
        uppercase-named constructor; Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never returns Failure.
    """
    b_continue = True
    result: Result[bool] = Result.success(a_value=False)
    if b_continue:
        value = getattr(a_node, "value", None)
        if value is not None and isinstance(value, ast.Call):
            func = value.func
            name_ok = isinstance(func, ast.Name) and func.id[0:1].isupper()
            attr_ok = isinstance(func, ast.Attribute) and func.attr[0:1].isupper()
            if name_ok or attr_ok:
                result = Result.success(a_value=True)
    return result


def _is_mutable_value(
    a_node: ast.expr | None,
) -> Result[bool]:
    """Check whether an AST expression node represents a mutable value.

    Precondition: a_node is an optional AST expression node.
    Postcondition: Returns Ok(True) if the node is a mutable literal
        or constructor; Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never returns Failure.
    """
    b_continue = True
    result: Result[bool] = Result.success(a_value=False)
    if b_continue and a_node is not None:
        if isinstance(a_node, _MUTABLE_VALUE_NODES):
            result = Result.success(a_value=True)
        elif isinstance(a_node, ast.Call):
            name_match = isinstance(a_node.func, ast.Name) and a_node.func.id in (
                "dict",
                "list",
                "set",
                "defaultdict",
                "Counter",
                "OrderedDict",
            )
            attr_match = isinstance(
                a_node.func, ast.Attribute
            ) and a_node.func.attr in ("fromkeys", "copy")
            if name_match or attr_match:
                result = Result.success(a_value=True)
    return result


def _unwrap_bool(a_result: Result[bool]) -> Result[bool]:
    """Unwrap a Result[bool] to a plain bool wrapped in Result.

    Precondition: a_result is a Result[bool] value.
    Postcondition: Returns Result with the inner bool if success;
        returns Result.success(False) if failure.
    Side effect: None.
    Resource: None.
    Failure: Never returns Failure.
    """
    b_continue = True
    result: Result[bool] = Result.success(a_value=False)
    if b_continue and a_result.is_success().value:
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
            b_result = "SC071"
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
            b_result = "Deterministic execution (no datetime.now/random/etc.)"
        return b_result

    def _resolve_module(self, a_node: ast.expr) -> Result[str | None]:
        """Resolve a dotted attribute chain to its leftmost name.

        Precondition: a_node is a valid AST expression node.
        Postcondition: Returns Ok with the leftmost name string,
            or Ok(None) if unresolvable.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure.
        """
        b_continue = True
        result: Result[str | None] = Result.success(None)
        if b_continue:
            if isinstance(a_node, ast.Name):
                result = Result.success(a_node.id)
            elif isinstance(a_node, ast.Attribute):
                result = self._resolve_module(a_node.value)
        return result

    def _check_attribute_call(
        self, a_node: ast.Call, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check attribute-style calls (mod.method) for forbidden patterns.

        Precondition: a_node.func is an Attribute AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: Reads self._forbidden dictionary.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue and isinstance(a_node.func.value, ast.Name):
            mod = a_node.func.value.id
            meth = a_node.func.attr
            if mod in self._forbidden and meth in self._forbidden[mod]:
                violations = [
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        self.code,
                        f"Non-deterministic call "
                        f"'{mod}.{meth}()' forbidden; "
                        "inject time/random source",
                    )
                ]
        if b_continue and isinstance(a_node.func.value, ast.Attribute):
            outer_result = self._resolve_module(a_node.func.value.value)
            outer_mod = outer_result.value if outer_result.is_success().value else None
            if (
                outer_mod
                and outer_mod in self._forbidden
                and a_node.func.attr in self._forbidden[outer_mod]
            ):
                violations = [
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        self.code,
                        f"Non-deterministic call "
                        f"'{outer_mod}."
                        f"{a_node.func.attr}()' "
                        "forbidden; inject "
                        "time/random source",
                    )
                ]
        return Result.success(violations)

    def _check_name_call(
        self, a_node: ast.Call, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check bare-name calls for forbidden patterns.

        Precondition: a_node.func is a Name AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: Reads self._forbidden dictionary.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            for methods in self._forbidden.values():
                if a_node.func.id in methods:
                    violations = [
                        Violation(
                            a_filepath,
                            a_node.lineno,
                            a_node.col_offset,
                            self.code,
                            f"Non-deterministic call "
                            f"'{a_node.func.id}()' "
                            "forbidden; inject "
                            "time/random source",
                        )
                    ]
                    break
        return Result.success(violations)

    def check_call(self, a_node: ast.Call, a_filepath: str) -> Result[list[Violation]]:
        """Check for non-deterministic function calls.

        Precondition: a_node is a valid Call AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or
            Ok([]) if compliant.
        Side effect: None.
        Resource: Reads self._forbidden dictionary.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue and isinstance(a_node.func, ast.Attribute):
            attr_result = self._check_attribute_call(a_node, a_filepath)
            if attr_result.is_success().value:
                violations.extend(attr_result.value)
        elif b_continue and isinstance(a_node.func, ast.Name):
            name_result = self._check_name_call(a_node, a_filepath)
            if name_result.is_success().value:
                violations.extend(name_result.value)
        return Result.success(violations)


class NoModuleLevelMutableRule(Rule):
    """SC-070: No module-level variable assignments."""

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
            b_result = "SC070"
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
            b_result = "No module-level variables"
        return b_result

    @staticmethod
    def _is_exempt_target(a_name: str) -> Result[bool]:
        """Check whether a target name is exempt from the rule.

        Precondition: a_name is a string.
        Postcondition: Returns Ok(True) if name is uppercase or __all__.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result = False
        if b_continue:
            b_result = a_name.isupper() or a_name == "__all__"
        return Result.success(b_result)

    @staticmethod
    def _is_allowed_assignment(a_stmt: ast.Assign | ast.AnnAssign) -> Result[bool]:
        """Check whether an assignment is allowed (ContextVar or frozen dataclass).

        Precondition: a_stmt is an Assign or AnnAssign AST node.
        Postcondition: Returns Ok(True) if the assignment is allowed.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result = False
        if b_continue:
            ctx = _unwrap_bool(_is_contextvar_assignment(a_stmt))
            frozen = _unwrap_bool(_is_frozen_dataclass_instantiation(a_stmt))
            b_result = ctx.value or frozen.value
        return Result.success(b_result)

    def _check_assign_stmt(
        self, a_stmt: ast.Assign, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check a single Assign statement for module-level mutable variable.

        Precondition: a_stmt is an Assign AST node.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        b_allowed = False
        allowed_result = self._is_allowed_assignment(a_stmt)
        if b_continue and allowed_result.is_success().value and allowed_result.value:
            b_allowed = True
        if b_continue and not b_allowed:
            for target in a_stmt.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    exempt_result = self._is_exempt_target(name)
                    if exempt_result.is_success().value and exempt_result.value:
                        continue
                    if not _unwrap_bool(_is_mutable_value(a_stmt.value)).value:
                        continue
                    violations.append(
                        Violation(
                            a_filepath,
                            a_stmt.lineno,
                            a_stmt.col_offset,
                            self.code,
                            f"Module-level variable "
                            f"'{name}' forbidden; "
                            "move into function or class",
                        )
                    )
        return Result.success(violations)

    def _check_annassign_stmt(
        self, a_stmt: ast.AnnAssign, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check a single AnnAssign statement for module-level mutable variable.

        Precondition: a_stmt is an AnnAssign AST node with a Name target.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        b_allowed = False
        allowed_result = self._is_allowed_assignment(a_stmt)
        if b_continue and allowed_result.is_success().value and allowed_result.value:
            b_allowed = True
        if b_continue and not b_allowed:
            name = a_stmt.target.id  # type: ignore[union-attr]
            exempt_result = self._is_exempt_target(name)
            if (
                not (exempt_result.is_success().value and exempt_result.value)
                and _unwrap_bool(_is_mutable_value(a_stmt.value)).value
            ):
                violations.append(
                    Violation(
                        a_filepath,
                        a_stmt.lineno,
                        a_stmt.col_offset,
                        self.code,
                        f"Module-level variable "
                        f"'{name}' forbidden; "
                        "move into function or class",
                    )
                )
        return Result.success(violations)

    def check_module(
        self, a_node: ast.Module, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that no mutable module-level variables are defined.

        Precondition: a_node is a valid Module AST node in the
            file at a_filepath.
        Postcondition: Returns Ok containing violations found, or
            Ok([]) if compliant.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            for stmt in a_node.body:
                if isinstance(stmt, ast.Assign):
                    assign_result = self._check_assign_stmt(stmt, a_filepath)
                    if assign_result.is_success().value:
                        violations.extend(assign_result.value)
                elif isinstance(stmt, ast.AnnAssign) and isinstance(
                    stmt.target, ast.Name
                ):
                    annassign_result = self._check_annassign_stmt(stmt, a_filepath)
                    if annassign_result.is_success().value:
                        violations.extend(annassign_result.value)
        return Result.success(violations)
