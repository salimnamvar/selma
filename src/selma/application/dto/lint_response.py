"""LintResponse DTO — output from the lint use case.

Uses Pydantic v2 BaseModel with frozen config.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict

from selma.domain.entities.finding import Finding


class LintResponse(BaseModel):
    """Output DTO for lint use case."""

    model_config = ConfigDict(frozen=True)

    findings: tuple[Finding, ...]
    summary: str = ""
    has_errors: bool = False

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def violation_count(self) -> int:
        return sum(1 for f in self.findings if f.is_violation)
