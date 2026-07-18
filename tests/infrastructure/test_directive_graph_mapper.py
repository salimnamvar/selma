"""Tests for the DirectiveGraph anti-corruption layer mapper."""

from __future__ import annotations

import pytest
from tests.domain.directive_graph.conftest import make_directive_payload
from tests.domain.directive_graph.conftest import make_graph_payload

from domain.directive_graph.evaluators import CompositeEvaluator
from domain.directive_graph.evaluators import RegexEvaluator
from infrastructure.mappers.directive_graph_mapper import DirectiveGraphMapper


@pytest.fixture
def mapper() -> DirectiveGraphMapper:
    return DirectiveGraphMapper()


@pytest.mark.unit
class TestDirectiveGraphMapper:
    def test_rules_to_directives(self, mapper: DirectiveGraphMapper) -> None:
        wire = make_graph_payload()
        graph = mapper.to_domain(wire)
        assert len(graph.directives) == 1
        assert graph.directives[0].id == "RULE-001"

    def test_evaluator_type_merged(self, mapper: DirectiveGraphMapper) -> None:
        d = mapper.directive_to_domain(make_directive_payload())
        assert isinstance(d.evaluator_config, RegexEvaluator)
        assert d.evaluator_config.pattern == "^test$"

    def test_nested_composite_flattened(self, mapper: DirectiveGraphMapper) -> None:
        wire = make_directive_payload(
            evaluator_type="composite",
            evaluator_config={
                "logic": "and",
                "sub_evaluators": [
                    {"evaluator_type": "regex", "evaluator_config": {"pattern": "^a$"}},
                    {"evaluator_type": "regex", "evaluator_config": {"pattern": "^b$"}},
                ],
            },
        )
        d = mapper.directive_to_domain(wire)
        assert isinstance(d.evaluator_config, CompositeEvaluator)
        assert len(d.evaluator_config.sub_evaluators) == 2

    def test_metadata_extensions_folded(self, mapper: DirectiveGraphMapper) -> None:
        wire = make_directive_payload(
            metadata={
                "audit": {"authored_by": "alice"},
                "custom_tag": "x",
            }
        )
        d = mapper.directive_to_domain(wire)
        assert d.metadata is not None
        assert d.metadata.extensions.get("custom_tag") == "x"

    def test_round_trip_preserves_identity(self, mapper: DirectiveGraphMapper) -> None:
        wire = make_graph_payload(
            rules=[
                make_directive_payload(lineage_id="RULE-001", id="RULE-001"),
                make_directive_payload(lineage_id="RULE-002", id="RULE-002"),
            ]
        )
        graph = mapper.to_domain(wire)
        out = mapper.to_wire(graph)
        assert "rules" in out
        assert len(out["rules"]) == 2
        assert out["rules"][0]["evaluator_type"] == "regex"
        assert "evaluator_type" not in out["rules"][0]["evaluator_config"]
