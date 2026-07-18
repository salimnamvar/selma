"""Domain layer for LLM Context Builder.

Provides domain entities, enums, and exceptions.
"""

from context_builder.domain.enums import OutputMode
from context_builder.domain.exceptions import ContextBuilderError
from context_builder.domain.exceptions import InputNotFoundError
from context_builder.domain.exceptions import NoDocumentsError
from context_builder.domain.exceptions import ProjectBaseError
from context_builder.domain.models import BaseEntity
from context_builder.domain.models import ContextConfig
from context_builder.domain.models import ContextResult
from context_builder.domain.models import Document

__all__ = [
    "BaseEntity",
    "ContextBuilderError",
    "ContextConfig",
    "ContextResult",
    "Document",
    "InputNotFoundError",
    "NoDocumentsError",
    "OutputMode",
    "ProjectBaseError",
]
