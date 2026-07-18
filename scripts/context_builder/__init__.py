"""LLM Context Builder - build context for AI from source files."""

from context_builder.controller import app
from context_builder.controller import build
from context_builder.domain import BaseEntity
from context_builder.domain import ContextConfig
from context_builder.domain import ContextResult
from context_builder.domain import Document
from context_builder.domain import OutputMode
from context_builder.infrastructure import ContextBuilderSettings
from context_builder.infrastructure import count_tokens
from context_builder.infrastructure import resolve_output_path
from context_builder.renderer import detect_language
from context_builder.service import ContextBuilderService

__all__ = [
    "BaseEntity",
    "ContextBuilderService",
    "ContextBuilderSettings",
    "ContextConfig",
    "ContextResult",
    "Document",
    "OutputMode",
    "app",
    "build",
    "count_tokens",
    "detect_language",
    "resolve_output_path",
]
