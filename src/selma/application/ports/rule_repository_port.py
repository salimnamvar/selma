"""Rule repository port — executable rules for inspection.

Prefer DirectiveRepository for catalog and policy queries.
This port remains for inspection paths that need only Rule.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from selma.domain.entities.rule import Rule
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId


class RuleRepository(ABC):
    """Port: access executable rules for inspection."""

    @abstractmethod
    async def find_all(self) -> Result[tuple[Rule, ...]]:
        """Retrieve all active rules.

        Preconditions: None.
        Postconditions: Returns Ok with tuple of all active rules.
        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on load error.
        """
        ...

    @abstractmethod
    async def find_by_id(self, a_id: RuleId) -> Result[Rule]:
        """Retrieve a rule by ID.

        Preconditions: None.
        Postconditions: Returns Ok with rule, or Failure if not found.
        Side Effects: None.
        Resource: None.
        Failure: Returns Failure if rule not found.
        """
        ...

    @abstractmethod
    async def find_by_codes(self, a_codes: tuple[str, ...]) -> Result[tuple[Rule, ...]]:
        """Retrieve rules by code list.

        Preconditions: None.
        Postconditions: Returns Ok with matching rules.
        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on load error.
        """
        ...
