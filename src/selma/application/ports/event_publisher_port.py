"""Event publisher port — abstract interface for publishing domain events.

Domain depends on this interface, not on implementation.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from selma.domain.value_objects.result import Result


class EventPublisher(ABC):
    """Port: publish domain events.

    Infrastructure implements this interface.
    """

    @abstractmethod
    def publish(self, a_event: object) -> Result[None]:
        """Publish a domain event.

        Preconditions:
            - a_event is a valid domain event.

        Postconditions:
            Returns Ok(None) on success.

        Side Effects: May notify subscribers.
        Resource: None.
        Failure: Returns Failure on publish error.
        """
        ...
