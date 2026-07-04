"""Contract repository — loads YAML contracts from the rules directory."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from usecase_diagram.config.settings import get_config
from usecase_diagram.domain.entities.contract import (
    AssessmentDef,
    ContractBundle,
    RuleDef,
)


class ContractRepository:
    """Loads and caches contract YAML files into a ContractBundle.

    Attributes:
        _dir (Path): Directory containing rule files.
        _bundle (Optional[ContractBundle]): Cached loaded bundle.
    """

    def __init__(self, a_rules_dir: Optional[Path] = None) -> None:
        """Initialize with optional rules directory override.

        Args:
            a_rules_dir (Optional[Path]): Rules directory or None for default.
        """
        config = get_config()
        self._dir: Path = a_rules_dir or config.rules_dir
        self._bundle: Optional[ContractBundle] = None

    def load(self) -> ContractBundle:
        """Load all contract YAML files and return a ContractBundle.

        Returns:
            ContractBundle: Loaded contract bundle.
        """
        if self._bundle is not None:
            return self._bundle

        config = get_config()
        data: Dict[str, Any] = self._load_yaml(config.resolved_rules_file)

        rules: List[RuleDef] = self._parse_rules(data)
        assessments: List[AssessmentDef] = self._parse_assessments(data)

        self._bundle = ContractBundle(
            version=data.get("version", "0.0.0"),
            package=data,
            rules=rules,
            assessments=assessments,
            verbs=data.get("verbs", {}),
            patterns=data.get("patterns", {}),
            filename_groups=data.get("filename_groups", {}),
            rules_dir=self._dir,
        )
        return self._bundle

    def reload(self) -> ContractBundle:
        """Force-reload contracts from disk.

        Returns:
            ContractBundle: Freshly loaded contract bundle.
        """
        self._bundle = None
        result: ContractBundle = self.load()
        return result

    @staticmethod
    def _load_yaml(a_path: Path) -> Dict[str, Any]:
        """Load a YAML file from the given path.

        Args:
            a_path (Path): Path to the YAML file.

        Returns:
            Dict[str, Any]: Parsed YAML data as dict, or empty dict.
        """
        result: Dict[str, Any] = {}
        if a_path.exists():
            with open(a_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                result = data
        return result

    @staticmethod
    def _parse_rules(a_data: Dict[str, Any]) -> List[RuleDef]:
        """Parse rule definitions from YAML data.

        Args:
            a_data (Dict[str, Any]): Raw YAML rules data.

        Returns:
            List[RuleDef]: Parsed rule definitions.
        """
        rules: List[RuleDef] = []
        for entry in a_data.get("rules", []):
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
    def _parse_assessments(a_data: Dict[str, Any]) -> List[AssessmentDef]:
        """Parse assessment definitions from YAML data.

        Args:
            a_data (Dict[str, Any]): Raw YAML data.

        Returns:
            List[AssessmentDef]: Parsed assessment definitions.
        """
        assessments: List[AssessmentDef] = []
        for entry in a_data.get("assessments", []):
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
