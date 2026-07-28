"""Directive aggregate — rule (executable) + policy (reasoning).

The unit of governance content in Selma. Catalog holds all directives.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from selma.domain.entities.policy import DirectivePolicy
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.guidance import RuleGuidance


class Directive(BaseModel):
    """One governance directive: executable rule plus optional policy.

    Machine ID / lineage_id is the aggregate identity.
    Inspection uses ``rule`` only; agents query ``policy`` for reasoning.
    """

    model_config = ConfigDict(frozen=True)

    rule: Rule
    policy: DirectivePolicy | None = None

    @property
    def lineage_id(self) -> str:
        """Immutable Machine ID / lineage root."""
        return self.rule.lineage_id

    @property
    def execution_id(self) -> str:
        """Active execution identity."""
        return self.rule.id

    @property
    def title(self) -> str:
        """Human title from policy when present, else rule message."""
        b_continue = True
        result = self.rule.message
        if b_continue and self.policy is not None:
            specs = self.policy.directives.specific_directives
            if specs and specs[0].title:
                b_continue = False
                result = specs[0].title
            if b_continue and self.policy.preamble.purpose:
                result = self.policy.preamble.purpose
        return result

    def is_active(self) -> bool:
        """Whether the executable rule is active for inspection."""
        return self.rule.is_active()

    def has_policy(self) -> bool:
        """Whether a reasoning policy document is attached."""
        return self.policy is not None

    def reasoning_guidance(self) -> RuleGuidance | None:
        """Project policy into agent-facing RuleGuidance.

        Never used as evaluator input — reasoning and remediation only.
        """
        b_continue = True
        result: RuleGuidance | None = None
        if b_continue and self.policy is None:
            b_continue = False
        if b_continue and self.policy is not None:
            guide = self.policy.guidance
            title = self.lineage_id
            specs = self.policy.directives.specific_directives
            if specs:
                title = specs[0].title or specs[0].machine_id or self.lineage_id
            fix_instructions = ""
            if self.policy.sanctions.rows:
                fix_instructions = self.policy.sanctions.rows[0].remediation_path
            if not fix_instructions:
                fix_instructions = guide.explanation or self.rule.message
            related = tuple(guide.related_machine_ids)
            doctrine_section = self.policy.references.anchor_ref
            result = RuleGuidance(
                rule_code=self.lineage_id,
                title=title,
                description=guide.explanation or self.rule.message,
                rationale=guide.reasoning or self.rule.rationale,
                severity=self.rule.weight.value,
                fix_instructions=fix_instructions or self.rule.remediation,
                correct_example=guide.correct_example,
                anti_pattern=guide.incorrect_example,
                related_rules=related,
                doctrine_section=doctrine_section,
                hints=(),
            )
        return result


class DirectiveCatalog(BaseModel):
    """In-memory dataset of all directives (governance catalog)."""

    model_config = ConfigDict(frozen=True)

    directives: tuple[Directive, ...] = Field(default_factory=tuple)

    def list_all(self) -> tuple[Directive, ...]:
        """List every loaded directive."""
        return self.directives

    def list_active(self) -> tuple[Directive, ...]:
        """List directives whose rules are active."""
        return tuple(d for d in self.directives if d.is_active())

    def list_active_rules(self) -> tuple[Rule, ...]:
        """Executable rules for inspection (policy excluded)."""
        return tuple(d.rule for d in self.list_active())

    def find_by_lineage_id(self, a_lineage_id: str) -> Directive | None:
        """Find one directive by Machine ID / lineage_id."""
        b_continue = True
        result: Directive | None = None
        for directive in self.directives:
            if b_continue and directive.lineage_id == a_lineage_id:
                b_continue = False
                result = directive
            if b_continue and directive.execution_id == a_lineage_id:
                b_continue = False
                result = directive
        return result

    def find_by_codes(self, a_codes: tuple[str, ...]) -> tuple[Directive, ...]:
        """Find directives matching any lineage or execution id in codes."""
        codes = frozenset(a_codes)
        return tuple(
            d
            for d in self.directives
            if d.lineage_id in codes or d.execution_id in codes
        )

    def get_policy(self, a_lineage_id: str) -> DirectivePolicy | None:
        """Return policy for a Machine ID, if present."""
        b_continue = True
        result: DirectivePolicy | None = None
        directive = self.find_by_lineage_id(a_lineage_id)
        if b_continue and directive is None:
            b_continue = False
        if b_continue and directive is not None:
            result = directive.policy
        return result

    def get_rule(self, a_lineage_id: str) -> Rule | None:
        """Return executable rule for a Machine ID, if present."""
        b_continue = True
        result: Rule | None = None
        directive = self.find_by_lineage_id(a_lineage_id)
        if b_continue and directive is None:
            b_continue = False
        if b_continue and directive is not None:
            result = directive.rule
        return result

    def __len__(self) -> int:
        return len(self.directives)
