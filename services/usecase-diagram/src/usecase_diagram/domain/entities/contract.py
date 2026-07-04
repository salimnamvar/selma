"""Contract entities — rule definitions, assessment definitions, and the contract bundle."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RuleDef:
    """A single validation rule loaded from contracts/rules.yaml."""

    id: str
    scope: str
    severity: str
    check_type: str
    message: str
    principle: str = ""
    policy_ref: str = ""
    reasoning: str = ""
    fix: str = ""
    params: dict = field(default_factory=dict)
    skip_when: dict | None = None


@dataclass(frozen=True)
class AssessmentDef:
    """A project-level assessment contract loaded from contracts/principles.yaml."""

    id: str
    name: str
    check_type: str
    ok_detail: str = ""
    reasoning: str = ""
    skip_when_no_sq: bool = False


@dataclass
class ContractBundle:
    """Immutable bundle of all loaded contracts for a validation session."""

    version: str
    package: dict
    rules: list[RuleDef]
    assessments: list[AssessmentDef]
    verbs: dict
    patterns: dict
    filename_groups: dict
    contracts_dir: Path

    def rules_by_scope(self, scope: str) -> list[RuleDef]:
        return [r for r in self.rules if r.scope == scope]

    def rule_by_id(self, rule_id: str) -> RuleDef | None:
        for r in self.rules:
            if r.id == rule_id:
                return r
        return None

    def rules_by_check_type(self, check_type: str) -> list[RuleDef]:
        return [r for r in self.rules if r.check_type == check_type]

    @property
    def limits(self) -> dict:
        return self.package.get("limits", {})

    @property
    def csr_layers(self) -> list[str]:
        return self.package.get("csr", {}).get("layers", [])

    @property
    def csr_tier(self) -> dict[str, int]:
        return {name: i for i, name in enumerate(self.csr_layers)}

    @property
    def skip_dir_names(self) -> set[str]:
        return set(self.package.get("discovery", {}).get("skip", []))

    def allowed_verbs(self, category: str | None = None) -> set[str]:
        verbs = set()
        for cat, word_list in self.verbs.items():
            if category is None or cat == category:
                verbs.update(word_list)
        return verbs

    def banned_verbs(self) -> set[str]:
        return set(self.verbs.get("banned", []))

    def api_rest_verbs(self) -> set[str]:
        return set(self.verbs.get("api_rest", []))

    def compiled_patterns(self) -> dict:
        import re
        compiled = {}
        for key, value in self.patterns.items():
            if isinstance(value, str):
                compiled[key] = re.compile(value)
            elif isinstance(value, list):
                compiled[key] = [re.compile(p) for p in value]
            else:
                compiled[key] = value
        return compiled

    def metadata_hint_pattern(self):
        import re
        hints = self.patterns.get("metadata_hints", [])
        if hints:
            return re.compile("|".join(hints), re.IGNORECASE)
        return None
