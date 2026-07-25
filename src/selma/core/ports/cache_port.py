"""Abstract cache port for Selma."""

from abc import ABC
from abc import abstractmethod

from selma.core.entities.facts import FactDocument

class AbstractCache(ABC):
    """Abstract interface for caching parsed facts."""

    @abstractmethod
    def get(self, file_hash: str) -> FactDocument | None:
        """Retrieve cached facts by file hash.

        Args:
            file_hash: SHA-256 hash of the source file.

        Returns:
            Cached FactDocument or None if not found.
        """
        ...

    @abstractmethod
    def put(self, file_hash: str, document: FactDocument) -> None:
        """Store facts in cache.

        Args:
            file_hash: SHA-256 hash of the source file.
            document: FactDocument to cache.
        """
        ...
