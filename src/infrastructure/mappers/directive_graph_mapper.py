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
from typing import cast

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph

_DIRECTIVE_METADATA_KNOWN_KEYS: frozenset[str] = frozenset({"audit", "migration", "extensions"})
_DATASET_METADATA_KNOWN_KEYS: frozenset[str] = frozenset(
    {"audit", "vendor", "author", "migration", "domain", "jurisdiction", "project", "extensions"}
)


class DirectiveGraphMapper:
    """Maps between rule_schema.json documents and ``DirectiveGraph``."""

    def to_domain(self, a_wire: dict[str, Any]) -> DirectiveGraph:
        """Translate a wire-format rule dataset dict into a domain aggregate.

        Args:
            a_wire: JSON-compatible dict matching rule_schema.json root.

        Returns:
            Validated ``DirectiveGraph``.
        """
        data = deepcopy(a_wire)
        domain_shaped = self._graph_wire_to_domain(data)
        return DirectiveGraph.model_validate(domain_shaped)

    def to_wire(self, a_graph: DirectiveGraph) -> dict[str, Any]:
        """Translate a domain aggregate into rule_schema.json wire format.

        Args:
            a_graph: Domain aggregate.

        Returns:
            JSON-compatible dict with ``rules`` and split evaluator fields.
        """
        dumped = a_graph.model_dump(mode="json")
        directives = dumped.pop("directives", [])
        rules = [self._directive_domain_to_wire(d) for d in directives]
        metadata: dict[str, Any] | None = dumped.get("metadata")
        if isinstance(metadata, dict):
            dumped["metadata"] = self._metadata_domain_to_wire(metadata)
        dumped["rules"] = rules
        return dumped

    def directive_to_domain(self, a_wire: dict[str, Any]) -> Directive:
        """Translate a single wire-format directive into a domain entity."""
        return Directive.model_validate(self._directive_wire_to_domain(deepcopy(a_wire)))

    # ------------------------------------------------------------------
    # Graph / directive → domain
    # ------------------------------------------------------------------

    def _graph_wire_to_domain(self, a_data: dict[str, Any]) -> dict[str, Any]:
        if "rules" in a_data and "directives" not in a_data:
            rules = a_data.pop("rules")
            a_data["directives"] = [self._directive_wire_to_domain(r) for r in rules]
        elif "directives" in a_data:
            a_data["directives"] = [self._directive_wire_to_domain(r) for r in a_data["directives"]]
        if isinstance(a_data.get("metadata"), dict):
            a_data["metadata"] = self._fold_metadata_extensions(a_data["metadata"], _DATASET_METADATA_KNOWN_KEYS)
        return a_data

    def _directive_wire_to_domain(self, a_data: dict[str, Any]) -> dict[str, Any]:
        a_data = self._merge_evaluator_type_into_config(a_data)
        if "evaluator_config" in a_data:
            a_data["evaluator_config"] = self._flatten_evaluator(a_data["evaluator_config"])
        if isinstance(a_data.get("metadata"), dict):
            a_data["metadata"] = self._fold_metadata_extensions(a_data["metadata"], _DIRECTIVE_METADATA_KNOWN_KEYS)
        return a_data

    def _merge_evaluator_type_into_config(self, a_data: dict[str, Any]) -> dict[str, Any]:
        """Merge top-level evaluator_type into evaluator_config (wire → domain)."""
        ev_type = a_data.get("evaluator_type")
        ev_config = a_data.get("evaluator_config")
        if ev_type is not None and isinstance(ev_config, dict) and "evaluator_type" not in ev_config:
            a_data = dict(a_data)
            a_data["evaluator_config"] = self._flatten_evaluator({"evaluator_type": ev_type, **ev_config})
            del a_data["evaluator_type"]
        elif isinstance(ev_config, dict):
            a_data = dict(a_data)
            a_data["evaluator_config"] = self._flatten_evaluator(ev_config)
            a_data.pop("evaluator_type", None)
        return a_data

    def _flatten_evaluator(self, a_data: Any) -> Any:
        """Flatten nested ``{evaluator_type, evaluator_config}`` recursively."""
        if isinstance(a_data, dict):
            result: dict[str, Any] = dict(a_data)  # type: ignore[arg-type]
            ev_type: Any = result.get("evaluator_type")
            ev_config: dict[str, Any] | None = result.get("evaluator_config")
            if ev_type is not None and isinstance(ev_config, dict) and "evaluator_type" not in ev_config:
                result = {"evaluator_type": ev_type, **ev_config}
            # Recurse into composite children
            if "sub_evaluators" in result and isinstance(result["sub_evaluators"], list):
                sub_evals = cast("list[Any]", result["sub_evaluators"])
                result["sub_evaluators"] = [self._flatten_evaluator(child) for child in sub_evals]
        else:
            result = a_data  # type: ignore[assignment]
        return result

    def _fold_metadata_extensions(
        self,
        a_data: dict[str, Any],
        a_known_keys: frozenset[str],
    ) -> dict[str, Any]:
        """Move unrecognised top-level metadata keys into ``extensions``."""
        unknowns = {k: v for k, v in a_data.items() if k not in a_known_keys}
        if unknowns:
            a_data = dict(a_data)
            existing: dict[str, Any] = a_data.get("extensions") or {}
            a_data["extensions"] = {**unknowns, **existing}
            for k in unknowns:
                del a_data[k]
        return a_data

    # ------------------------------------------------------------------
    # Domain → wire
    # ------------------------------------------------------------------

    def _directive_domain_to_wire(self, a_data: dict[str, Any]) -> dict[str, Any]:
        a_data = dict(a_data)
        ev: dict[str, Any] | None = a_data.get("evaluator_config")  # type: ignore[assignment]
        if isinstance(ev, dict) and "evaluator_type" in ev:
            ev_type: str = ev["evaluator_type"]
            config: dict[str, Any] = {k: v for k, v in ev.items() if k != "evaluator_type"}
            if "sub_evaluators" in config and isinstance(config["sub_evaluators"], list):
                sub_evals = cast("list[Any]", config["sub_evaluators"])
                config["sub_evaluators"] = [self._nest_evaluator(child) for child in sub_evals]
            a_data["evaluator_type"] = ev_type
            a_data["evaluator_config"] = config
        if isinstance(a_data.get("metadata"), dict):
            a_data["metadata"] = self._metadata_domain_to_wire(a_data["metadata"])
        return a_data

    def _nest_evaluator(self, a_data: Any) -> Any:
        """Convert flat domain evaluator to nested wire form for sub-evaluators."""
        if isinstance(a_data, dict) and "evaluator_type" in a_data:
            typed: dict[str, Any] = a_data  # type: ignore[assignment]
            ev_type: Any = typed["evaluator_type"]
            config: dict[str, Any] = {k: v for k, v in typed.items() if k != "evaluator_type"}
            if "sub_evaluators" in config and isinstance(config["sub_evaluators"], list):
                sub_evals = cast("list[Any]", config["sub_evaluators"])
                config["sub_evaluators"] = [self._nest_evaluator(c) for c in sub_evals]
            result: dict[str, Any] = {"evaluator_type": ev_type, "evaluator_config": config}
        else:
            result = a_data  # type: ignore[assignment]
        return result

    def _metadata_domain_to_wire(
        self,
        a_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Expand ``extensions`` back to top-level keys for wire format."""
        a_data = dict(a_data)
        extensions: dict[str, Any] = a_data.pop("extensions", None) or {}
        for k, v in extensions.items():
            if k not in a_data:
                a_data[k] = v
        # Drop empty extensions if nothing else — wire allows additionalProperties
        return a_data
