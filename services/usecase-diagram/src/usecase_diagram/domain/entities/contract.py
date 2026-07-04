"""Contract entities — rule definitions, assessment definitions, and the contract bundle."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Set


@dataclass(frozen=True)
class RuleDef:
    """A single validation rule loaded from contracts/rules.yaml.

    Attributes:
        id (str): Unique rule identifier.
        scope (str): Rule scope (per_file, per_uc, project).
        severity (str): Violation severity level.
        check_type (str): Check executor key.
        message (str): Violation message template.
        principle (str): Associated principle reference.
        policy_ref (str): Policy reference.
        reasoning (str): Explanation of why the rule exists.
        fix (str): Fix instruction.
        params (Dict[str, Any]): Rule-specific parameters.
        skip_when (Optional[Dict[str, Any]]): Conditions to skip the rule.
    """

    id: str = field(metadata={"description": "Unique rule identifier"})
    scope: str = field(metadata={"description": "Rule scope"})
    severity: str = field(metadata={"description": "Violation severity level"})
    check_type: str = field(metadata={"description": "Check executor key"})
    message: str = field(metadata={"description": "Violation message template"})
    principle: str = field(default="", metadata={"description": "Associated principle reference"})
    policy_ref: str = field(default="", metadata={"description": "Policy reference"})
    reasoning: str = field(
        default="", metadata={"description": "Explanation of why the rule exists"}
    )
    fix: str = field(default="", metadata={"description": "Fix instruction"})
    params: Dict[str, Any] = field(
        default_factory=dict, metadata={"description": "Rule-specific parameters"}
    )
    skip_when: Optional[Dict[str, Any]] = field(
        default=None, metadata={"description": "Conditions to skip the rule"}
    )


@dataclass(frozen=True)
class AssessmentDef:
    """A project-level assessment contract loaded from contracts/principles.yaml.

    Attributes:
        id (str): Unique assessment identifier.
        name (str): Human-readable assessment name.
        check_type (str): Assessment executor key.
        ok_detail (str): Detail message when assessment passes.
        reasoning (str): Explanation of the assessment purpose.
        skip_when_no_sq (bool): Skip when no SQ diagrams exist.
    """

    id: str = field(metadata={"description": "Unique assessment identifier"})
    name: str = field(metadata={"description": "Human-readable assessment name"})
    check_type: str = field(metadata={"description": "Assessment executor key"})
    ok_detail: str = field(
        default="", metadata={"description": "Detail message when assessment passes"}
    )
    reasoning: str = field(
        default="", metadata={"description": "Explanation of the assessment purpose"}
    )
    skip_when_no_sq: bool = field(
        default=False, metadata={"description": "Skip when no SQ diagrams exist"}
    )


@dataclass
class ContractBundle:
    """Bundle of all loaded contracts for a validation session.

    Attributes:
        version (str): Contract version string.
        package (Dict[str, Any]): Package-level configuration.
        rules (List[RuleDef]): Loaded validation rules.
        assessments (List[AssessmentDef]): Loaded assessment definitions.
        verbs (Dict[str, Any]): Verb registry data.
        patterns (Dict[str, Any]): Regex pattern definitions.
        filename_groups (Dict[str, Any]): Filename group mappings.
        contracts_dir (Path): Directory containing contract files.
    """

    version: str = field(metadata={"description": "Contract version string"})
    package: Dict[str, Any] = field(metadata={"description": "Package-level configuration"})
    rules: List[RuleDef] = field(metadata={"description": "Loaded validation rules"})
    assessments: List[AssessmentDef] = field(
        metadata={"description": "Loaded assessment definitions"}
    )
    verbs: Dict[str, Any] = field(metadata={"description": "Verb registry data"})
    patterns: Dict[str, Any] = field(metadata={"description": "Regex pattern definitions"})
    filename_groups: Dict[str, Any] = field(metadata={"description": "Filename group mappings"})
    contracts_dir: Path = field(metadata={"description": "Directory containing contract files"})

    def rules_by_scope(self, a_scope: str) -> List[RuleDef]:
        """Return rules matching the given scope.

        Args:
            a_scope (str): Scope to filter by.

        Returns:
            List[RuleDef]: Matching rules.
        """
        result: List[RuleDef] = [r for r in self.rules if r.scope == a_scope]
        return result

    def rule_by_id(self, a_rule_id: str) -> Optional[RuleDef]:
        """Return the rule with the given ID, or None.

        Args:
            a_rule_id (str): Rule identifier to look up.

        Returns:
            Optional[RuleDef]: Matching rule or None.
        """
        result: Optional[RuleDef] = None
        for r in self.rules:
            if r.id == a_rule_id:
                result = r
                break
        return result

    def rules_by_check_type(self, a_check_type: str) -> List[RuleDef]:
        """Return rules matching the given check type.

        Args:
            a_check_type (str): Check type to filter by.

        Returns:
            List[RuleDef]: Matching rules.
        """
        result: List[RuleDef] = [r for r in self.rules if r.check_type == a_check_type]
        return result

    @property
    def limits(self) -> Dict[str, Any]:
        """Package limits configuration."""
        result: Dict[str, Any] = self.package.get("limits", {})
        return result

    @property
    def csr_layers(self) -> List[str]:
        """CSR layer names from package config."""
        result: List[str] = self.package.get("csr", {}).get("layers", [])
        return result

    @property
    def csr_tier(self) -> Dict[str, int]:
        """CSR layer name to tier index mapping."""
        result: Dict[str, int] = {name: i for i, name in enumerate(self.csr_layers)}
        return result

    @property
    def skip_dir_names(self) -> Set[str]:
        """Directory names to skip during discovery."""
        result: Set[str] = set(self.package.get("discovery", {}).get("skip", []))
        return result

    def allowed_verbs(self, a_category: Optional[str] = None) -> Set[str]:
        """Return allowed verbs, optionally filtered by category.

        Args:
            a_category (Optional[str]): Category to filter by, or None for all.

        Returns:
            Set[str]: Allowed verb strings.
        """
        verbs: Set[str] = set()
        for cat, word_list in self.verbs.items():
            if a_category is None or cat == a_category:
                verbs.update(word_list)
        return verbs

    def banned_verbs(self) -> Set[str]:
        """Return the set of banned verbs.

        Returns:
            Set[str]: Banned verb strings.
        """
        result: Set[str] = set(self.verbs.get("banned", []))
        return result

    def api_rest_verbs(self) -> Set[str]:
        """Return the set of API REST verbs.

        Returns:
            Set[str]: API REST verb strings.
        """
        result: Set[str] = set(self.verbs.get("api_rest", []))
        return result

    def compiled_patterns(self) -> Dict[str, Any]:
        """Compile regex patterns from the patterns dictionary.

        Returns:
            Dict[str, Any]: Compiled patterns keyed by pattern name.
        """
        compiled: Dict[str, Any] = {}
        for key, value in self.patterns.items():
            if isinstance(value, str):
                compiled[key] = re.compile(value)
            elif isinstance(value, list):
                compiled[key] = [re.compile(p) for p in value]
            else:
                compiled[key] = value
        return compiled

    def metadata_hint_pattern(self) -> Optional[Pattern[str]]:
        """Return compiled metadata hint pattern, or None.

        Returns:
            Optional[Pattern[str]]: Compiled regex or None.
        """
        result: Optional[Pattern[str]] = None
        hints: List[str] = self.patterns.get("metadata_hints", [])
        if hints:
            result = re.compile("|".join(hints), re.IGNORECASE)
        return result
