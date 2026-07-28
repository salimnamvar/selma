"""Directive repository port — catalog of rule + policy pairs."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from selma.domain.aggregates.directive import Directive
from selma.domain.aggregates.directive import DirectiveCatalog
from selma.domain.entities.policy import DirectivePolicy
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId


class DirectiveRepository(ABC):
    """Port: load and query the directive catalog."""

    @abstractmethod
    async def list_catalog(self) -> Result[DirectiveCatalog]:
        """Load the full directive catalog.

        Preconditions: None.
        Postconditions: Ok with catalog (may be empty).
        Side Effects: May read files on first call.
        Resource: File I/O.
        Failure: Failure on load/validation error.
        """
        ...

    @abstractmethod
    async def list_active_rules(self) -> Result[tuple[Rule, ...]]:
        """List executable rules for inspection (policy excluded)."""
        ...

    @abstractmethod
    async def find_by_lineage_id(self, a_id: RuleId) -> Result[Directive]:
        """Find one directive by Machine ID / lineage_id."""
        ...

    @abstractmethod
    async def find_by_codes(
        self, a_codes: tuple[str, ...]
    ) -> Result[tuple[Directive, ...]]:
        """Find directives matching codes."""
        ...

    @abstractmethod
    async def get_policy(self, a_id: RuleId) -> Result[DirectivePolicy]:
        """Get reasoning policy for a Machine ID."""
        ...

    @abstractmethod
    async def get_rule(self, a_id: RuleId) -> Result[Rule]:
        """Get executable rule for a Machine ID."""
        ...
