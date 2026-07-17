"""Anti-corruption layer: rule_schema.json wire format ↔ domain model.

Translates structural contract shapes into domain-shaped objects:

- ``rules`` → ``directives``
- top-level ``evaluator_type`` + nested ``evaluator_config`` → flat evaluator
- nested sub-evaluator ``{evaluator_type, evaluator_config}`` → flat form
- metadata unknown keys → ``extensions``

Domain models never perform these translations.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph

_DIRECTIVE_METADATA_KNOWN_KEYS: frozenset[str] = frozenset({"audit", "migration", "extensions"})
_DATASET_METADATA_KNOWN_KEYS: frozenset[str] = frozenset(
    {"audit", "vendor", "author", "migration", "domain", "jurisdiction", "project", "extensions"}
)


class DirectiveGraphMapper:
    """Maps between rule_schema.json documents and ``DirectiveGraph``."""

    def to_domain(self, wire: dict[str, Any]) -> DirectiveGraph:
        """Translate a wire-format rule dataset dict into a domain aggregate.

        Args:
            wire: JSON-compatible dict matching rule_schema.json root.

        Returns:
            Validated ``DirectiveGraph``.
        """
        data = deepcopy(wire)
        domain_shaped = self._graph_wire_to_domain(data)
        return DirectiveGraph.model_validate(domain_shaped)

    def to_wire(self, graph: DirectiveGraph) -> dict[str, Any]:
        """Translate a domain aggregate into rule_schema.json wire format.

        Args:
            graph: Domain aggregate.

        Returns:
            JSON-compatible dict with ``rules`` and split evaluator fields.
        """
        dumped = graph.model_dump(mode="json")
        directives = dumped.pop("directives", [])
        rules = [self._directive_domain_to_wire(d) for d in directives]
        metadata = dumped.get("metadata")
        if isinstance(metadata, dict):
            dumped["metadata"] = self._metadata_domain_to_wire(metadata, _DATASET_METADATA_KNOWN_KEYS)
        dumped["rules"] = rules
        return dumped

    def directive_to_domain(self, wire: dict[str, Any]) -> Directive:
        """Translate a single wire-format directive into a domain entity."""
        return Directive.model_validate(self._directive_wire_to_domain(deepcopy(wire)))

    # ------------------------------------------------------------------
    # Graph / directive → domain
    # ------------------------------------------------------------------

    def _graph_wire_to_domain(self, data: dict[str, Any]) -> dict[str, Any]:
        if "rules" in data and "directives" not in data:
            rules = data.pop("rules")
            data["directives"] = [self._directive_wire_to_domain(r) for r in rules]
        elif "directives" in data:
            data["directives"] = [self._directive_wire_to_domain(r) for r in data["directives"]]
        if isinstance(data.get("metadata"), dict):
            data["metadata"] = self._fold_metadata_extensions(
                data["metadata"], _DATASET_METADATA_KNOWN_KEYS
            )
        return data

    def _directive_wire_to_domain(self, data: dict[str, Any]) -> dict[str, Any]:
        data = self._merge_evaluator_type_into_config(data)
        if "evaluator_config" in data:
            data["evaluator_config"] = self._flatten_evaluator(data["evaluator_config"])
        if isinstance(data.get("metadata"), dict):
            data["metadata"] = self._fold_metadata_extensions(
                data["metadata"], _DIRECTIVE_METADATA_KNOWN_KEYS
            )
        return data

    def _merge_evaluator_type_into_config(self, data: dict[str, Any]) -> dict[str, Any]:
        """Merge top-level evaluator_type into evaluator_config (wire → domain)."""
        ev_type = data.get("evaluator_type")
        ev_config = data.get("evaluator_config")
        if ev_type is not None and isinstance(ev_config, dict) and "evaluator_type" not in ev_config:
            data = dict(data)
            data["evaluator_config"] = self._flatten_evaluator({"evaluator_type": ev_type, **ev_config})
            del data["evaluator_type"]
        elif isinstance(ev_config, dict):
            data = dict(data)
            data["evaluator_config"] = self._flatten_evaluator(ev_config)
            data.pop("evaluator_type", None)
        return data

    def _flatten_evaluator(self, data: Any) -> Any:
        """Flatten nested ``{evaluator_type, evaluator_config}`` recursively."""
        if not isinstance(data, dict):
            return data
        result = dict(data)
        ev_type = result.get("evaluator_type")
        ev_config = result.get("evaluator_config")
        if ev_type is not None and isinstance(ev_config, dict) and "evaluator_type" not in ev_config:
            result = {"evaluator_type": ev_type, **ev_config}
        # Recurse into composite children
        if "sub_evaluators" in result and isinstance(result["sub_evaluators"], list):
            result["sub_evaluators"] = [self._flatten_evaluator(child) for child in result["sub_evaluators"]]
        return result

    def _fold_metadata_extensions(
        self,
        data: dict[str, Any],
        known_keys: frozenset[str],
    ) -> dict[str, Any]:
        """Move unrecognised top-level metadata keys into ``extensions``."""
        unknowns = {k: v for k, v in data.items() if k not in known_keys}
        if not unknowns:
            return data
        data = dict(data)
        existing = data.get("extensions") or {}
        data["extensions"] = {**unknowns, **(existing if isinstance(existing, dict) else {})}
        for k in unknowns:
            del data[k]
        return data

    # ------------------------------------------------------------------
    # Domain → wire
    # ------------------------------------------------------------------

    def _directive_domain_to_wire(self, data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data)
        ev = data.get("evaluator_config")
        if isinstance(ev, dict) and "evaluator_type" in ev:
            ev_type = ev["evaluator_type"]
            config = {k: v for k, v in ev.items() if k != "evaluator_type"}
            if "sub_evaluators" in config and isinstance(config["sub_evaluators"], list):
                config["sub_evaluators"] = [
                    self._nest_evaluator(child) for child in config["sub_evaluators"]
                ]
            data["evaluator_type"] = ev_type
            data["evaluator_config"] = config
        if isinstance(data.get("metadata"), dict):
            data["metadata"] = self._metadata_domain_to_wire(
                data["metadata"], _DIRECTIVE_METADATA_KNOWN_KEYS
            )
        return data

    def _nest_evaluator(self, data: Any) -> Any:
        """Convert flat domain evaluator to nested wire form for sub-evaluators."""
        if not isinstance(data, dict) or "evaluator_type" not in data:
            return data
        ev_type = data["evaluator_type"]
        config = {k: v for k, v in data.items() if k != "evaluator_type"}
        if "sub_evaluators" in config and isinstance(config["sub_evaluators"], list):
            config["sub_evaluators"] = [self._nest_evaluator(c) for c in config["sub_evaluators"]]
        return {"evaluator_type": ev_type, "evaluator_config": config}

    def _metadata_domain_to_wire(
        self,
        data: dict[str, Any],
        known_keys: frozenset[str],
    ) -> dict[str, Any]:
        """Expand ``extensions`` back to top-level keys for wire format."""
        data = dict(data)
        extensions = data.pop("extensions", None) or {}
        for k, v in extensions.items():
            if k not in data:
                data[k] = v
        # Drop empty extensions if nothing else — wire allows additionalProperties
        return data
