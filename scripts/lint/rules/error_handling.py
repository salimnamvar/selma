"""SC-041, SC-042, SC-052: Error handling rules."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

if TYPE_CHECKING:
    from scripts.lint.core.visitor import VisitorContext


class SpecificExceptionRule(Rule):
    """SC-041: All except clauses must catch specific exception types."""

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
            b_result = "SC041"
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
            b_result = "Specific exception types in except clauses"
        return b_result

    def _is_last_handler(
        self,
        a_node: ast.ExceptHandler,
        a_context: VisitorContext,
    ) -> Result[bool]:
        """Check whether a_node is the last handler in its enclosing try block.

        Precondition: a_node is an ExceptHandler AST node; a_context provides parent stack.
        Postcondition: Returns Ok(True) if a_node is the final handler;
            Ok(False) otherwise.
        Side effect: None.
        Resource: Reads a_context.parent_stack.
        Failure: Returns Ok(False) if no context is available.
        """
        result: Result[bool] = Result.success(a_value=False)
        if a_context is not None:
            for parent in reversed(a_context.parent_stack):
                if isinstance(parent, ast.Try):
                    if parent.handlers and parent.handlers[-1] is a_node:
                        result = Result.success(a_value=True)
                    break
        return result

    def check_except_handler(
        self,
        a_node: ast.ExceptHandler,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that except clauses catch specific exception types.

        Precondition: a_node is a valid ExceptHandler AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or Ok([]) if compliant.
        Side effect: None.
        Resource: Reads the VisitorContext for last-handler detection.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        violations: list[Violation] = []
        if a_node.type is None:
            violations = [
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    self.code,
                    "Bare 'except:' forbidden; catch specific exception types",
                )
            ]
        elif isinstance(a_node.type, ast.Name) and a_node.type.id == "Exception":
            is_last_result = self._is_last_handler(a_node, a_context)
            is_last = (
                is_last_result.value
                if is_last_result.is_success().value
                else False
            )
            if not is_last:
                violations = [
                    Violation(
                        a_filepath,
                        a_node.lineno,
                        a_node.col_offset,
                        self.code,
                        "Broad 'except Exception' forbidden; catch specific types",
                    )
                ]
        return Result.success(violations)


class NoSilentFailureRule(Rule):
    """SC-042: No empty except blocks (silent failures).

    Limitation: cannot detect except blocks that don't convert to Result
    or log without full dataflow analysis. Only catches empty/pass-only
    blocks.
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
            b_result = "SC042"
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
            b_result = "No silent failures (empty except blocks)"
        return b_result

    def check_except_handler(
        self,
        a_node: ast.ExceptHandler,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that except blocks are not empty or pass-only.

        Precondition: a_node is a valid ExceptHandler AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or Ok([]) if compliant.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        violations: list[Violation] = []
        if not a_node.body:
            violations = [
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    self.code,
                    "Empty except block: silent failure forbidden",
                )
            ]
        elif len(a_node.body) == 1 and isinstance(a_node.body[0], ast.Pass):
            violations = [
                Violation(
                    a_filepath,
                    a_node.lineno,
                    a_node.col_offset,
                    self.code,
                    "Except block contains only 'pass': silent failure forbidden",
                )
            ]
        return Result.success(violations)


class NoReraiseRule(Rule):
    """SC-052: Caught exceptions must not be re-raised."""

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
            b_result = "SC052"
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
            b_result = "No exception re-raising"
        return b_result

    def check_except_handler(
        self,
        a_node: ast.ExceptHandler,
        a_filepath: str,
        a_context: VisitorContext | None = None,
    ) -> Result[list[Violation]]:
        """Check that caught exceptions are not re-raised.

        Precondition: a_node is a valid ExceptHandler AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or Ok([]) if compliant.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        violations: list[Violation] = []
        for child in ast.walk(a_node):
            if isinstance(child, ast.Raise) and child.exc is None:
                violations = [
                    Violation(
                        a_filepath,
                        child.lineno,
                        child.col_offset,
                        self.code,
                        "Re-raise forbidden; convert exception to Result return",
                    )
                ]
                break
        return Result.success(violations)
