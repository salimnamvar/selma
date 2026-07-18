"""Tests for the DirectiveGraph aggregate root."""

from __future__ import annotations

from pydantic import ValidationError
import pytest
from tests.domain.directive_graph.conftest import make_directive_payload
from tests.domain.directive_graph.conftest import make_domain_directive_payload
from tests.domain.directive_graph.conftest import make_graph
from tests.domain.directive_graph.conftest import make_graph_payload

from domain.directive_graph.directive_graph import DirectiveGraph


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveGraphConstruction:
    def test_minimal_graph(self) -> None:
        g = make_graph()
        assert len(g.directives) == 1

    def test_rules_alias_via_mapper(self) -> None:
        """JSON schema uses 'rules'; mapper maps to domain 'directives'."""
        raw = make_graph_payload()
        assert "rules" in raw
        g = make_graph()
        assert len(g.directives) == 1

    def test_domain_shaped_construction(self) -> None:
        g = DirectiveGraph.model_validate(
            {
                "version": "1.0.0",
                "policy_contract_version": "1.0.0",
                "policy_contract_id": "universal-policy-doctrine",
                "directives": [make_domain_directive_payload()],
            }
        )
        assert len(g.directives) == 1

    def test_policy_contract_id_const(self) -> None:
        g = make_graph()
        assert g.policy_contract_id == "universal-policy-doctrine"

    def test_rejects_invalid_policy_contract_id(self) -> None:
        with pytest.raises(ValidationError):
            make_graph(policy_contract_id="wrong-policy")

    def test_empty_rules_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_graph(rules=[])

    def test_multiple_directives(self) -> None:
        g = make_graph(
            rules=[
                make_directive_payload(lineage_id="RULE-001", id="RULE-001"),
                make_directive_payload(lineage_id="RULE-002", id="RULE-002"),
            ]
        )
        assert len(g.directives) == 2

    def test_frozen(self) -> None:
        g = make_graph()
        with pytest.raises(Exception):
            g.version = "9.9.9"  # type: ignore[misc]


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveGraphAccessors:
    def test_get_by_id_found(self) -> None:
        g = make_graph()
        d = g.get_by_id("RULE-001")
        assert d is not None
        assert d.id == "RULE-001"

    def test_get_by_id_not_found(self) -> None:
        g = make_graph()
        assert g.get_by_id("UNKNOWN-999") is None

    def test_get_by_lineage_id(self) -> None:
        g = make_graph()
        results = g.get_by_lineage_id("RULE-001")
        assert len(results) == 1

    def test_get_by_lineage_id_shared_after_fork(self) -> None:
        g = make_graph(
            rules=[
                make_directive_payload(lineage_id="RULE-001", id="RULE-001"),
                make_directive_payload(lineage_id="RULE-001", id="RULE-001-A"),
            ]
        )
        results = g.get_by_lineage_id("RULE-001")
        assert len(results) == 2

    def test_execution_ids(self) -> None:
        g = make_graph(
            rules=[
                make_directive_payload(lineage_id="RULE-001", id="RULE-001"),
                make_directive_payload(lineage_id="RULE-002", id="RULE-002"),
            ]
        )
        assert g.execution_ids() == frozenset({"RULE-001", "RULE-002"})

    def test_lineage_ids(self) -> None:
        g = make_graph()
        assert "RULE-001" in g.lineage_ids()
