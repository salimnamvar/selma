"""Violation entity — a single lint violation found during analysis.

Distinct from Finding: Violation is the output format, Finding is the domain object.
"""

from __future__ import annotations

from dataclasses import dataclass

from selma.domain.value_objects.guidance import RuleGuidance


@dataclass(frozen=True)
class Violation:
    """A single lint violation found during analysis."""

    filepath: str
    line: int
    col: int
    code: str
    message: str
    severity: str = "error"
    guidance: RuleGuidance | None = None

    def __str__(self) -> str:
        return (
            f"{self.filepath}:{self.line}:{self.col}: "
            f"{self.severity}: {self.message} ({self.code})"
        )

    def to_dict(self, a_include_guidance: bool = False) -> dict:
        """Convert to dictionary for JSON output."""
        d: dict[str, object] = {
            "file": self.filepath,
            "line": self.line,
            "col": self.col,
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if a_include_guidance and self.guidance:
            d["guidance"] = {
                "title": self.guidance.title,
                "description": self.guidance.description,
                "rationale": self.guidance.rationale,
                "severity": self.guidance.severity,
                "fix_instructions": self.guidance.fix_instructions,
                "correct_example": self.guidance.correct_example,
                "anti_pattern": self.guidance.anti_pattern,
                "related_rules": self.guidance.related_rules,
                "doctrine_section": self.guidance.doctrine_section,
                "hints": self.guidance.hints,
            }
        return d
