"""Pipeline layer for LLM Context Builder.

Orchestrates data flow through collection, splitting, and rendering stages.
"""

from context_builder.pipeline.collector_pipeline import collect_and_order
from context_builder.pipeline.renderer_pipeline import render_and_write
from context_builder.pipeline.splitter_pipeline import split_documents

__all__ = ["collect_and_order", "render_and_write", "split_documents"]
