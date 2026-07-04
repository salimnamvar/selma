"""Contract repository — loads YAML contracts from the rules directory."""

from __future__ import annotations

from pathlib import Path

import yaml

from usecase_diagram.config.settings import get_config
from usecase_diagram.domain.entities.contract import (
    AssessmentDef,
    ContractBundle,
    RuleDef,
)


class ContractRepository:
    """Loads and caches contract YAML files into a ContractBundle."""

    def __init__(self, contracts_dir: Path | None = None) -> None:
        config = get_config()
        self._dir = contracts_dir or config.resolved_contracts_dir
        self._bundle: ContractBundle | None = None

    def load(self) -> ContractBundle:
        """Load all contract YAML files and return a ContractBundle."""
        if self._bundle is not None:
            return self._bundle

        package = self._load_yaml("package.yaml")
        rules_data = self._load_yaml("rules.yaml")
        principles_data = self._load_yaml("principles.yaml")
        verbs_data = self._load_yaml("verbs.yaml")
        patterns_data = self._load_yaml("patterns.yaml")
        fg_data = self._load_yaml("filename_groups.yaml")

        rules = self._parse_rules(rules_data)
        assessments = self._parse_assessments(principles_data)

        self._bundle = ContractBundle(
            version=package.get("version", "0.0.0"),
            package=package,
            rules=rules,
            assessments=assessments,
            verbs=verbs_data,
            patterns=patterns_data,
            filename_groups=fg_data,
            contracts_dir=self._dir,
        )
        return self._bundle

    def reload(self) -> ContractBundle:
        """Force-reload contracts from disk."""
        self._bundle = None
        return self.load()

    def _load_yaml(self, filename: str) -> dict:
        path = self._dir / filename
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _parse_rules(data: dict) -> list[RuleDef]:
        rules: list[RuleDef] = []
        for entry in data.get("rules", []):
            rules.append(
                RuleDef(
                    id=entry["id"],
                    scope=entry["scope"],
                    severity=entry.get("severity", "warning"),
                    check_type=entry["check_type"],
                    message=entry.get("message", ""),
                    principle=entry.get("principle", ""),
                    policy_ref=entry.get("policy_ref", ""),
                    reasoning=entry.get("reasoning", ""),
                    fix=entry.get("fix", ""),
                    params=entry.get("params", {}),
                    skip_when=entry.get("skip_when"),
                )
            )
        return rules

    @staticmethod
    def _parse_assessments(data: dict) -> list[AssessmentDef]:
        assessments: list[AssessmentDef] = []
        for entry in data.get("assessments", []):
            assessments.append(
                AssessmentDef(
                    id=entry["id"],
                    name=entry.get("name", ""),
                    check_type=entry["check_type"],
                    ok_detail=entry.get("ok_detail", ""),
                    reasoning=entry.get("reasoning", ""),
                    skip_when_no_sq=entry.get("skip_when_no_sq", False),
                )
            )
        return assessments
