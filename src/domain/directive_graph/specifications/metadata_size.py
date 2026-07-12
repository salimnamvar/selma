"""Metadata byte-size specification.

Enforces ``max_metadata_bytes_per_rule: 16384`` from SPECIFICATION.md §2.9
(x-complexity-limits).

Size is computed from the UTF-8 JSON serialization of the directive's
``metadata`` field via Pydantic's ``model_dump_json()``.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.8
"""

from __future__ import annotations

from domain.directive_graph.directive_graph import DirectiveGraph

MAX_METADATA_BYTES_PER_RULE: int = 16_384


class MetadataSizeSpec:
    """Each directive's metadata must not exceed 16 384 UTF-8 bytes when serialised."""

    def is_satisfied_by(self, graph: DirectiveGraph) -> bool:
        """Return True iff all directives comply with the metadata size limit.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            bool: True when satisfied.
        """
        return len(self.violations(graph)) == 0

    def violations(self, graph: DirectiveGraph) -> list[str]:
        """Return violation messages for directives whose metadata exceeds the limit.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            list[str]: Human-readable violation descriptions.
        """
        messages: list[str] = []
        for d in graph.directives:
            if d.metadata is None:
                continue
            byte_size = len(d.metadata.model_dump_json().encode("utf-8"))
            if byte_size > MAX_METADATA_BYTES_PER_RULE:
                messages.append(
                    f"Directive {d.id!r}: metadata serialised size "
                    f"{byte_size} bytes exceeds max {MAX_METADATA_BYTES_PER_RULE}"
                )
        return messages
