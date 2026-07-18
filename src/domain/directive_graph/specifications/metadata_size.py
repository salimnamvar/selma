"""Metadata byte-size specification.

Enforces ``max_metadata_bytes_per_rule: 16384`` from SPECIFICATION.md §2.9
(x-complexity-limits).

Size is computed from a domain-defined canonical JSON encoding (sorted keys,
UTF-8, no whitespace) so the check does not depend on a particular
serializer's default formatting beyond those rules.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from domain.directive_graph.directive_graph import DirectiveGraph

MAX_METADATA_BYTES_PER_RULE: int = 16_384


def _canonical_metadata_bytes(a_metadata_dict: dict[str, Any]) -> int:
    """Return UTF-8 byte length of canonical JSON for metadata."""
    encoded = json.dumps(a_metadata_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return len(encoded.encode("utf-8"))


class MetadataSizeSpec:
    """Each directive's metadata must not exceed 16 384 UTF-8 canonical bytes."""

    def is_satisfied_by(self, a_object: DirectiveGraph) -> bool:
        """Return True iff all directives comply with the metadata size limit."""
        return len(self.violations(a_object)) == 0

    def violations(self, a_object: DirectiveGraph) -> list[str]:
        """Return violation messages for directives whose metadata exceeds the limit."""
        messages: list[str] = []
        for d in a_object.directives:
            if d.metadata is None:
                continue
            # mode='json' yields JSON-serialisable primitives
            meta_dict = d.metadata.model_dump(mode="json")
            byte_size = _canonical_metadata_bytes(meta_dict)
            if byte_size > MAX_METADATA_BYTES_PER_RULE:
                messages.append(
                    f"Directive {d.id!r}: metadata serialised size "
                    f"{byte_size} bytes exceeds max {MAX_METADATA_BYTES_PER_RULE}"
                )
        return messages
