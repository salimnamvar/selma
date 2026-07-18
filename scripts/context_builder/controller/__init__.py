"""Controller layer for LLM Context Builder.

Provides CLI interface for context building.
"""

from context_builder.controller.cli import app
from context_builder.controller.cli import build

__all__ = ["app", "build"]
