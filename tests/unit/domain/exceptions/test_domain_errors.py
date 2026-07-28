"""Tests for domain error exceptions — all exception types."""

import pytest

from selma.domain.exceptions.domain_errors import DomainError
from selma.domain.exceptions.domain_errors import InvalidFactDocument
from selma.domain.exceptions.domain_errors import InvalidRule
from selma.domain.exceptions.domain_errors import LintResultAlreadyComplete
from selma.domain.exceptions.domain_errors import RuleNotFound


class TestDomainError:
    """DomainError base exception."""

    def test_message(self) -> None:
        """DomainError should store the message."""
        e = DomainError("test error")
        assert str(e) == "test error"
        assert e.message == "test error"

    def test_default_message(self) -> None:
        """DomainError with no message should default to empty."""
        e = DomainError()
        assert e.message == ""

    def test_is_exception(self) -> None:
        """DomainError should be an Exception subclass."""
        assert issubclass(DomainError, Exception)

    def test_can_be_caught(self) -> None:
        """DomainError should be catchable as Exception."""
        with pytest.raises(Exception):
            raise DomainError("test")


class TestRuleNotFound:
    """RuleNotFound exception."""

    def test_message_includes_rule_id(self) -> None:
        """RuleNotFound should include rule_id in message."""
        e = RuleNotFound("SC001")
        assert "SC001" in str(e)
        assert e.rule_id == "SC001"

    def test_default_message(self) -> None:
        """RuleNotFound with no rule_id should have a default message."""
        e = RuleNotFound()
        assert "Rule not found" in str(e)

    def test_is_domain_error(self) -> None:
        """RuleNotFound should be a DomainError subclass."""
        assert issubclass(RuleNotFound, DomainError)


class TestInvalidFactDocument:
    """InvalidFactDocument exception."""

    def test_message(self) -> None:
        """InvalidFactDocument should store the message."""
        e = InvalidFactDocument("bad doc")
        assert str(e) == "bad doc"

    def test_default_message(self) -> None:
        """InvalidFactDocument with no message should have a default."""
        e = InvalidFactDocument()
        assert "Invalid fact document" in str(e)

    def test_is_domain_error(self) -> None:
        """InvalidFactDocument should be a DomainError subclass."""
        assert issubclass(InvalidFactDocument, DomainError)


class TestLintResultAlreadyComplete:
    """LintResultAlreadyComplete exception."""

    def test_message(self) -> None:
        """LintResultAlreadyComplete should store the message."""
        e = LintResultAlreadyComplete("already done")
        assert str(e) == "already done"

    def test_default_message(self) -> None:
        """LintResultAlreadyComplete with no message should have a default."""
        e = LintResultAlreadyComplete()
        assert "Lint result already complete" in str(e)

    def test_is_domain_error(self) -> None:
        """LintResultAlreadyComplete should be a DomainError subclass."""
        assert issubclass(LintResultAlreadyComplete, DomainError)


class TestInvalidRule:
    """InvalidRule exception."""

    def test_message(self) -> None:
        """InvalidRule should store the message."""
        e = InvalidRule("bad rule")
        assert str(e) == "bad rule"

    def test_default_message(self) -> None:
        """InvalidRule with no message should have a default."""
        e = InvalidRule()
        assert "Invalid rule" in str(e)

    def test_is_domain_error(self) -> None:
        """InvalidRule should be a DomainError subclass."""
        assert issubclass(InvalidRule, DomainError)
