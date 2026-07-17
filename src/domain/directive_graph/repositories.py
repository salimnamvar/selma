"""Abstract persistence port for DirectiveGraph.

Infrastructure implementations live outside the domain package.
The domain only defines the abstract interface and an opaque identity type.

Reference: Clean Architecture / Hexagonal ports
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import NewType

from domain.directive_graph.directive_graph import DirectiveGraph

# Opaque repository identity — not a filesystem path. Infrastructure maps
# this token to storage (file, DB row, object key, etc.).
DirectiveGraphRef = NewType("DirectiveGraphRef", str)


class DirectiveGraphRepository(ABC):
    """Abstract persistence port for loading and saving directive graphs."""

    @abstractmethod
    def get(self, ref: DirectiveGraphRef) -> DirectiveGraph:
        """Load a ``DirectiveGraph`` by opaque repository reference.

        Args:
            ref: Infrastructure-defined identity token.

        Returns:
            The loaded and structurally validated graph.

        Raises:
            KeyError: If no graph exists for ``ref`` (implementation-defined).
        """

    @abstractmethod
    def save(self, graph: DirectiveGraph, ref: DirectiveGraphRef) -> None:
        """Persist a ``DirectiveGraph`` under the given reference.

        Args:
            graph: The graph to persist.
            ref: Infrastructure-defined identity token.
        """

    @abstractmethod
    def exists(self, ref: DirectiveGraphRef) -> bool:
        """Return True iff a graph is stored under ``ref``."""
