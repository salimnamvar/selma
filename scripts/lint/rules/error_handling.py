"""SC-041, SC-042, SC-052: Error handling rules."""

from __future__ import annotations

import ast

from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.core.visitor import get_visitor


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

    def _is_last_handler(self, a_node: ast.ExceptHandler) -> Result[bool]:
        """Check whether a_node is the last handler in its enclosing try block.

        Precondition: a_node is an ExceptHandler visited by a LintVisitor
            with a non-empty parent stack.
        Postcondition: Returns Ok(True) if a_node is the final handler;
            Ok(False) otherwise.
        Side effect: None.
        Resource: Reads the visitor's parent stack via ContextVar.
        Failure: Returns Ok(False) if no visitor is available.
        """
        b_continue = True
        result: Result[bool] = Result.success(False)  # noqa: FBT003
        if b_continue:
            visitor = get_visitor()
            if visitor.is_success().value and visitor.value:
                for parent in reversed(visitor.value._parent_stack):  # noqa: SLF001
                    if isinstance(parent, ast.Try):
                        if parent.handlers and parent.handlers[-1] is a_node:
                            result = Result.success(True)  # noqa: FBT003
                        break
        return result

    def check_ExceptHandler(  # noqa: N802
        self, a_node: ast.ExceptHandler, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that except clauses catch specific exception types.

        Precondition: a_node is a valid ExceptHandler AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or Ok([]) if compliant.
        Side effect: None.
        Resource: Reads the visitor's parent stack for last-handler detection.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
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
                is_last_result = self._is_last_handler(a_node)
                is_last = (
                    is_last_result.value.value
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

    def check_ExceptHandler(  # noqa: N802
        self, a_node: ast.ExceptHandler, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that except blocks are not empty or pass-only.

        Precondition: a_node is a valid ExceptHandler AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or Ok([]) if compliant.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
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

    def check_ExceptHandler(  # noqa: N802
        self, a_node: ast.ExceptHandler, a_filepath: str
    ) -> Result[list[Violation]]:
        """Check that caught exceptions are not re-raised.

        Precondition: a_node is a valid ExceptHandler AST node in the file
            at a_filepath.
        Postcondition: Returns Ok containing violations found, or Ok([]) if compliant.
        Side effect: None.
        Resource: None.
        Failure: Never returns Failure; all errors are encoded as violations in Ok.
        """
        b_continue = True
        violations: list[Violation] = []
        if b_continue:
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
