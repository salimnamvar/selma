"""In-memory cache implementation."""

from __future__ import annotations

from selma.application.ports.cache_port import FactCache
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.source_hash import SourceHash


class InMemoryCache:
    """Infrastructure: In-memory cache for parsed facts."""

    def __init__(self) -> None:
        self._cache: dict[str, object] = {}

    def get(self, a_key: SourceHash) -> Result[object | None]:
        """Retrieve cached item by key."""
        return Result.success(self._cache.get(a_key.value))

    def put(self, a_key: SourceHash, a_value: object) -> Result[None]:
        """Store item in cache."""
        self._cache[a_key.value] = a_value
        return Result.success(None)
