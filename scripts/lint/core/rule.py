from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class Rule(ABC):
    @property
    @abstractmethod
    def code(self) -> str:
        """Short rule identifier, e.g. 'SC001'."""

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line human description."""
