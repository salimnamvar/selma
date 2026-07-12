"""Abstract persistence port for DirectiveGraph.

Infrastructure implementations live in ``src/infrastructure/repository.py``.
The domain only defines the abstract interface.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.9
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from domain.directive_graph.directive_graph import DirectiveGraph


class DirectiveGraphRepository(ABC):
    """Abstract persistence port for loading and saving directive graphs.

    Attributes:
        None
    """

    @abstractmethod
    def load(self, source: str) -> DirectiveGraph:
        """Load a ``DirectiveGraph`` from the given source.

        Args:
            source (str): Source path or identifier (format is
                implementation-defined).

        Returns:
            DirectiveGraph: The loaded and structurally validated graph.
        """

    @abstractmethod
    def save(self, graph: DirectiveGraph, destination: str) -> None:
        """Persist a ``DirectiveGraph`` to the given destination.

        Args:
            graph (DirectiveGraph): The graph to persist.
            destination (str): Destination path or identifier.
        """
