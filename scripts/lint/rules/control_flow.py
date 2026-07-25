"""SC-001, SC-002: Exit door rules — single exit point and zero-raise policy."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

if TYPE_CHECKING:
    from scripts.lint.core.visitor import VisitorContext

_SC002_EXEMPT_DUNDERS = frozenset(
    {
        "__init__",
        "__enter__",
        "__exit__",
        "__iter__",
        "__next__",
        "__getitem__",
        "__len__",
        "__bool__",
        "__eq__",
        "__lt__",
        "__str__",
        "__repr__",
        "__aenter__",
        "__aexit__",
        "__aiter__",
        "__anext__",
    }
)


def _is_dunder(name: str) -> Result[bool]:
    """Check whether name is a dunder identifier.

    Precondition: name is a non-empty string.
    Postcondition: Returns Result.success(True) if name starts and
        ends with '__', Result.success(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    b_result: bool = False
    if b_continue:
        b_result = name.startswith("__") and name.endswith("__")
    return Result.success(b_result)


def _has_yield(node: ast.AST) -> Result[bool]:
    """Check whether a function body contains yield expressions.

    Precondition: node is a FunctionDef or AsyncFunctionDef AST node.
    Postcondition: Returns Result.success(True) if the function body
        contains yield, Result.success(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    b_result: bool = False
    if b_continue:
        for child in ast.walk(node):
            if (
                isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
                and child is not node
            ):
                continue
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                b_result = True
                break
    return Result.success(b_result)


def _is_exit_call(node: ast.expr) -> Result[bool]:
    """Check whether a Call node is sys.exit() or os._exit().

    Precondition: node is a valid AST expression node.
    Postcondition: Returns Result.success(True) if node is sys.exit()
        or os._exit(), Result.success(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    b_result: bool = False
    if b_continue and isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            is_sys = func.value.id == "sys" and func.attr == "exit"
            is_os = func.value.id == "os" and func.attr == "_exit"
            if is_sys or is_os:
                b_result = True
    return Result.success(b_result)


def _get_raise_exception_name(
    node: ast.Raise,
) -> Result[str | None]:
    """Extract the exception class name from a raise statement.

    Precondition: node is an ast.Raise AST node.
    Postcondition: Returns Result.success with the exception name
        string, or Result.success(None) for bare raise.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    name: str | None = None
    if b_continue and node.exc is not None:
        if isinstance(node.exc, ast.Call):
            if isinstance(node.exc.func, ast.Name):
                name = node.exc.func.id
            elif isinstance(node.exc.func, ast.Attribute):
                name = node.exc.func.attr
        elif isinstance(node.exc, ast.Name):
            name = node.exc.id
    return Result.success(name)


def _classify_call_exit(node: ast.Call) -> Result[tuple[bool, bool]]:
    """Classify whether a call node is a sys.exit() or os._exit().

    Precondition: node is a Call AST node.
    Postcondition: Returns Ok with (is_sys_exit, is_os_exit).
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    is_sys = False
    is_os = False
    if (
        b_continue
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
    ):
        is_sys = node.func.value.id == "sys" and node.func.attr == "exit"
        is_os = node.func.value.id == "os" and node.func.attr == "_exit"
    return Result.success((is_sys, is_os))


def _get_exit_increments(
    child: ast.AST,
) -> Result[tuple[int, int, int, int, str | None]]:
    """Classify a single AST child as an exit mechanism.

    Precondition: child is an AST node from ast.walk().
    Postcondition: Returns Ok with (return_inc, raise_inc, sys_inc,
        os_inc, raise_name_or_none).
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    ret = (0, 0, 0, 0, None)
    if b_continue and isinstance(child, ast.Return):
        ret = (1, 0, 0, 0, None)
    if b_continue and isinstance(child, ast.Raise):
        name_result = _get_raise_exception_name(child)
        name = (
            name_result.value
            if name_result.is_success().value and name_result.value
            else None
        )
        ret = (0, 1, 0, 0, name)
    if b_continue and isinstance(child, ast.Call):
        class_result = _classify_call_exit(child)
        if class_result.is_success().value:
            is_sys, is_os = class_result.value
            if is_sys:
                ret = (0, 0, 1, 0, None)
            elif is_os:
                ret = (0, 0, 0, 1, None)
    return Result.success(ret)


def _classify_child_exit(
    child: ast.AST,
    parent: ast.AST,
) -> Result[tuple[int, int, int, int, str | None]]:
    """Classify a child node as an exit, skipping nested functions.

    Precondition: child and parent are AST nodes.
    Postcondition: Returns Ok with exit increments for this child.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    ret = (0, 0, 0, 0, None)
    if b_continue:
        child_result = _is_child_function(child, parent)
        b_is_child = child_result.is_success().value and child_result.value
        if not b_is_child:
            incr_result = _get_exit_increments(child)
            if incr_result.is_success().value:
                ret = incr_result.value
    return Result.success(ret)


def _is_child_function(node: ast.AST, parent: ast.AST) -> Result[bool]:
    """Check whether node is a nested function different from parent.

    Precondition: node and parent are AST nodes.
    Postcondition: Returns Ok(True) if node is a nested function
        def not equal to parent.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    b_result = False
    if b_continue:
        b_result = (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node is not parent
        )
    return Result.success(b_result)


def _collect_exits(
    node: ast.AST,
) -> Result[tuple[int, int, int, int, list[str]]]:
    """Count all exit mechanisms in a function body.

    Precondition: node is a FunctionDef or AsyncFunctionDef AST node.
    Postcondition: Returns Result.success with (return_count,
        raise_count, sys_exit_count, os_exit_count,
        raise_exception_names).
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_continue = True
    return_count = 0
    raise_count = 0
    sys_exit_count = 0
    os_exit_count = 0
    raise_names: list[str] = []
    if b_continue:
        for child in ast.walk(node):
            cr = _classify_child_exit(child, node)
            if cr.is_success().value:
                ri, rai, si, oi, rn = cr.value
                return_count += ri
                raise_count += rai
                sys_exit_count += si
                os_exit_count += oi
                if rn is not None:
                    raise_names.append(rn)
    return Result.success(
        (
            return_count,
            raise_count,
            sys_exit_count,
            os_exit_count,
            raise_names,
        )
    )


class SingleExitRule(Rule):
    """SC-001: Every function must have exactly one exit door.

    Exit doors are: return, raise, sys.exit(), os._exit().
    Generators (yield) are exempt. Dunder methods are exempt.
    """

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
            b_result = "SC001"
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
            b_result = "Single exit door per function"
        return b_result

    @staticmethod
    def _build_exit_breakdown(
        a_return_count: int,
        a_raise_count: int,
        a_sys_exit_count: int,
        a_os_exit_count: int,
    ) -> Result[str]:
        """Build a human-readable breakdown string for exit counts.

        Precondition: counts are non-negative integers.
        Postcondition: Returns Ok with a formatted breakdown string.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        parts: list[str] = []
        if b_continue:
            if a_return_count:
                parts.append(f"{a_return_count} return")
            if a_raise_count:
                parts.append(f"{a_raise_count} raise")
            if a_sys_exit_count:
                parts.append(f"{a_sys_exit_count} sys.exit()")
            if a_os_exit_count:
                parts.append(f"{a_os_exit_count} os._exit()")
        return Result.success(" + ".join(parts))

    def _check_multi_exit(
        self,
        a_total: int,
        a_breakdown: str,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Return violation for multiple exit doors.

        Precondition: a_total > 1.
        Postcondition: Returns Ok with list containing one violation.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            violations.append(
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    self.code,
                    f"Function '{a_node.name}' has "
                    f"{a_total} exit doors "
                    f"({a_breakdown}) — use b_continue "
                    "pattern",
                )
            )
        return Result.success(violations)

    def _check_single_raise_exit(
        self,
        a_raise_names: list[str],
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Return violation for single raise as sole exit.

        Precondition: raise is the only exit mechanism.
        Postcondition: Returns Ok with list containing one violation.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            exc_name = a_raise_names[0] if a_raise_names else "unknown"
            violations.append(
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    f"{self.code}-raise",
                    f"Function '{a_node.name}' has raise "
                    f"{exc_name} as sole exit — handle "
                    "locally with Result.failure()",
                )
            )
        return Result.success(violations)

    def _check_single_sys_exit(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Return violation for sys.exit() as sole exit.

        Precondition: sys.exit() is the only exit mechanism.
        Postcondition: Returns Ok with list containing one violation.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            violations.append(
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    f"{self.code}-sys-exit",
                    f"Function '{a_node.name}' has "
                    "sys.exit() as sole exit — use "
                    "Result.failure()",
                )
            )
        return Result.success(violations)

    def _check_single_os_exit(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Return violation for os._exit() as sole exit.

        Precondition: os._exit() is the only exit mechanism.
        Postcondition: Returns Ok with list containing one violation.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            violations.append(
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    f"{self.code}-os-exit",
                    f"Function '{a_node.name}' has "
                    "os._exit() as sole exit — use "
                    "Result.failure()",
                )
            )
        return Result.success(violations)

    def _check_single_exit(
        self,
        a_raise_count: int,
        a_sys_exit_count: int,
        a_os_exit_count: int,
        a_raise_names: list[str],
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Dispatch single-exit violation checks.

        Precondition: exactly one exit mechanism present.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            if a_raise_count > 0:
                raise_result = self._check_single_raise_exit(
                    a_raise_names, a_node, a_filepath
                )
                if raise_result.is_success().value:
                    violations.extend(raise_result.value)
            elif a_sys_exit_count > 0:
                sys_result = self._check_single_sys_exit(a_node, a_filepath)
                if sys_result.is_success().value:
                    violations.extend(sys_result.value)
            elif a_os_exit_count > 0:
                os_result = self._check_single_os_exit(a_node, a_filepath)
                if os_result.is_success().value:
                    violations.extend(os_result.value)
        return Result.success(violations)

    def _check_exit_violations(
        self,
        a_return_count: int,
        a_raise_count: int,
        a_sys_exit_count: int,
        a_os_exit_count: int,
        a_raise_names: list[str],
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Dispatch exit-count checks to specific handlers.

        Precondition: exit counts are non-negative.
        Postcondition: Returns Ok with list of violations found.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
            total = a_return_count + a_raise_count + a_sys_exit_count + a_os_exit_count
            if total > 1:
                breakdown_result = self._build_exit_breakdown(
                    a_return_count,
                    a_raise_count,
                    a_sys_exit_count,
                    a_os_exit_count,
                )
                if breakdown_result.is_success().value:
                    multi_result = self._check_multi_exit(
                        total,
                        breakdown_result.value,
                        a_node,
                        a_filepath,
                    )
                    if multi_result.is_success().value:
                        violations.extend(multi_result.value)
            elif total == 1:
                single_result = self._check_single_exit(
                    a_raise_count,
                    a_sys_exit_count,
                    a_os_exit_count,
                    a_raise_names,
                    a_node,
                    a_filepath,
                )
                if single_result.is_success().value:
                    violations.extend(single_result.value)
        return Result.success(violations)

    def _check_exits(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check that function has exactly one exit door.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Result.success with list of SC001
            violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        b_skip = False
        if b_continue:
            dunder_result = _is_dunder(a_node.name)
            if dunder_result.is_success().value and dunder_result.value:
                b_skip = True
        if b_continue and not b_skip:
            yield_result = _has_yield(a_node)
            if yield_result.is_success().value and yield_result.value:
                b_skip = True
        if b_continue and not b_skip:
            exits_result = _collect_exits(a_node)
            if exits_result.is_success().value:
                (
                    return_count,
                    raise_count,
                    sys_exit_count,
                    os_exit_count,
                    raise_names,
                ) = exits_result.value
                violations_result = self._check_exit_violations(
                    return_count,
                    raise_count,
                    sys_exit_count,
                    os_exit_count,
                    raise_names,
                    a_node,
                    a_filepath,
                )
                if violations_result.is_success().value:
                    violations.extend(violations_result.value)
        return Result.success(violations)

    def check_function_def(
        self,
        a_node: ast.FunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that function has exactly one exit door.

        Precondition: a_node is a FunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Result.success with list of SC001
            violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        return self._check_exits(a_node, a_filepath)

    def check_async_function_def(
        self,
        a_node: ast.AsyncFunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that async function has exactly one exit door.

        Precondition: a_node is an AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Result.success with list of SC001
            violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        return self._check_exits(a_node, a_filepath)


class ZeroRaiseRule(Rule):
    """SC-002: No raise statements in non-dunder functions."""

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
            b_result = "SC002"
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
            b_result = "Zero raise statements in non-dunder functions"
        return b_result

    def _is_framework_boundary_adapter(self, a_node: ast.FunctionDef) -> Result[bool]:
        """Check whether a function is a framework boundary adapter.

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Result.success(True) if function name
            contains an exception keyword and has raise statements.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_continue = True
        b_result: bool = False
        if b_continue:
            name_lower = a_node.name.lower()
            has_exception_keyword = (
                "exception" in name_lower
                or "error" in name_lower
                or "http" in name_lower
            )
            if has_exception_keyword:
                for child in ast.walk(a_node):
                    if isinstance(child, ast.Raise):
                        b_result = True
                        break
        return Result.success(b_result)

    def _check_raise(
        self,
        a_node: ast.FunctionDef | ast.AsyncFunctionDef,
        a_filepath: str,
    ) -> Result[list[Violation]]:
        """Check that no raise statements exist in non-dunder functions.

        Precondition: a_node is a FunctionDef or AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Result.success with list of SC002
            violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        b_skip = False
        if b_continue and a_node.name in _SC002_EXEMPT_DUNDERS:
            b_skip = True
        if b_continue and not b_skip and isinstance(a_node, ast.FunctionDef):
            adapter_result = self._is_framework_boundary_adapter(a_node)
            if adapter_result.is_success().value and adapter_result.value:
                b_skip = True
        if b_continue and not b_skip:
            violations.extend(
                Violation(
                    a_filepath,
                    child.lineno,
                    child.col_offset,
                    self.code,
                    f"Forbidden raise in function '{a_node.name}'",
                )
                for child in ast.walk(a_node)
                if isinstance(child, ast.Raise)
            )
        return Result.success(violations)

    def check_function_def(
        self,
        a_node: ast.FunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that no raise statements exist in non-dunder functions.

        Precondition: a_node is a FunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Result.success with list of SC002
            violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        return self._check_raise(a_node, a_filepath)

    def check_async_function_def(
        self,
        a_node: ast.AsyncFunctionDef,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check no raise statements in non-dunder async functions.

        Precondition: a_node is an AsyncFunctionDef AST node;
            a_filepath is a valid file path.
        Postcondition: Returns Result.success with list of SC002
            violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as
            violations in Ok.
        """
        return self._check_raise(a_node, a_filepath)
