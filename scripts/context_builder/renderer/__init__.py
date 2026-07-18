"""Renderer layer for LLM Context Builder.

Provides document rendering implementations and language detection.
"""

from context_builder.renderer.language import detect_language
from context_builder.renderer.markdown import MarkdownRenderer
from context_builder.renderer.protocols import RendererProtocol

__all__ = ["MarkdownRenderer", "RendererProtocol", "detect_language"]
