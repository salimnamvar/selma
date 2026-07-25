from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scripts.lint.core.violation import Violation

INVALID_RESULT = None


class Rule(ABC):
    @property
    @abstractmethod
    def code(self) -> str:
        """Short rule identifier, e.g. 'SC001'."""

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line human description."""
