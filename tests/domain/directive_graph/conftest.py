"""Shared fixtures for Directive Graph tests.

Provides minimal valid directive and graph factories used across all
directive_graph test modules.
"""

from __future__ import annotations

from typing import Any

import pytest

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.enums import (
    DeonticType,
    DirectiveStatus,
    EvaluatorType,
    PriorityLevel,
)
from domain.directive_graph.scalars import SemanticVersion
from domain.directive_graph.value_objects.audit import AuditTrail
from domain.directive_graph.value_objects.metadata import DirectiveMetadata


# ---------------------------------------------------------------------------
# Minimal valid directive payload (JSON schema format)
# ---------------------------------------------------------------------------

MINIMAL_REGEX_EVALUATOR = {
    "evaluator_type": "regex",
    "evaluator_config": {"pattern": "^test$"},
}


def make_directive_payload(**overrides: Any) -> dict[str, Any]:
    """Return a minimal valid directive dictionary in JSON schema format."""
    payload: dict[str, Any] = {
        "lineage_id": "RULE-001",
        "id": "RULE-001",
        "type": "obligation",
        "message": "Test directive",
        "evaluator_type": "regex",
        "evaluator_config": {"pattern": "^test$"},
        "status": "draft",
        "created_at": "2026-01-01T00:00:00Z",
    }
    payload.update(overrides)
    return payload


def make_active_directive_payload(**overrides: Any) -> dict[str, Any]:
    """Return a minimal valid ACTIVE directive dictionary."""
    payload = make_directive_payload(status="active")
    payload["metadata"] = {
        "audit": {"authored_by": "alice"}
    }
    payload.update(overrides)
    return payload


def make_directive(**overrides: Any) -> Directive:
    """Construct a minimal valid Directive instance."""
    return Directive.model_validate(make_directive_payload(**overrides))


def make_active_directive(**overrides: Any) -> Directive:
    """Construct a minimal valid ACTIVE Directive instance."""
    return Directive.model_validate(make_active_directive_payload(**overrides))


# ---------------------------------------------------------------------------
# Minimal valid graph payload
# ---------------------------------------------------------------------------

def make_graph_payload(**overrides: Any) -> dict[str, Any]:
    """Return a minimal valid DirectiveGraph dict (rules[] format)."""
    payload: dict[str, Any] = {
        "version": "1.0.0",
        "policy_contract_version": "1.0.0",
        "policy_contract_id": "universal-policy-doctrine",
        "rules": [make_directive_payload()],
    }
    payload.update(overrides)
    return payload


def make_graph(**overrides: Any) -> DirectiveGraph:
    """Construct a minimal valid DirectiveGraph instance."""
    return DirectiveGraph.model_validate(make_graph_payload(**overrides))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_directive() -> Directive:
    """Return a minimal valid draft Directive."""
    return make_directive()


@pytest.fixture
def minimal_active_directive() -> Directive:
    """Return a minimal valid active Directive with authored_by."""
    return make_active_directive()


@pytest.fixture
def minimal_graph() -> DirectiveGraph:
    """Return a minimal valid DirectiveGraph with one draft directive."""
    return make_graph()
