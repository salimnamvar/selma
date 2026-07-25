"""Rule repository port — abstract interface for loading rules.

Domain depends on this interface, not on implementation.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from selma.domain.entities.rule import RuleDefinition
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId


class RuleRepository(ABC):
    """Port: access and manage lint rules.

    Infrastructure implements this interface (e.g., from JSON files).
    """

    @abstractmethod
    def find_all(self) -> Result[tuple[RuleDefinition, ...]]:
        """Retrieve all active rules.

        Preconditions: None.
        Postconditions: Returns Ok with tuple of all active rules.
        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on load error.
        """
        ...

    @abstractmethod
    def find_by_id(self, a_id: RuleId) -> Result[RuleDefinition]:
        """Retrieve a rule by ID.

        Preconditions: None.
        Postconditions: Returns Ok with rule, or Failure if not found.
        Side Effects: None.
        Resource: None.
        Failure: Returns Failure if rule not found.
        """
        ...

    @abstractmethod
    def find_by_codes(self, a_codes: tuple[str, ...]) -> Result[tuple[RuleDefinition, ...]]:
        """Retrieve rules by code list.

        Preconditions: None.
        Postconditions: Returns Ok with matching rules.
        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on load error.
        """
        ...
