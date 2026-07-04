"""Violation and AssessmentResult entities."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Violation:
    """A single lint violation found during validation.

    Attributes:
        rule_id (str): Identifier of the violated rule.
        severity (str): Violation severity level.
        message (str): Human-readable violation description.
        file (str): Source file where violation was found.
        line (int): Line number of the violation.
        context (str): Surrounding context text.
        reasoning (str): Explanation of why this is a violation.
        fix (str): Fix instruction.
    """

    rule_id: str = field(metadata={"description": "Identifier of the violated rule"})
    severity: str = field(metadata={"description": "Violation severity level"})
    message: str = field(metadata={"description": "Human-readable violation description"})
    file: str = field(metadata={"description": "Source file where violation was found"})
    line: int = field(default=0, metadata={"description": "Line number of the violation"})
    context: str = field(default="", metadata={"description": "Surrounding context text"})
    reasoning: str = field(
        default="",
        metadata={"description": "Explanation of why this is a violation"},
    )
    fix: str = field(default="", metadata={"description": "Fix instruction"})


@dataclass
class AssessmentResult:
    """Result of a project-level principle assessment.

    Attributes:
        id (str): Assessment identifier.
        name (str): Human-readable assessment name.
        status (str): Assessment status (OK or VIOLATED).
        detail (str): Detail message.
        reasoning (str): Explanation of the assessment.
    """

    id: str = field(metadata={"description": "Assessment identifier"})
    name: str = field(metadata={"description": "Human-readable assessment name"})
    status: str = field(metadata={"description": "Assessment status"})
    detail: str = field(default="", metadata={"description": "Detail message"})
    reasoning: str = field(default="", metadata={"description": "Explanation of the assessment"})
