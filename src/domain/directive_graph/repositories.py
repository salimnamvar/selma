"""Abstract persistence port for DirectiveGraph.

Infrastructure implementations live outside the domain package.
The domain only defines the abstract interface and an opaque identity type.

Reference: Clean Architecture / Hexagonal ports
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import NewType

if TYPE_CHECKING:
    from domain.directive_graph.directive_graph import DirectiveGraph

# Opaque repository identity — not a filesystem path. Infrastructure maps
# this token to storage (file, DB row, object key, etc.).
DirectiveGraphRef = NewType("DirectiveGraphRef", str)


class DirectiveGraphRepository(ABC):
    """Abstract persistence port for loading and saving directive graphs."""

    @abstractmethod
    def get(self, a_ref: DirectiveGraphRef) -> DirectiveGraph:
        """Load a ``DirectiveGraph`` by opaque repository reference.

        Args:
            a_ref: Infrastructure-defined identity token.

        Returns:
            The loaded and structurally validated graph.

        Raises:
            KeyError: If no graph exists for ``a_ref`` (implementation-defined).
        """

    @abstractmethod
    def save(self, a_graph: DirectiveGraph, a_ref: DirectiveGraphRef) -> None:
        """Persist a ``DirectiveGraph`` under the given reference.

        Args:
            a_graph: The graph to persist.
            a_ref: Infrastructure-defined identity token.
        """

    @abstractmethod
    def exists(self, a_ref: DirectiveGraphRef) -> bool:
        """Return True iff a graph is stored under ``a_ref``."""
