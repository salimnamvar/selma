"""Tests for Selma Regulation contract validators."""

from pathlib import Path

from scripts.validate_contracts import (
    validate_all,
    validate_audit_clarifications,
    validate_policy_runtime_prohibition,
    validate_version_synchronization,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


class TestPolicyRuntimeProhibition:
    def test_runtime_source_has_no_policy_references(self) -> None:
        result = validate_policy_runtime_prohibition(repo_root())
        errors = [e for e in result.errors if e.severity == "error"]
        assert not errors, result.summary()

    def test_detects_policy_reference_in_runtime_source(self, tmp_path: Path) -> None:
        runtime_dir = tmp_path / "src" / "selma"
        runtime_dir.mkdir(parents=True)
        (runtime_dir / "engine.py").write_text('DOCTRINE = "policy_doctrine.yaml"\n')

        result = validate_policy_runtime_prohibition(tmp_path)
        assert not result.is_valid
        assert any("policy doctrine" in e.message for e in result.errors)


class TestVersionSynchronization:
    def test_contract_versions_share_major_family(self) -> None:
        result = validate_version_synchronization(repo_root())
        errors = [e for e in result.errors if e.severity == "error"]
        assert not errors, result.summary()


class TestAuditClarifications:
    def test_spec_contains_audit_clarifications(self) -> None:
        result = validate_audit_clarifications(repo_root())
        errors = [e for e in result.errors if e.severity == "error"]
        assert not errors, result.summary()

    def test_user_stories_has_segregation_column(self) -> None:
        stories = (repo_root() / "docs" / "User-Story" / "User_Stories.md").read_text(encoding="utf-8")
        assert "Segregation of Duties Constraint" in stories


class TestValidateAll:
    def test_full_contract_validation_passes(self) -> None:
        result = validate_all(repo_root())
        assert result.is_valid, result.summary()