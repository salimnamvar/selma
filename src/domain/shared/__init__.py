"""Shared kernel types used across bounded contexts.

``SemanticVersion`` is intentionally *not* shared: the directive-graph context
uses a string RootModel aligned with rule_schema.json, while policy-doctrine
uses a structured major/minor/patch model aligned with policy_doctrine.yaml.
"""

from __future__ import annotations

from domain.shared.events import DomainEvent

__all__ = ["DomainEvent"]
