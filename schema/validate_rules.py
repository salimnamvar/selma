#!/usr/bin/env python3
"""Validate all rule JSON files against rule_schema.json using jsonschema."""

import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator, ValidationError

SCHEMA_PATH = Path(__file__).parent / "rule_schema.json"
RULES_DIR = Path(__file__).parent / "rules"


def load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_rule(rule_path: Path, schema: dict, validator: Draft7Validator) -> list[str]:
    """Validate a single rule file. Returns list of error messages."""
    errors = []
    try:
        with open(rule_path) as f:
            rule = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    for error in validator.iter_errors(rule):
        path = " -> ".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  [{path}] {error.message}")

    return errors


def main() -> int:
    schema = load_schema()
    validator = Draft7Validator(schema)

    rule_files = sorted(RULES_DIR.glob("*.json"))
    if not rule_files:
        print("No rule files found!")
        return 1

    total = len(rule_files)
    passed = 0
    failed = 0
    warnings = []

    print(f"Validating {total} rule files against {SCHEMA_PATH.name}\n")

    for rule_file in rule_files:
        errors = validate_rule(rule_file, schema, validator)
        if errors:
            failed += 1
            print(f"FAIL  {rule_file.name}")
            for err in errors:
                print(err)
            print()
        else:
            passed += 1
            print(f"OK    {rule_file.name}")

    # Check for duplicate lineage_ids
    lineage_ids = {}
    for rule_file in rule_files:
        try:
            with open(rule_file) as f:
                rule = json.load(f)
            lid = rule.get("lineage_id")
            if lid:
                if lid in lineage_ids:
                    warnings.append(f"Duplicate lineage_id '{lid}': {lineage_ids[lid]} and {rule_file.name}")
                lineage_ids[lid] = rule_file.name
        except (json.JSONDecodeError, KeyError):
            pass

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {total} rules")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
