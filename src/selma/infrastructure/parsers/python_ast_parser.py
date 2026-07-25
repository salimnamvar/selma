"""Python AST parser — infrastructure implementation of SourceCodeParser port."""

from __future__ import annotations

import ast
import logging

from selma.application.ports.parser_port import SourceCodeParser
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result

logger = logging.getLogger(__name__)


class PythonAstParser(SourceCodeParser):
    """Infrastructure: Python AST parser using stdlib ast module.

    Implements SourceCodeParser port.
    """

    def parse(self, a_path: FilePath) -> Result[ast.AST]:
        """Parse a Python source file into an AST.

        Preconditions:
            - a_path points to an existing Python file.

        Postconditions:
            Returns Ok with AST, or Failure with error message.

        Side Effects: Reads file from disk.
        Resource: File handle.
        Failure: Returns Failure on read or parse error.
        """
        b_continue = True
        result: Result[ast.AST] = Result.failure("unreachable")
        source = str(a_path)
        try:
            with open(source, encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=source)
            if b_continue:
                result = Result.success(tree)
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            if b_continue:
                logger.warning("Failed to parse %s: %s", a_path, exc)
                b_continue = False
                result = Result.failure(f"Parse error: {exc}")
        return result

    def parse_source(
        self, a_source: str, a_filename: str = "<string>"
    ) -> Result[ast.AST]:
        """Parse source code string into an AST.

        Preconditions:
            - a_source is valid Python source code.

        Postconditions:
            Returns Ok with AST, or Failure with error message.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on parse error.
        """
        b_continue = True
        result: Result[ast.AST] = Result.failure("unreachable")
        try:
            tree = ast.parse(a_source, filename=a_filename)
            if b_continue:
                result = Result.success(tree)
        except SyntaxError as exc:
            if b_continue:
                b_continue = False
                result = Result.failure(f"Syntax error: {exc}")
        return result
