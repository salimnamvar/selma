"""In-memory cache implementation."""

from selma.core.entities.facts import FactDocument
from selma.core.ports.cache_port import AbstractCache

class InMemoryCache(AbstractCache):
    """Simple in-memory cache for parsed facts."""

    def __init__(self) -> None:
        """Initialize the cache."""
        self._cache: dict[str, FactDocument] = {}

    def get(self, file_hash: str) -> FactDocument | None:
        """Retrieve cached facts by file hash.

        Args:
            file_hash: SHA-256 hash of the source file.

        Returns:
            Cached FactDocument or None if not found.
        """
        return self._cache.get(file_hash)

    def put(self, file_hash: str, document: FactDocument) -> None:
        """Store facts in cache.

        Args:
            file_hash: SHA-256 hash of the source file.
            document: FactDocument to cache.
        """
        self._cache[file_hash] = document
