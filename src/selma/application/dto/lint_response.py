"""LintResponse DTO — output from the lint use case."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from selma.domain.entities.finding import Finding


@dataclass(frozen=True)
class LintResponse:
    """Output DTO for lint use case."""

    findings: tuple[Finding, ...]
    summary: str = ""
    has_errors: bool = False

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def violation_count(self) -> int:
        return sum(1 for f in self.findings if f.is_violation)
