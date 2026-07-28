"""Python AST parser — infrastructure implementation of SourceParser port."""

from __future__ import annotations

import ast
import asyncio
import logging
from pathlib import Path

from selma.application.ports.parser_port import SourceParser
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result

logger = logging.getLogger(__name__)


class PythonAstParser(SourceParser):
    """Infrastructure: Python AST parser using stdlib ast module."""

    async def parse(self, a_path: FilePath) -> Result[ast.AST]:
        """Parse a Python source file into an AST."""
        return await asyncio.to_thread(self._parse_sync, a_path)

    async def parse_source(
        self, a_source: str, a_filename: str = "<string>"
    ) -> Result[ast.AST]:
        """Parse source code string into an AST."""
        return await asyncio.to_thread(self._parse_source_sync, a_source, a_filename)

    def _parse_sync(self, a_path: FilePath) -> Result[ast.AST]:
        """Blocking parse of a file path."""
        b_continue = True
        result: Result[ast.AST] = Result.failure("unreachable")
        source = str(a_path)
        try:
            content = Path(source).read_text(encoding="utf-8")
            tree = ast.parse(content, filename=source)
            if b_continue:
                result = Result.success(tree)
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            if b_continue:
                logger.warning("Failed to parse %s: %s", a_path, exc)
                b_continue = False
                logger.warning("Parse error: %s", exc)
                result = Result.failure(f"Parse error: {exc}")
        return result

    def _parse_source_sync(
        self, a_source: str, a_filename: str = "<string>"
    ) -> Result[ast.AST]:
        """Blocking parse of source text."""
        b_continue = True
        result: Result[ast.AST] = Result.failure("unreachable")
        try:
            tree = ast.parse(a_source, filename=a_filename)
            if b_continue:
                result = Result.success(tree)
        except SyntaxError as exc:
            if b_continue:
                b_continue = False
                logger.warning("Syntax error: %s", exc)
                result = Result.failure(f"Syntax error: {exc}")
        return result
