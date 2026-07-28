"""InspectionResult aggregate root — consistency boundary for findings.

Maintains invariants: no findings after completion, violation count accurate.
Uses Pydantic v2 BaseModel (mutable for aggregate state management).
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import PrivateAttr

from selma.domain.entities.finding import Finding
from selma.domain.entities.source_file import SourceFile
from selma.domain.value_objects.result import Result


class LintResult(BaseModel):
    """Aggregate root for inspection findings.

    Maintains consistency: no findings can be added after completion.
    Mutable — aggregate state changes via methods.
    """

    source_file: SourceFile
    _findings: list[Finding] = PrivateAttr()
    _is_complete: bool = PrivateAttr(default=False)

    def model_post_init(self, __context: object) -> None:
        """Initialize private attributes after model creation."""
        if not hasattr(self, "_findings"):
            self._findings = []
        if not hasattr(self, "_is_complete"):
            self._is_complete = False

    def add_finding(self, a_finding: Finding) -> Result[None]:
        """Add a finding. Enforces business rules without raise (SC-002).

        Preconditions:
            - Result is not yet complete.
        Postconditions:
            - Finding is added, or Failure if complete.
        Side Effects: None.
        Resource: None.
        Failure: Returns Failure if result is complete.
        """
        b_continue = True
        result: Result[None] = Result.failure("unreachable")
        if b_continue and self._is_complete:
            b_continue = False
            result = Result.failure("Cannot add finding to completed result")
        if b_continue:
            # Immutable rebuild avoids in-place mutation methods (SC-092).
            self._findings = [*self._findings, a_finding]
            result = Result.success(None)
        return result

    def complete(self) -> None:
        """Mark result as complete. No more findings allowed."""
        self._is_complete = True

    @property
    def findings(self) -> tuple[Finding, ...]:
        return tuple(self._findings)

    @property
    def has_violations(self) -> bool:
        return any(f.is_violation for f in self._findings)

    @property
    def violation_count(self) -> int:
        return sum(1 for f in self._findings if f.is_violation)

    @property
    def finding_count(self) -> int:
        return len(self._findings)
