"""SC-001, SC-002: Exit door rules — single exit point and zero-raise policy."""

from __future__ import annotations

import ast

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

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
            if (
                isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
                and child is not node
            ):
                continue
            if isinstance(child, ast.Return):
                return_count += 1
            elif isinstance(child, ast.Raise):
                raise_count += 1
                name_result = _get_raise_exception_name(child)
                if name_result.is_success().value and name_result.value:
                    raise_names.append(name_result.value)
            elif (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and isinstance(child.func.value, ast.Name)
            ):
                is_sys = child.func.value.id == "sys" and child.func.attr == "exit"
                is_os = child.func.value.id == "os" and child.func.attr == "_exit"
                if is_sys:
                    sys_exit_count += 1
                elif is_os:
                    os_exit_count += 1
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
                total_exits = (
                    return_count + raise_count + sys_exit_count + os_exit_count
                )
                if total_exits > 1:
                    parts: list[str] = []
                    if return_count:
                        parts.append(f"{return_count} return")
                    if raise_count:
                        parts.append(f"{raise_count} raise")
                    if sys_exit_count:
                        parts.append(f"{sys_exit_count} sys.exit()")
                    if os_exit_count:
                        parts.append(f"{os_exit_count} os._exit()")
                    breakdown = " + ".join(parts)
                    violations.append(
                        Violation(
                            a_filepath,
                            a_node.lineno,
                            a_node.col_offset,
                            self.code,
                            f"Function '{a_node.name}' has "
                            f"{total_exits} exit doors "
                            f"({breakdown}) — use b_continue "
                            "pattern",
                        )
                    )
                elif total_exits == 1 and raise_count > 0:
                    exc_name = raise_names[0] if raise_names else "unknown"
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
                elif total_exits == 1 and sys_exit_count > 0:
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
                elif total_exits == 1 and os_exit_count > 0:
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

    def check_FunctionDef(
        self, a_node: ast.FunctionDef, a_filepath: str
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
        b_continue = True
        if b_continue:
            return self._check_exits(a_node, a_filepath)
        return Result.success([])

    def check_AsyncFunctionDef(
        self, a_node: ast.AsyncFunctionDef, a_filepath: str
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
        b_continue = True
        if b_continue:
            return self._check_exits(a_node, a_filepath)
        return Result.success([])


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

    def check_FunctionDef(
        self, a_node: ast.FunctionDef, a_filepath: str
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
        b_continue = True
        if b_continue:
            return self._check_raise(a_node, a_filepath)
        return Result.success([])

    def check_AsyncFunctionDef(
        self, a_node: ast.AsyncFunctionDef, a_filepath: str
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
        b_continue = True
        if b_continue:
            return self._check_raise(a_node, a_filepath)
        return Result.success([])
