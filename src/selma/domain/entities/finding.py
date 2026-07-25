"""Finding entity — a lint violation found during analysis.

Has identity (file + line + code), carries behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.guidance import RuleGuidance
from selma.domain.value_objects.severity import Severity


@dataclass(frozen=True)
class Finding:
    """A lint finding produced by rule evaluation.

    Immutable. Has identity defined by (file, line, code).
    """

    rule_id: str
    file: str
    line: int
    col: int = 0
    message: str = ""
    severity: Severity = Severity.MEDIUM
    guidance: RuleGuidance | None = None
    filepath: str = ""

    @property
    def is_violation(self) -> bool:
        """Check if this finding represents a violation (error/critical)."""
        return self.severity in (Severity.CRITICAL, Severity.HIGH)

    def __str__(self) -> str:
        return (
            f"{self.filepath or self.file}:{self.line}:{self.col}: "
            f"{self.severity}: {self.message} ({self.rule_id})"
        )
