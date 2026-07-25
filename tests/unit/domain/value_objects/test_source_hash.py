"""Tests for SourceHash value object — creation, equality, hashing."""

import hashlib

import pytest

from selma.domain.value_objects.source_hash import SourceHash


class TestSourceHashCreation:
    """SourceHash creation behavior."""

    def test_from_string_value(self) -> None:
        """SourceHash should store the provided value."""
        sh = SourceHash("abc123")
        assert sh.value == "abc123"

    def test_from_content_string(self) -> None:
        """from_content with string should create valid hash."""
        sh = SourceHash.from_content("hello")
        assert len(sh.value) == 64  # SHA-256 hex digest

    def test_from_content_bytes(self) -> None:
        """from_content with bytes should create valid hash."""
        sh = SourceHash.from_content(b"hello")
        assert len(sh.value) == 64  # SHA-256 hex digest

    def test_empty_raises(self) -> None:
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            SourceHash("")


class TestSourceHashEquality:
    """SourceHash equality behavior."""

    def test_same_value_equal(self) -> None:
        """SourceHash with same value should be equal."""
        h1 = SourceHash("abc123")
        h2 = SourceHash("abc123")
        assert h1 == h2

    def test_different_value_not_equal(self) -> None:
        """SourceHash with different values should not be equal."""
        h1 = SourceHash("abc123")
        h2 = SourceHash("def456")
        assert h1 != h2

    def test_not_equal_to_non_source_hash(self) -> None:
        """SourceHash should not equal a non-SourceHash object."""
        sh = SourceHash("abc123")
        assert sh != "abc123"


class TestSourceHashHashing:
    """SourceHash hashing behavior."""

    def test_same_value_same_hash(self) -> None:
        """SourceHash with same value should have same hash."""
        h1 = SourceHash("abc123")
        h2 = SourceHash("abc123")
        assert hash(h1) == hash(h2)

    def test_usable_in_set(self) -> None:
        """SourceHash should be usable as a set element."""
        s = {SourceHash("abc"), SourceHash("abc"), SourceHash("def")}
        assert len(s) == 2


class TestSourceHashString:
    """SourceHash string representations."""

    def test_str(self) -> None:
        """str() should return the raw hash value."""
        sh = SourceHash("abc123")
        assert str(sh) == "abc123"

    def test_repr_truncates(self) -> None:
        """repr() should truncate the hash for readability."""
        sh = SourceHash("abcdef1234567890")
        r = repr(sh)
        assert r.startswith("SourceHash(abcdef123456...")
        assert r.endswith(")")
