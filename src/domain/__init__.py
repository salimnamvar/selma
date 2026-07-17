"""Selma domain layer.

Bounded contexts:
- ``domain.authorization`` — capability matrix + SoD (§3.2)
- ``domain.directive_graph`` — executable Directive Graph (rule_schema projection)
- ``domain.finding`` — Finding FSM (SPEC §3.1 / state-machine catalog)
- ``domain.inspection`` — inspection pipeline + finding birth
- ``domain.policy_doctrine`` — governance doctrine (policy_doctrine.yaml projection)
- ``domain.shared`` — cross-context kernel types (domain events)
"""

from __future__ import annotations

from domain import authorization, directive_graph, finding, inspection, policy_doctrine, shared

__all__ = [
    "authorization",
    "directive_graph",
    "finding",
    "inspection",
    "policy_doctrine",
    "shared",
]

