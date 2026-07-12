"""Tests for the DirectiveGraph aggregate root.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.1
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.directive_graph.directive_graph import DirectiveGraph
from tests.domain.directive_graph.conftest import make_directive_payload, make_graph_payload


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveGraphConstruction:
    def test_minimal_graph(self) -> None:
        g = DirectiveGraph.model_validate(make_graph_payload())
        assert len(g.directives) == 1

    def test_rules_alias_accepted(self) -> None:
        """JSON schema uses 'rules', domain uses 'directives'."""
        raw = make_graph_payload()
        assert "rules" in raw
        g = DirectiveGraph.model_validate(raw)
        assert len(g.directives) == 1

    def test_policy_contract_id_const(self) -> None:
        g = DirectiveGraph.model_validate(make_graph_payload())
        assert g.policy_contract_id == "universal-policy-doctrine"

    def test_rejects_invalid_policy_contract_id(self) -> None:
        with pytest.raises(ValidationError):
            DirectiveGraph.model_validate(
                make_graph_payload(policy_contract_id="wrong-policy")
            )

    def test_empty_rules_raises(self) -> None:
        with pytest.raises(ValidationError):
            DirectiveGraph.model_validate(make_graph_payload(rules=[]))

    def test_multiple_directives(self) -> None:
        g = DirectiveGraph.model_validate(
            make_graph_payload(
                rules=[
                    make_directive_payload(lineage_id="RULE-001", id="RULE-001"),
                    make_directive_payload(lineage_id="RULE-002", id="RULE-002"),
                ]
            )
        )
        assert len(g.directives) == 2


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveGraphAccessors:
    def test_get_by_id_found(self) -> None:
        g = DirectiveGraph.model_validate(make_graph_payload())
        d = g.get_by_id("RULE-001")
        assert d is not None
        assert d.id == "RULE-001"

    def test_get_by_id_not_found(self) -> None:
        g = DirectiveGraph.model_validate(make_graph_payload())
        assert g.get_by_id("UNKNOWN-999") is None

    def test_get_by_lineage_id(self) -> None:
        g = DirectiveGraph.model_validate(make_graph_payload())
        results = g.get_by_lineage_id("RULE-001")
        assert len(results) == 1

    def test_execution_ids(self) -> None:
        g = DirectiveGraph.model_validate(
            make_graph_payload(
                rules=[
                    make_directive_payload(lineage_id="RULE-001", id="RULE-001"),
                    make_directive_payload(lineage_id="RULE-002", id="RULE-002"),
                ]
            )
        )
        assert g.execution_ids() == frozenset({"RULE-001", "RULE-002"})

    def test_lineage_ids(self) -> None:
        g = DirectiveGraph.model_validate(make_graph_payload())
        assert "RULE-001" in g.lineage_ids()
