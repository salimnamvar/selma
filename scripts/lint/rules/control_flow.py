"""SC-001, SC-002: Exit door rules — single exit point and zero-raise policy."""
from __future__ import annotations

import ast

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


_SC002_EXEMPT_DUNDERS = frozenset({
    "__init__", "__enter__", "__exit__", "__iter__", "__next__",
    "__getitem__", "__len__", "__bool__", "__eq__", "__lt__",
    "__str__", "__repr__", "__aenter__", "__aexit__", "__aiter__", "__anext__",
})


def _is_dunder(name: str) -> Result[bool]:
    """Check whether name is a dunder (double-underscore-wrapped) identifier.

    Precondition: name is a non-empty string.
    Postcondition: Returns Ok(True) if name starts and ends with '__', Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    return Result.success(name.startswith("__") and name.endswith("__"))


def _has_yield(node: ast.AST) -> Result[bool]:
    """Check whether a function body contains yield or yield from expressions.

    Precondition: node is a FunctionDef or AsyncFunctionDef AST node.
    Postcondition: Returns Ok(True) if the function body contains yield, Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_result: bool = False
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child is not node:
                continue
        if isinstance(child, (ast.Yield, ast.YieldFrom)):
            b_result = True
            break
    return Result.success(b_result)


def _is_sys_exit_call(node: ast.expr) -> Result[bool]:
    """Check whether a Call node is a sys.exit() or os._exit() invocation.

    Precondition: node is a valid AST expression node.
    Postcondition: Returns Ok(True) if node is sys.exit() or os._exit(), Ok(False) otherwise.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    b_result: bool = False
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name):
                if func.value.id == "sys" and func.attr == "exit":
                    b_result = True
                elif func.value.id == "os" and func.attr == "_exit":
                    b_result = True
    return Result.success(b_result)


def _collect_exits(node: ast.AST) -> Result[tuple[int, int, int]]:
    """Count return, raise, and sys.exit/os._exit statements in a function body.

    Precondition: node is a FunctionDef or AsyncFunctionDef AST node.
    Postcondition: Returns Ok with a (return_count, raise_count, sys_exit_count) tuple.
    Side effect: None.
    Resource: None.
    Failure: Never fails (pure function).
    """
    return_count = 0
    raise_count = 0
    sys_exit_count = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child is not node:
                continue
        if isinstance(child, ast.Return):
            return_count += 1
        elif isinstance(child, ast.Raise):
            raise_count += 1
        elif isinstance(child, ast.Call):
            exit_result = _is_sys_exit_call(child)
            if exit_result.is_success() and exit_result.value:
                sys_exit_count += 1
    return Result.success((return_count, raise_count, sys_exit_count))


class SingleExitRule(Rule):
    """SC-001: Every function must have exactly one exit point (return + raise + sys.exit)."""

    @property
    def code(self) -> str:
        return "SC001"

    @property
    def description(self) -> str:
        return "Single exit point per function"

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> Result[list[Violation]]:
        """Check that function has exactly one exit point.

        Precondition: a_node is a FunctionDef AST node; a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC001 violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        violations: list[Violation] = []
        b_skip = False
        dunder_result = _is_dunder(a_node.name)
        if dunder_result.is_success() and dunder_result.value:
            b_skip = True
        if not b_skip:
            yield_result = _has_yield(a_node)
            if yield_result.is_success() and yield_result.value:
                b_skip = True
        if not b_skip:
            exits_result = _collect_exits(a_node)
            if exits_result.is_success():
                return_count, raise_count, sys_exit_count = exits_result.value
                total_exits = return_count + raise_count + sys_exit_count
                if total_exits > 1:
                    violations.append(Violation(
                        a_filepath, a_node.lineno, a_node.col_offset,
                        self.code,
                        f"Function '{a_node.name}' has {total_exits} exit doors (expected 1) — use b_continue pattern",
                    ))
                elif total_exits == 1 and raise_count > 0:
                    violations.append(Violation(
                        a_filepath, a_node.lineno, a_node.col_offset,
                        f"{self.code}-raise",
                        f"Function '{a_node.name}' has 1 raise as sole exit — handle locally with Result.failure()",
                    ))
                elif total_exits == 1 and sys_exit_count > 0:
                    violations.append(Violation(
                        a_filepath, a_node.lineno, a_node.col_offset,
                        f"{self.code}-sys-exit",
                        f"Function '{a_node.name}' has sys.exit() as sole exit — use Result.failure()",
                    ))
        return Result.success(violations)

    check_AsyncFunctionDef = check_FunctionDef


class ZeroRaiseRule(Rule):
    """SC-002: No raise statements in non-dunder functions."""

    @property
    def code(self) -> str:
        return "SC002"

    @property
    def description(self) -> str:
        return "Zero raise statements in non-dunder functions"

    def _is_framework_boundary_adapter(self, a_node: ast.FunctionDef) -> Result[bool]:
        """Check whether a function is a framework boundary adapter (exception/error/http handler).

        Precondition: a_node is a FunctionDef AST node.
        Postcondition: Returns Ok(True) if function name contains an exception keyword and has raise statements.
        Side effect: None.
        Resource: None.
        Failure: Never fails (pure function).
        """
        b_result: bool = False
        name_lower = a_node.name.lower()
        has_exception_keyword = "exception" in name_lower or "error" in name_lower or "http" in name_lower
        if has_exception_keyword:
            for child in ast.walk(a_node):
                if isinstance(child, ast.Raise):
                    b_result = True
                    break
        return Result.success(b_result)

    def check_FunctionDef(self, a_node: ast.FunctionDef, a_filepath: str) -> Result[list[Violation]]:
        """Check that no raise statements exist in non-dunder functions.

        Precondition: a_node is a FunctionDef AST node; a_filepath is a valid file path.
        Postcondition: Returns Ok with list of SC002 violations found.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        violations: list[Violation] = []
        b_skip = False
        if a_node.name in _SC002_EXEMPT_DUNDERS:
            b_skip = True
        if not b_skip:
            adapter_result = self._is_framework_boundary_adapter(a_node)
            if adapter_result.is_success() and adapter_result.value:
                b_skip = True
        if not b_skip:
            for child in ast.walk(a_node):
                if isinstance(child, ast.Raise):
                    violations.append(Violation(
                        a_filepath, child.lineno, child.col_offset,
                        self.code,
                        f"Forbidden raise in function '{a_node.name}'",
                    ))
        return Result.success(violations)

    check_AsyncFunctionDef = check_FunctionDef
