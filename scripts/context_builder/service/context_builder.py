"""Service layer for LLM Context Builder.

Orchestrates the context building pipeline with dependency injection.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from context_builder.domain.enums import OutputMode
from context_builder.domain.models import ContextConfig
from context_builder.domain.models import ContextResult
from context_builder.domain.models import Document
from context_builder.infrastructure.output_path_resolver import resolve_output_path
from context_builder.pipeline.renderer_pipeline import render_and_write
from context_builder.pipeline.splitter_pipeline import split_documents
from context_builder.renderer.protocols import RendererProtocol
from context_builder.repository.protocols import CollectorProtocol
from context_builder.repository.protocols import WriterProtocol


class ContextBuilderService:
    """Main orchestration service for building LLM context.

    Attributes:
        _config (ContextConfig): Configuration.
    """

    def __init__(
        self,
        a_config: ContextConfig,
        a_collector: CollectorProtocol,
        a_writer: WriterProtocol,
        a_renderer: RendererProtocol,
        a_tokenizer: Callable[[str], int],
    ) -> None:
        """Initialize service with injected dependencies.

        Args:
            a_config: Configuration.
            a_collector: Document collector.
            a_writer: Output writer.
            a_renderer: Content renderer.
            a_tokenizer: Token counting function.
        """
        self._config: ContextConfig = a_config
        self._collector: CollectorProtocol = a_collector
        self._writer: WriterProtocol = a_writer
        self._renderer: RendererProtocol = a_renderer
        self._tokenizer: Callable[[str], int] = a_tokenizer

    def build(self) -> ContextResult:
        """Build context and write output.

        Returns:
            ContextResult: Result of the operation.
        """
        # Collect documents
        documents: list[Document] = self._collector.collect(self._config.inputs)

        # Order documents
        documents = sorted(documents, key=lambda d: d.path)

        # Determine chunks based on mode
        chunks: list[list[Document]]
        if self._config.mode == OutputMode.AGGREGATE and self._config.max_tokens is not None:
            chunks = split_documents(documents, self._config.max_tokens)
        else:
            chunks = [documents]

        # Resolve output path
        out_path: Path = resolve_output_path(self._config.output_path)

        # Render and write
        result: ContextResult = render_and_write(
            a_documents=documents,
            a_chunks=chunks,
            a_output_path=out_path,
            a_mode=self._config.mode,
            a_max_tokens=self._config.max_tokens,
            a_renderer=self._renderer,
            a_writer=self._writer,
        )

        return result
