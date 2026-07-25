"""Domain errors — exception hierarchy for domain violations."""

from __future__ import annotations


class DomainError(Exception):
    """Base domain error."""

    def __init__(self, a_message: str = "") -> None:
        super().__init__(a_message)
        self.message = a_message


class RuleNotFound(DomainError):
    """Raised when a rule cannot be found."""

    def __init__(self, a_rule_id: str = "") -> None:
        super().__init__(f"Rule not found: {a_rule_id}")
        self.rule_id = a_rule_id


class InvalidFactDocument(DomainError):
    """Raised when a fact document is invalid."""

    def __init__(self, a_message: str = "") -> None:
        super().__init__(a_message or "Invalid fact document")


class LintResultAlreadyComplete(DomainError):
    """Raised when trying to add finding to completed result."""

    def __init__(self, a_message: str = "") -> None:
        super().__init__(a_message or "Lint result already complete")


class InvalidRuleDefinition(DomainError):
    """Raised when a rule definition is invalid."""

    def __init__(self, a_message: str = "") -> None:
        super().__init__(a_message or "Invalid rule definition")
