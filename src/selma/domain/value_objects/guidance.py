"""RuleGuidance value object — structured guidance for fixing violations.

Carries everything an agent needs to understand and fix a lint violation.
Uses Pydantic v2 BaseModel with frozen config.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict


class RuleGuidance(BaseModel):
    """Structured guidance for fixing a lint rule violation.

    Carried by each rule definition. When a violation is found,
    the guidance is attached for the agent to consume.
    """

    model_config = ConfigDict(frozen=True)

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
