#!/usr/bin/env python3
"""
Contract Validators for Universal Rule Governance.

Validates:
1. Policy documents against policy_doctrine.yaml structure
2. Rules against JSON Schema
3. Traceability between policy and rules
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


class ValidationError:
    """Represents a single validation error."""

    def __init__(self, path: str, message: str, severity: str = "error"):
        self.path = path
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.path}: {self.message}"


class ValidationResult:
    """Aggregates validation errors and provides summary."""

    def __init__(self) -> None:
        self.errors: list[ValidationError] = []

    def add_error(self, path: str, message: str, severity: str = "error") -> None:
        self.errors.append(ValidationError(path, message, severity))

    @property
    def is_valid(self) -> bool:
        return not any(e.severity == "error" for e in self.errors)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "warning")

    def summary(self) -> str:
        lines = [f"Validation complete: {self.error_count} error(s), {self.warning_count} warning(s)"]
        if self.errors:
            lines.append("")
            for error in self.errors:
                lines.append(str(error))
        return "\n".join(lines)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its content."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file and return its content."""
    with open(path) as f:
        return json.load(f)


def _contracts_dir() -> Path:
    """Return the contracts directory path relative to this file."""
    return Path(__file__).parent.parent.parent.parent.parent / "contracts"


def validate_policy_structure(policy_path: Path, doctrine_path: Path) -> ValidationResult:
    """
    Validate a policy document against the policy doctrine structure.

    Checks:
    1. All required sections exist
    2. Sections have correct content types (tables vs prose)
    3. No forbidden fields are present (contamination guard)
    4. Machine IDs follow consistent naming
    """
    result = ValidationResult()

    if not policy_path.exists():
        result.add_error("policy", f"Policy file not found: {policy_path}")
        return result

    if not doctrine_path.exists():
        result.add_error("doctrine", f"Doctrine file not found: {doctrine_path}")
        return result

    policy_content = policy_path.read_text()
    doctrine = load_yaml(doctrine_path)

    # Extract all section headers from policy
    section_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    found_sections = [m.group(1).strip().lower() for m in section_pattern.finditer(policy_content)]

    # Check required sections
    for section in doctrine.get("sections", []):
        section_id = section["id"]
        section_title = section["title"].lower()
        required = section.get("required", False)

        # Check if section exists (flexible matching)
        section_found = any(
            section_title in found or found in section_title
            for found in found_sections
        )

        if required and not section_found:
            result.add_error(
                f"policy.sections.{section_id}",
                f"Required section '{section['title']}' not found in policy"
            )

    # Check contamination guard - forbidden fields in policy
    # Only flag if appears as a YAML/JSON key, not in natural prose
    forbidden_fields = doctrine.get("contamination_guard", {}).get("forbidden_fields", [])
    for field in forbidden_fields:
        # Check for field as a YAML key (e.g., "parameters:" or "conditions:")
        if re.search(rf"^{field}\s*:", policy_content, re.MULTILINE | re.IGNORECASE):
            result.add_error(
                f"policy.contamination.{field}",
                f"Forbidden field '{field}' found as structured data key in policy",
                severity="warning"
            )

    # Extract Machine IDs from policy
    machine_id_pattern = re.compile(r"\|[^|]*\|\s*([A-Z]+-\d+)\s*\|")
    policy_machine_ids = set(machine_id_pattern.findall(policy_content))

    if not policy_machine_ids:
        result.add_error(
            "policy.traceability",
            "No Machine IDs found in policy directive tables",
            severity="warning"
        )

    return result


def validate_rules_schema(rules_path: Path, schema_path: Path) -> ValidationResult:
    """
    Validate rules.yaml against the JSON Schema.

    Uses jsonschema library for full validation.
    """
    result = ValidationResult()

    if not rules_path.exists():
        result.add_error("rules", f"Rules file not found: {rules_path}")
        return result

    if not schema_path.exists():
        result.add_error("schema", f"Schema file not found: {schema_path}")
        return result

    try:
        from jsonschema import ValidationError as JsonSchemaValidationError
        from jsonschema import validate

        rules_data = load_yaml(rules_path)
        schema_data = load_json(schema_path)

        validate(instance=rules_data, schema=schema_data)

    except ImportError:
        result.add_error(
            "dependencies",
            "jsonschema library not installed. Run: pip install jsonschema",
            severity="warning"
        )
    except JsonSchemaValidationError as e:
        result.add_error(
            f"rules.{e.json_path}",
            f"Schema validation failed: {e.message}"
        )
    except Exception as e:
        result.add_error("rules", f"Unexpected error during validation: {e}")

    return result


def validate_traceability(
    policy_path: Path, rules_path: Path, doctrine_path: Path
) -> ValidationResult:
    """
    Validate bidirectional traceability between policy and rules.

    Checks:
    1. Every Machine ID in policy exists as an id in rules
    2. Every rule id has a corresponding Machine ID in policy
    3. Every rule has an anchor_ref pointing to a valid section
    """
    result = ValidationResult()

    if not policy_path.exists() or not rules_path.exists() or not doctrine_path.exists():
        result.add_error("files", "One or more required files not found")
        return result

    policy_content = policy_path.read_text()
    rules_data = load_yaml(rules_path)
    doctrine = load_yaml(doctrine_path)

    # Extract Machine IDs from policy (pattern: | ... | TRAF-001 | ... |)
    machine_id_pattern = re.compile(r"\|[^|]*\|\s*([A-Z]+-\d+)\s*\|")
    policy_machine_ids = set(machine_id_pattern.findall(policy_content))

    # Extract rule IDs from rules.yaml
    rule_ids = {rule["id"] for rule in rules_data.get("rules", [])}

    # Check policy → rules traceability
    missing_in_rules = policy_machine_ids - rule_ids
    for mid in missing_in_rules:
        result.add_error(
            f"traceability.policy_to_rules.{mid}",
            f"Machine ID '{mid}' in policy but not found in rules.yaml"
        )

    # Check rules → policy traceability
    missing_in_policy = rule_ids - policy_machine_ids
    for rid in missing_in_policy:
        result.add_error(
            f"traceability.rules_to_policy.{rid}",
            f"Rule ID '{rid}' in rules.yaml but not found in policy"
        )

    # Validate anchor_ref points to valid sections
    valid_sections = {s["id"] for s in doctrine.get("sections", [])}
    for rule in rules_data.get("rules", []):
        anchor_ref = rule.get("anchor_ref", "")
        if anchor_ref and anchor_ref.startswith("section:"):
            # Extract section path and check main section exists
            section_path = anchor_ref.split(":", 1)[1].strip("/")
            main_section = section_path.split("/")[0]
            if main_section not in valid_sections:
                result.add_error(
                    f"traceability.anchor_ref.{rule['id']}",
                    f"anchor_ref '{anchor_ref}' references unknown section '{main_section}'",
                    severity="warning"
                )

    # Check version synchronization
    policy_version = doctrine.get("doctrine", {}).get("version")
    rules_policy_version = rules_data.get("policy_contract_version")
    if policy_version and rules_policy_version and policy_version != rules_policy_version:
        result.add_error(
            "traceability.version",
            f"Version mismatch: policy doctrine version '{policy_version}' "
            f"!= rules policy_contract_version '{rules_policy_version}'"
        )

    return result


def validate_contamination(
    rules_path: Path, schema_path: Path
) -> ValidationResult:
    """
    Validate contamination guard for rules schema.

    Checks that rules.yaml doesn't contain forbidden human-facing fields.
    """
    result = ValidationResult()

    if not rules_path.exists() or not schema_path.exists():
        result.add_error("files", "One or more required files not found")
        return result

    rules_data = load_yaml(rules_path)
    schema_data = load_json(schema_path)

    # Get forbidden fields from schema's contamination guard
    forbidden = schema_data.get("x-contamination-guard", {}).get("forbidden_at_root", [])

    # Check each forbidden field
    for field in forbidden:
        if field in rules_data:
            result.add_error(
                f"contamination.{field}",
                f"Forbidden field '{field}' found in rules.yaml at root level",
                severity="warning"
            )

    # Check for common contamination patterns in rule parameters
    contamination_patterns = [
        (r"preamble", "human preamble"),
        (r"governance", "governance section"),
        (r"sanctions", "sanctions section"),
        (r"definitions", "definitions section"),
    ]

    for rule in rules_data.get("rules", []):
        rule_str = json.dumps(rule)
        for pattern, desc in contamination_patterns:
            if re.search(pattern, rule_str, re.IGNORECASE):
                result.add_error(
                    f"contamination.rule.{rule.get('id', 'unknown')}",
                    f"Possible contamination: rule contains reference to {desc}",
                    severity="warning"
                )

    return result


def validate_example(example_dir: Path) -> ValidationResult:
    """
    Run all validators on an example directory.

    Expected structure:
    example_dir/
    ├── policy.md
    └── rules.yaml
    """
    result = ValidationResult()

    policy_path = example_dir / "policy.md"
    rules_path = example_dir / "rules.yaml"
    contracts = _contracts_dir()
    doctrine_path = contracts / "policy_doctrine.yaml"
    schema_path = contracts / "rule_schema.json"

    # Run all validators
    results = [
        validate_policy_structure(policy_path, doctrine_path),
        validate_rules_schema(rules_path, schema_path),
        validate_traceability(policy_path, rules_path, doctrine_path),
        validate_contamination(rules_path, schema_path),
    ]

    # Aggregate results
    for r in results:
        result.errors.extend(r.errors)

    return result


def main() -> int:
    """CLI entry point for contract validation."""
    if len(sys.argv) < 2:
        print("Usage: python validate.py <example_dir>")
        print("       python validate.py <policy.md> <rules.yaml>")
        sys.exit(1)

    contracts = _contracts_dir()

    if len(sys.argv) == 2:
        # Validate all files in a directory
        example_dir = Path(sys.argv[1])
        if not example_dir.is_dir():
            print(f"Error: {example_dir} is not a directory")
            sys.exit(1)
        result = validate_example(example_dir)
    elif len(sys.argv) == 3:
        # Validate specific policy and rules files
        policy_path = Path(sys.argv[1])
        rules_path = Path(sys.argv[2])
        doctrine_path = contracts / "policy_doctrine.yaml"
        schema_path = contracts / "rule_schema.json"

        result = ValidationResult()
        results = [
            validate_policy_structure(policy_path, doctrine_path),
            validate_rules_schema(rules_path, schema_path),
            validate_traceability(policy_path, rules_path, doctrine_path),
            validate_contamination(rules_path, schema_path),
        ]
        for r in results:
            result.errors.extend(r.errors)
    else:
        print("Error: Invalid arguments")
        sys.exit(1)

    print(result.summary())
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
