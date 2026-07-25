"""Tests for FilePath value object — equality, extension, name."""

import pytest

from selma.domain.value_objects.file_path import FilePath


class TestFilePathEquality:
    """FilePath equality behavior."""

    def test_same_value_equal(self) -> None:
        """FilePath with same value should be equal."""
        fp1 = FilePath("/src/main.py")
        fp2 = FilePath("/src/main.py")
        assert fp1 == fp2

    def test_different_value_not_equal(self) -> None:
        """FilePath with different values should not be equal."""
        fp1 = FilePath("/src/main.py")
        fp2 = FilePath("/src/other.py")
        assert fp1 != fp2

    def test_not_equal_to_non_file_path(self) -> None:
        """FilePath should not be equal to a non-FilePath object."""
        fp = FilePath("/src/main.py")
        assert fp != "/src/main.py"
        assert fp != 42


class TestFilePathProperties:
    """FilePath property behavior."""

    def test_extension(self) -> None:
        """Extension should return the file suffix."""
        fp = FilePath("/src/main.py")
        assert fp.extension == ".py"

    def test_extension_no_dot(self) -> None:
        """Extension returns empty for files without extension."""
        fp = FilePath("/src/Makefile")
        assert fp.extension == ""

    def test_name(self) -> None:
        """Name should return the filename portion."""
        fp = FilePath("/src/deep/main.py")
        assert fp.name == "main.py"

    def test_value_returns_raw(self) -> None:
        """Value property returns the raw string."""
        fp = FilePath("/src/main.py")
        assert fp.value == "/src/main.py"


class TestFilePathValidation:
    """FilePath validation behavior."""

    def test_empty_raises(self) -> None:
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            FilePath("")

    def test_valid_value(self) -> None:
        """Non-empty string should create valid FilePath."""
        fp = FilePath("/src/main.py")
        assert fp.value == "/src/main.py"


class TestFilePathString:
    """FilePath string representations."""

    def test_str(self) -> None:
        """str() should return the raw value."""
        fp = FilePath("/src/main.py")
        assert str(fp) == "/src/main.py"

    def test_repr(self) -> None:
        """repr() should show the FilePath wrapper."""
        fp = FilePath("/src/main.py")
        assert repr(fp) == "FilePath('/src/main.py')"
