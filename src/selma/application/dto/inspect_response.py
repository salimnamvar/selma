"""Inspect response DTO — output from source inspection."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict

from selma.domain.entities.finding import Finding


class InspectResponse(BaseModel):
    """Result of inspecting source paths."""

    model_config = ConfigDict(frozen=True)

    findings: tuple[Finding, ...] = ()
    summary: str = ""
    has_errors: bool = False
    report_text: str = ""

    @property
    def finding_count(self) -> int:
        """Number of findings."""
        return len(self.findings)
