"""Domain policies — validation and naming rules for use case diagrams."""

from .naming import NamingPolicy
from .validation import ValidationPolicy

__all__ = ["NamingPolicy", "ValidationPolicy"]
