"""Tests for contract validators."""

from pathlib import Path

import pytest
from rule_manager.validate import (
    validate_contamination,
    validate_policy_structure,
    validate_rules_schema,
    validate_traceability,
)


@pytest.fixture
def contracts_dir() -> Path:
    """Return the contracts directory path."""
    return Path(__file__).parent.parent.parent.parent / "contracts"


@pytest.fixture
def doctrine_path(contracts_dir: Path) -> Path:
    """Return the doctrine file path."""
    return contracts_dir / "policy_doctrine.yaml"


@pytest.fixture
def schema_path(contracts_dir: Path) -> Path:
    """Return the schema file path."""
    return contracts_dir / "rule_schema.json"


class TestPolicyValidation:
    """Tests for policy document validation."""

    def test_valid_policy_passes(self, doctrine_path: Path) -> None:
        """A well-formed policy should pass validation."""
        policy_content = """# Test Policy

## Preamble

This is a test policy.

## Governance & Amendment

Standard governance process.

## Definitions

| Term | Definition | Exclusion |
|------|-----------|-----------|
| Test | A test | Not a test |

## Foundational Principles

Standard principles.

## Directives

### Specific Directives

| Type | Description | Machine ID | Context |
|------|-------------|------------|---------|
| Obligation | Test rule | TEST-001 | Always |

### Flexible Standards

| Description | Machine ID | Factors | Examples |
|-------------|------------|---------|----------|
| Test standard | STND-001 | Factors | Examples |

## Sanctions & Remedies

| Violation | Enforcement | Remediation |
|-----------|-------------|-------------|
| Test | Fine $100 | Course |

"""
        policy_path = Path("/tmp/test_policy.md")
        policy_path.write_text(policy_content)

        result = validate_policy_structure(policy_path, doctrine_path)
        assert result.is_valid, result.summary()

    def test_missing_required_section_fails(self, tmp_path: Path, doctrine_path: Path) -> None:
        """Policy missing required sections should fail."""
        policy_content = """# Test Policy

## Preamble

This is a test.

"""
        policy_path = tmp_path / "policy.md"
        policy_path.write_text(policy_content)

        result = validate_policy_structure(policy_path, doctrine_path)
        # Should have errors for missing required sections
        assert not result.is_valid

    def test_contamination_guard(self, tmp_path: Path, doctrine_path: Path) -> None:
        """Policy containing forbidden fields as structured data keys should trigger warnings."""
        policy_content = """# Test Policy

## Preamble

This code uses parameters for configuration.

## Governance & Amendment

Standard governance process.

## Definitions

| Term | Definition | Exclusion |
|------|-----------|-----------|
| Test | A test | Not a test |

## Foundational Principles

Standard principles.

## Directives

### Specific Directives

| Type | Description | Machine ID | Context |
|------|-------------|------------|---------|
| Obligation | Test rule | TEST-001 | Always |

### Flexible Standards

| Description | Machine ID | Factors | Examples |
|-------------|------------|---------|----------|
| Test standard | STND-001 | Factors | Examples |

## Sanctions & Remedies

| Violation | Enforcement | Remediation |
|-----------|-------------|-------------|
| Test | Fine $100 | Course |

parameters:
  some_key: some_value

"""
        policy_path = tmp_path / "policy.md"
        policy_path.write_text(policy_content)

        result = validate_policy_structure(policy_path, doctrine_path)
        # Should have warning about forbidden field 'parameters' as structured data key
        warnings = [e for e in result.errors if e.severity == "warning"]
        assert any("parameters" in w.message for w in warnings)


class TestRulesValidation:
    """Tests for rules schema validation."""

    def test_valid_rules_pass(self, schema_path: Path) -> None:
        """A well-formed rules file should pass validation."""
        rules_content = """version: "1.0.0"
policy_contract_version: "1.3.0"
rules:
  - id: TEST-001
    type: obligation
    message: "Test rule"
"""
        rules_path = Path("/tmp/test_rules.yaml")
        rules_path.write_text(rules_content)

        result = validate_rules_schema(rules_path, schema_path)
        assert result.is_valid, result.summary()

    def test_missing_required_field_fails(self, tmp_path: Path, schema_path: Path) -> None:
        """Rules missing required fields should fail."""
        rules_content = """version: "1.0.0"
rules:
  - id: TEST-001
    # Missing required 'type' field
    message: "Test rule"
"""
        rules_path = tmp_path / "rules.yaml"
        rules_path.write_text(rules_content)

        result = validate_rules_schema(rules_path, schema_path)
        assert not result.is_valid

    def test_contamination_in_rules(self, tmp_path: Path, schema_path: Path) -> None:
        """Rules containing forbidden fields should trigger warnings."""
        rules_content = """version: "1.0.0"
preamble: "This should not be here"
rules:
  - id: TEST-001
    type: obligation
    message: "Test rule"
"""
        rules_path = tmp_path / "rules.yaml"
        rules_path.write_text(rules_content)

        result = validate_contamination(rules_path, schema_path)
        warnings = [e for e in result.errors if e.severity == "warning"]
        # Should have warning about forbidden field 'preamble' at root level
        assert any("preamble" in w.message for w in warnings)


class TestTraceability:
    """Tests for bidirectional traceability validation."""

    def test_valid_traceability(self, doctrine_path: Path) -> None:
        """Well-linked policy and rules should pass traceability."""
        policy_content = """# Test Policy

## Preamble

Test.

## Governance & Amendment

Test.

## Definitions

| Term | Definition | Exclusion |
|------|-----------|-----------|
| Test | A test | Not a test |

## Foundational Principles

Test.

## Directives

### Specific Directives

| Type | Description | Machine ID | Context |
|------|-------------|------------|---------|
| Obligation | Test rule | TEST-001 | Always |

### Flexible Standards

| Description | Machine ID | Factors | Examples |
|-------------|------------|---------|----------|
| Test standard | STND-001 | Factors | Examples |

## Sanctions & Remedies

| Violation | Enforcement | Remediation |
|-----------|-------------|-------------|
| Test | Fine $100 | Course |

"""
        rules_content = """version: "1.0.0"
policy_contract_version: "1.3.0"
rules:
  - id: TEST-001
    type: obligation
    message: "Test rule"
    anchor_ref: "section:directives"
  - id: STND-001
    type: standard
    message: "Test standard"
    anchor_ref: "section:directives"
"""
        policy_path = Path("/tmp/test_policy_trace.md")
        rules_path = Path("/tmp/test_rules_trace.yaml")
        policy_path.write_text(policy_content)
        rules_path.write_text(rules_content)

        result = validate_traceability(policy_path, rules_path, doctrine_path)
        assert result.is_valid, result.summary()

    def test_missing_rule_in_policy(self, tmp_path: Path, doctrine_path: Path) -> None:
        """Rule ID not referenced in policy should fail."""
        policy_content = """# Test Policy

## Preamble

Test.

## Governance & Amendment

Test.

## Definitions

| Term | Definition | Exclusion |
|------|-----------|-----------|
| Test | A test | Not a test |

## Foundational Principles

Test.

## Directives

### Specific Directives

| Type | Description | Machine ID | Context |
|------|-------------|------------|---------|
| Obligation | Test rule | OTHER-001 | Always |

### Flexible Standards

| Description | Machine ID | Factors | Examples |
|-------------|------------|---------|----------|
| Test standard | STND-002 | Factors | Examples |

## Sanctions & Remedies

| Violation | Enforcement | Remediation |
|-----------|-------------|-------------|
| Test | Fine $100 | Course |

"""
        rules_content = """version: "1.0.0"
policy_contract_version: "1.2.0"
rules:
  - id: TEST-001
    type: obligation
    message: "Test rule"
    anchor_ref: "section:directives"
"""
        policy_path = tmp_path / "policy.md"
        rules_path = tmp_path / "rules.yaml"
        policy_path.write_text(policy_content)
        rules_path.write_text(rules_content)

        result = validate_traceability(policy_path, rules_path, doctrine_path)
        # Should have error: TEST-001 in rules but not in policy
        errors = [e for e in result.errors if e.severity == "error"]
        assert any("TEST-001" in e.message for e in errors)

    def test_version_mismatch(self, tmp_path: Path, doctrine_path: Path) -> None:
        """Version mismatch between policy and rules should fail."""
        policy_content = """# Test Policy

## Preamble

Test.

## Governance & Amendment

Test.

## Definitions

| Term | Definition | Exclusion |
|------|-----------|-----------|
| Test | A test | Not a test |

## Foundational Principles

Test.

## Directives

### Specific Directives

| Type | Description | Machine ID | Context |
|------|-------------|------------|---------|
| Obligation | Test rule | TEST-001 | Always |

### Flexible Standards

| Description | Machine ID | Factors | Examples |
|-------------|------------|---------|----------|
| Test standard | STND-001 | Factors | Examples |

## Sanctions & Remedies

| Violation | Enforcement | Remediation |
|-----------|-------------|-------------|
| Test | Fine $100 | Course |

"""
        rules_content = """version: "1.0.0"
policy_contract_version: "99.0.0"
rules:
  - id: TEST-001
    type: obligation
    message: "Test rule"
    anchor_ref: "section:directives"
"""
        policy_path = tmp_path / "policy.md"
        rules_path = tmp_path / "rules.yaml"
        policy_path.write_text(policy_content)
        rules_path.write_text(rules_content)

        result = validate_traceability(policy_path, rules_path, doctrine_path)
        assert any("Version mismatch" in e.message for e in result.errors)
