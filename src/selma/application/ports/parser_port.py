"""Source parser port — parse source files into ASTs."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
import ast

from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result


class SourceParser(ABC):
    """Port: parse source code into an AST for inspection."""

    @abstractmethod
    async def parse(self, a_path: FilePath) -> Result[ast.AST]:
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
    async def parse_source(
        self, a_source: str, a_filename: str = "<string>"
    ) -> Result[ast.AST]:
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
