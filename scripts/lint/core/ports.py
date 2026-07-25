"""Domain ports for filesystem access and AST parsing abstractions."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
import ast

from scripts.lint.core.result import Result


class FileLoaderPort(ABC):
    """Abstract port for reading file contents."""

    @abstractmethod
    def read_source(self, path: str) -> Result[str]:
        """Read source code from given file path.

        Precondition: path is a non-empty string file path.
        Postcondition: Returns Result.success with file text or Result.failure.
        Side effect: None (abstract).
        Resource: None.
        Failure: Abstract method.
        """
        b_continue = True
        result: Result[str] = Result.failure("abstract method")
        if b_continue:
            result = Result.failure("abstract method")
        return result


class ASTParserPort(ABC):
    """Abstract port for parsing source text into Python AST."""

    @abstractmethod
    def parse_ast(self, source: str, filename: str) -> Result[ast.AST]:
        """Parse source text into an AST module node.

        Precondition: source is a string containing Python code.
        Postcondition: Returns Result.success with ast.AST or Result.failure.
        Side effect: None (abstract).
        Resource: None.
        Failure: Abstract method.
        """
        b_continue = True
        result: Result[ast.AST] = Result.failure("abstract method")
        if b_continue:
            result = Result.failure("abstract method")
        return result
