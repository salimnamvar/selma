"""Tests for Severity value object — enum values."""

from selma.domain.value_objects.enums import Severity


class TestSeverityEnum:
    """Severity enum values."""

    def test_all_values_present(self) -> None:
        """Severity should have all five levels."""
        assert len(Severity) == 5

    def test_critical(self) -> None:
        """CRITICAL should exist with correct value."""
        assert Severity.CRITICAL == "critical"

    def test_high(self) -> None:
        """HIGH should exist with correct value."""
        assert Severity.HIGH == "high"

    def test_medium(self) -> None:
        """MEDIUM should exist with correct value."""
        assert Severity.MEDIUM == "medium"

    def test_low(self) -> None:
        """LOW should exist with correct value."""
        assert Severity.LOW == "low"

    def test_informational(self) -> None:
        """INFORMATIONAL should exist with correct value."""
        assert Severity.INFORMATIONAL == "informational"

    def test_is_str_enum(self) -> None:
        """Severity members should be usable as strings."""
        assert Severity.HIGH == "high"
        assert isinstance(Severity.HIGH, str)
