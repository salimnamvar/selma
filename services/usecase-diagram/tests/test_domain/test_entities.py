"""Tests for the domain entities."""

from pathlib import Path

from usecase_diagram.domain.entities.contract import (
    ContractBundle,
    RuleDef,
)
from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.domain.entities.violation import Violation
from usecase_diagram.domain.value_objects.check_scope import CheckScope
from usecase_diagram.domain.value_objects.severity import Severity


def test_uc_diagram_creation():
    diagram = UCDiagram(
        filename="uc_cli.puml",
        title="CLI Use Cases",
        source="@startuml\n@enduml",
        group="CLI",
    )
    assert diagram.filename == "uc_cli.puml"
    assert diagram.group == "CLI"
    assert diagram.usecases == []


def test_rule_def_creation():
    rule = RuleDef(
        id="UC-001",
        scope="per_file",
        severity="error",
        check_type="filename_pattern",
        message="Invalid filename",
    )
    assert rule.id == "UC-001"
    assert rule.severity == "error"


def test_violation_creation():
    violation = Violation(
        rule_id="UC-001",
        severity="error",
        message="Bad filename",
        file="test.puml",
    )
    assert violation.rule_id == "UC-001"
    assert violation.file == "test.puml"


def test_severity_enum():
    assert Severity.ERROR == "error"
    assert Severity.WARNING == "warning"
    assert Severity.INFO == "info"


def test_check_scope_enum():
    assert CheckScope.PER_FILE == "per_file"
    assert CheckScope.PROJECT == "project"


def test_contract_bundle_rules_by_scope():
    bundle = ContractBundle(
        version="1.0.0",
        package={"limits": {"max_usecases_per_diagram": 15}},
        rules=[
            RuleDef(id="R1", scope="per_file", severity="error",
                    check_type="test", message="msg1"),
            RuleDef(id="R2", scope="project", severity="warning",
                    check_type="test", message="msg2"),
        ],
        assessments=[],
        verbs={"banned": ["CREATE"]},
        patterns={"filename": "^uc_.*$"},
        filename_groups={},
        contracts_dir=Path("/tmp"),
    )
    per_file = bundle.rules_by_scope("per_file")
    assert len(per_file) == 1
    assert per_file[0].id == "R1"

    project = bundle.rules_by_scope("project")
    assert len(project) == 1
    assert project[0].id == "R2"


def test_contract_bundle_verbs():
    bundle = ContractBundle(
        version="1.0.0",
        package={},
        rules=[],
        assessments=[],
        verbs={"banned": ["CREATE", "GET"], "api_rest": ["GET", "POST"]},
        patterns={},
        filename_groups={},
        contracts_dir=Path("/tmp"),
    )
    assert "CREATE" in bundle.banned_verbs()
    assert "GET" in bundle.api_rest_verbs()
