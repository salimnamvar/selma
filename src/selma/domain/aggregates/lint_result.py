"""LintResult aggregate root — consistency boundary for lint findings.

Maintains invariants: no findings after completion, violation count accurate.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from selma.domain.entities.finding import Finding
from selma.domain.entities.source_file import SourceFile
from selma.domain.exceptions.domain_errors import LintResultAlreadyComplete


@dataclass
class LintResult:
    """Aggregate root for lint results.

    Maintains consistency: no findings can be added after completion.
    """

    source_file: SourceFile
    _findings: list[Finding] = field(default_factory=list)
    _is_complete: bool = False

    def add_finding(self, a_finding: Finding) -> None:
        """Add a finding. Enforces business rules.

        Preconditions:
            - Result is not yet complete.

        Postconditions:
            - Finding is added to the result.

        Side Effects: None.
        Resource: None.
        Failure: Raises LintResultAlreadyComplete if result is complete.
        """
        if self._is_complete:
            raise LintResultAlreadyComplete(
                "Cannot add finding to completed result"
            )
        self._findings.append(a_finding)

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
