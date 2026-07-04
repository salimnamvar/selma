"""Tests for the contract repository."""

import tempfile
from pathlib import Path

import yaml

from usecase_diagram.repository.contracts import ContractRepository


def test_contract_repository_loads_from_default():
    repo = ContractRepository()
    bundle = repo.load()
    assert bundle.version == "1.0.0"
    assert len(bundle.rules) > 0
    assert len(bundle.assessments) > 0


def test_contract_repository_caches():
    repo = ContractRepository()
    bundle1 = repo.load()
    bundle2 = repo.load()
    assert bundle1 is bundle2


def test_contract_repository_reload():
    repo = ContractRepository()
    bundle1 = repo.load()
    bundle2 = repo.reload()
    assert bundle1 is not bundle2
    assert bundle1.version == bundle2.version


def test_contract_repository_from_custom_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        contracts_dir = tmpdir / "contracts"
        contracts_dir.mkdir()

        (contracts_dir / "package.yaml").write_text(
            yaml.dump({"version": "2.0.0", "name": "test", "limits": {}})
        )
        rules_data = {
            "rules": [{"id": "T-01", "scope": "per_file",
                        "severity": "error", "check_type": "test"}]
        }
        (contracts_dir / "rules.yaml").write_text(yaml.dump(rules_data))
        (contracts_dir / "principles.yaml").write_text(yaml.dump({"assessments": []}))
        (contracts_dir / "verbs.yaml").write_text(yaml.dump({"banned": []}))
        (contracts_dir / "patterns.yaml").write_text(yaml.dump({}))
        (contracts_dir / "filename_groups.yaml").write_text(yaml.dump({}))

        repo = ContractRepository(contracts_dir)
        bundle = repo.load()
        assert bundle.version == "2.0.0"
        assert len(bundle.rules) == 1
        assert bundle.rules[0].id == "T-01"
