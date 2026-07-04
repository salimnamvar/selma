"""Violation and AssessmentResult entities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Violation:
    """A single lint violation found during validation."""

    rule_id: str
    severity: str
    message: str
    file: str
    line: int = 0
    context: str = ""
    reasoning: str = ""
    fix: str = ""


@dataclass
class AssessmentResult:
    """Result of a project-level principle assessment."""

    id: str
    name: str
    status: str  # "OK" or "VIOLATED"
    detail: str = ""
    reasoning: str = ""
