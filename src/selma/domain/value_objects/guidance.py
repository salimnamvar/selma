"""RuleGuidance value object — structured guidance for fixing violations.

Carries everything an agent needs to understand and fix a lint violation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleGuidance:
    """Structured guidance for fixing a lint rule violation.

    Carried by each rule definition. When a violation is found,
    the guidance is attached for the agent to consume.
    """

    rule_code: str
    title: str
    description: str
    rationale: str
    severity: str
    fix_instructions: str
    correct_example: str
    anti_pattern: str
    related_rules: tuple[str, ...]
    doctrine_section: str
    hints: tuple[str, ...] = ()
