"""Selma domain layer.

Bounded contexts:
- ``domain.directive_graph`` — executable Directive Graph (rule_schema projection)
- ``domain.policy_doctrine`` — governance doctrine (policy_doctrine.yaml projection)
- ``domain.shared`` — cross-context kernel types (domain events)
"""

from __future__ import annotations

from domain import directive_graph, policy_doctrine, shared

__all__ = ["directive_graph", "policy_doctrine", "shared"]
