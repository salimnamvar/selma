"""Source code parser port — abstract interface for parsing source files.

Domain depends on this interface, not on implementation.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result


class SourceCodeParser(ABC):
    """Port: parse source code into AST.

    Infrastructure implements this interface.
    """

    @abstractmethod
    def parse(self, a_path: FilePath) -> Result[Any]:
        """Parse a source file into an AST.

        Preconditions:
            - a_path points to an existing file.

        Postconditions:
            Returns Ok with parsed AST, or Failure with error message.

        Side Effects: Reads file from disk.
        Resource: File handle.
        Failure: Returns Failure on parse error.
        """
        ...

    @abstractmethod
    def parse_source(self, a_source: str, a_filename: str = "<string>") -> Result[Any]:
        """Parse source code string into an AST.

        Preconditions:
            - a_source is valid Python source code.

        Postconditions:
            Returns Ok with parsed AST, or Failure with error message.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on parse error.
        """
        ...
