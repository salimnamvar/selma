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
from context_builder.pipeline.collector_pipeline import collect_and_order
from context_builder.pipeline.renderer_pipeline import render_and_write
from context_builder.pipeline.splitter_pipeline import split_documents
from context_builder.renderer.markdown import MarkdownRenderer
from context_builder.renderer.protocols import RendererProtocol
from context_builder.repository.protocols import CollectorProtocol
from context_builder.repository.protocols import WriterProtocol
from context_builder.repository.writer import FileWriter


def _noop_tokenizer(_text: str) -> int:
    """No-op tokenizer for fallback.

    Args:
        _text: Ignored text input.

    Returns:
        Always returns 0.
    """
    return 0


class ContextBuilderService:
    """Main orchestration service for building LLM context.

    Attributes:
        _config (ContextConfig): Configuration.
    """

    def __init__(
        self,
        a_config: ContextConfig,
        a_collector: CollectorProtocol | None = None,
        a_writer: WriterProtocol | None = None,
        a_renderer: RendererProtocol | None = None,
        a_tokenizer: Callable[[str], int] | None = None,
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
        self._collector: CollectorProtocol | None = a_collector
        self._writer: WriterProtocol | None = a_writer
        self._renderer: RendererProtocol | None = a_renderer
        self._tokenizer: Callable[[str], int] | None = a_tokenizer

    def build(self) -> ContextResult:
        """Build context and write output.

        Returns:
            ContextResult: Result of the operation.
        """
        # Collect or use injected collector
        if self._collector is not None:
            documents: list[Document] = self._collector.collect(self._config.inputs)
        else:
            tokenizer: Callable[[str], int] = self._tokenizer or _noop_tokenizer
            documents = collect_and_order(
                self._config.inputs,
                self._config.extensions,
                self._config.exclude,
                tokenizer,
            )

        # Order documents
        documents = sorted(documents, key=lambda d: d.path)

        # Determine chunks based on mode
        chunks: list[list[Document]]
        if self._config.mode == OutputMode.AGGREGATE and self._config.max_tokens is not None:
            chunks = split_documents(documents, self._config.max_tokens)
        else:
            chunks = [documents]

        # Resolve output path and get writer/renderer
        out_path: Path = resolve_output_path(self._config.output_path)
        renderer: RendererProtocol = self._renderer or MarkdownRenderer()
        writer: WriterProtocol = self._writer or FileWriter(out_path)

        # Render and write
        result: ContextResult = render_and_write(
            a_documents=documents,
            a_chunks=chunks,
            a_output_path=out_path,
            a_mode=self._config.mode,
            a_max_tokens=self._config.max_tokens,
            a_renderer=renderer,
            a_writer=writer,
        )

        return result
