"""Abstract parser port for Selma."""

from abc import ABC
from abc import abstractmethod
from pathlib import Path

from selma.core.entities.facts import FactDocument

class AbstractParser(ABC):
    """Abstract interface for language parsers."""

    @abstractmethod
    def extract(self, path: Path, requested_layers: list[str]) -> FactDocument:
        """Extract facts from a source file.

        Args:
            path: Path to the source file.
            requested_layers: List of fact layers to extract.

        Returns:
            FactDocument containing the extracted facts.
        """
        ...
