"""Collector pipeline for LLM Context Builder.

Collects documents and orders them alphabetically.
"""

from __future__ import annotations

from collections.abc import Callable

from context_builder.domain.models import Document
from context_builder.repository.collector import FilesystemCollector


def collect_and_order(
    a_inputs: list[str],
    a_extensions: frozenset[str],
    a_exclude: frozenset[str],
    a_tokenizer: Callable[[str], int],
) -> list[Document]:
    """Collect documents from inputs and order alphabetically.

    Args:
        a_inputs: Input paths to collect from.
        a_extensions: File extensions to include.
        a_exclude: Directory names to exclude.
        a_tokenizer: Token counting function.

    Returns:
        Ordered list of collected documents.
    """
    collector: FilesystemCollector = FilesystemCollector(a_extensions, a_exclude, a_tokenizer)
    documents: list[Document] = collector.collect(a_inputs)
    return sorted(documents, key=lambda d: d.path)
