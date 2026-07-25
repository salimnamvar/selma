"""Concrete infrastructure adapters for file loading and AST parsing."""

from __future__ import annotations

import ast
from pathlib import Path

from scripts.lint.core.ports import ASTParserPort
from scripts.lint.core.ports import FileLoaderPort
from scripts.lint.core.result import Result


class FilesystemFileLoader(FileLoaderPort):
    """Concrete adapter for reading files from local filesystem."""

    def read_source(self, path: str) -> Result[str]:
        """Read source text from local disk.

        Precondition: path is a valid file path string.
        Postcondition: Returns Result.success with file text or Result.failure.
        Side effect: Reads disk file.
        Resource: File handle.
        Failure: Returns Result.failure on OSError or encoding error.
        """
        b_continue = True
        result: Result[str] = Result.failure(f"Failed to read {path}")
        try:
            content = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            b_continue = False
            result = Result.failure(f"Error reading {path}: {exc}")
        except UnicodeDecodeError as exc:
            b_continue = False
            result = Result.failure(f"Encoding error reading {path}: {exc}")

        if b_continue:
            result = Result.success(content)
        return result


class StandardASTParser(ASTParserPort):
    """Concrete adapter for parsing Python code using standard ast module."""

    def parse_ast(self, source: str, filename: str) -> Result[ast.AST]:
        """Parse source string using ast.parse.

        Precondition: source is a Python source code string.
        Postcondition: Returns Result.success with AST tree or Result.failure.
        Side effect: None.
        Resource: None.
        Failure: Returns Result.failure on SyntaxError or ValueError.
        """
        b_continue = True
        result: Result[ast.AST] = Result.failure(f"Failed to parse {filename}")
        try:
            tree = ast.parse(source, filename=filename)
        except SyntaxError as exc:
            b_continue = False
            result = Result.failure(
                f"SyntaxError in {filename}:{exc.lineno}:{exc.offset}: {exc.msg}"
            )
        except ValueError as exc:
            b_continue = False
            result = Result.failure(f"ValueError parsing {filename}: {exc}")

        if b_continue:
            result = Result.success(tree)
        return result
