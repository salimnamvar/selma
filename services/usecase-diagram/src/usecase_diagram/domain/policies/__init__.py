"""Domain policies — validation and naming rules for use case diagrams."""

from usecase_diagram.domain.policies.naming import NamingPolicy
from usecase_diagram.domain.policies.validation import ValidationPolicy

__all__ = ["NamingPolicy", "ValidationPolicy"]
