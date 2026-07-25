"""Finding reporter port — abstract interface for outputting findings.

Domain depends on this interface, not on implementation.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from selma.domain.entities.finding import Finding
from selma.domain.value_objects.result import Result


class FindingReporter(ABC):
    """Port: format and output findings.

    Infrastructure implements this interface (JSON, GCC, guidance, etc.).
    """

    @abstractmethod
    def report(self, a_findings: tuple[Finding, ...]) -> Result[str]:
        """Format findings for output.

        Preconditions:
            - a_findings is a tuple of Finding objects.

        Postconditions:
            Returns Ok with formatted string, or Failure on error.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on formatting error.
        """
        ...
