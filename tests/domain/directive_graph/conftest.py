"""Shared fixtures for Directive Graph tests.

Provides minimal valid directive and graph factories used across all
directive_graph test modules.

Wire-format payloads go through ``DirectiveGraphMapper`` (ACL) so domain
tests never depend on schema shape-normalisation living inside domain types.
"""

from __future__ import annotations

from typing import Any

import pytest

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph
from infrastructure.mappers.directive_graph_mapper import DirectiveGraphMapper

_mapper = DirectiveGraphMapper()

# ---------------------------------------------------------------------------
# Minimal valid directive payload (JSON schema / wire format)
# ---------------------------------------------------------------------------


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
    payload["metadata"] = {"audit": {"authored_by": "alice"}}
    payload.update(overrides)
    return payload


def make_directive(**overrides: Any) -> Directive:
    """Construct a minimal valid Directive instance via the ACL mapper."""
    return _mapper.directive_to_domain(make_directive_payload(**overrides))


def make_active_directive(**overrides: Any) -> Directive:
    """Construct a minimal valid ACTIVE Directive instance via the ACL mapper."""
    return _mapper.directive_to_domain(make_active_directive_payload(**overrides))


# ---------------------------------------------------------------------------
# Minimal valid graph payload
# ---------------------------------------------------------------------------


def make_graph_payload(**overrides: Any) -> dict[str, Any]:
    """Return a minimal valid DirectiveGraph dict (rules[] wire format)."""
    payload: dict[str, Any] = {
        "version": "1.0.0",
        "policy_contract_version": "1.0.0",
        "policy_contract_id": "universal-policy-doctrine",
        "rules": [make_directive_payload()],
    }
    payload.update(overrides)
    return payload


def make_graph(**overrides: Any) -> DirectiveGraph:
    """Construct a minimal valid DirectiveGraph instance via the ACL mapper."""
    return _mapper.to_domain(make_graph_payload(**overrides))


def make_domain_directive_payload(**overrides: Any) -> dict[str, Any]:
    """Return a domain-shaped directive dict (flat evaluator_config)."""
    payload: dict[str, Any] = {
        "lineage_id": "RULE-001",
        "id": "RULE-001",
        "type": "obligation",
        "message": "Test directive",
        "evaluator_config": {"evaluator_type": "regex", "pattern": "^test$"},
        "status": "draft",
        "created_at": "2026-01-01T00:00:00Z",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mapper() -> DirectiveGraphMapper:
    """Return a DirectiveGraphMapper instance."""
    return DirectiveGraphMapper()


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
