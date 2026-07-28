"""Tests for Result[T] value object — P0.1 fix verification.

CRITICAL: These tests verify that Result.success(None) works correctly
and that unwrap() on Result.success(None) returns None (not failure).
"""

from selma.domain.value_objects.result import INVALID_RESULT
from selma.domain.value_objects.result import Result


class TestResultSuccess:
    """Tests for Result.success()."""

    def test_success_with_value(self) -> None:
        """Result.success(42) should have is_success=True and value=42."""
        r = Result.success(42)
        assert r.is_success() is True
        assert r.is_failure() is False
        assert r.value == 42
        assert r.message == "Success"

    def test_success_with_string(self) -> None:
        """Result.success('hello') should work."""
        r = Result.success("hello")
        assert r.is_success() is True
        assert r.value == "hello"

    def test_success_with_none(self) -> None:
        """P0.1 FIX: Result.success(None) should have is_success=True."""
        r = Result.success(None)
        assert r.is_success() is True
        assert r.is_failure() is False
        assert r.value is None

    def test_success_with_custom_message(self) -> None:
        """Result.success(1, 'done') should have custom message."""
        r = Result.success(1, "done")
        assert r.is_success() is True
        assert r.message == "done"

    def test_bool_truthy_on_success(self) -> None:
        """If result: should be True for success."""
        r = Result.success(42)
        assert bool(r) is True

    def test_bool_falsy_on_failure(self) -> None:
        """If result: should be False for failure."""
        r = Result.failure("error")
        assert bool(r) is False


class TestResultFailure:
    """Tests for Result.failure()."""

    def test_failure(self) -> None:
        """Result.failure('error') should have is_success=False."""
        r = Result.failure("error")
        assert r.is_success() is False
        assert r.is_failure() is True
        assert r.value is None
        assert r.message == "error"


class TestResultUnwrap:
    """Tests for Result.unwrap() — P0.1 fix verification."""

    def test_unwrap_success_with_value(self) -> None:
        """unwrap() on success returns the value."""
        r = Result.success(42)
        assert r.unwrap() == 42

    def test_unwrap_success_with_none(self) -> None:
        """P0.1 FIX: unwrap() on Result.success(None) returns None."""
        r = Result.success(None)
        assert r.unwrap() is None

    def test_unwrap_failure_is_null_path(self) -> None:
        """unwrap() on failure does not raise; prefer unwrap_or for defaults."""
        r = Result.failure("error")
        assert r.is_failure()
        assert r.unwrap() is None


class TestResultUnwrapOr:
    """Tests for Result.unwrap_or() — P0.1 fix verification."""

    def test_unwrap_or_success(self) -> None:
        """unwrap_or() on success returns the value."""
        r = Result.success(42)
        assert r.unwrap_or(0) == 42

    def test_unwrap_or_success_with_none(self) -> None:
        """P0.1 FIX: unwrap_or() on Result.success(None) returns None."""
        r = Result.success(None)
        assert r.unwrap_or(0) is None

    def test_unwrap_or_failure(self) -> None:
        """unwrap_or() on failure returns default."""
        r = Result.failure("error")
        assert r.unwrap_or(0) == 0


class TestResultMap:
    """Tests for Result.map()."""

    def test_map_success(self) -> None:
        """map() on success transforms the value."""
        r = Result.success(2)
        mapped = r.map(lambda x: x * 3)
        assert mapped.is_success() is True
        assert mapped.value == 6

    def test_map_failure(self) -> None:
        """map() on failure preserves the failure."""
        r = Result.failure("error")
        mapped = r.map(lambda x: x * 3)
        assert mapped.is_success() is False
        assert mapped.message == "error"

    def test_map_success_with_none(self) -> None:
        """P0.1 FIX: map() on Result.success(None) applies function to None."""
        r = Result.success(None)
        mapped = r.map(lambda x: "was None" if x is None else "not None")
        assert mapped.is_success() is True
        assert mapped.value == "was None"


class TestResultFlatMap:
    """Tests for Result.flat_map()."""

    def test_flat_map_success(self) -> None:
        """flat_map() on success chains the function."""
        r = Result.success(2)
        chained = r.flat_map(lambda x: Result.success(x * 3))
        assert chained.is_success() is True
        assert chained.value == 6

    def test_flat_map_failure(self) -> None:
        """flat_map() on failure preserves the failure."""
        r = Result.failure("error")
        chained = r.flat_map(lambda x: Result.success(x * 3))
        assert chained.is_success() is False
        assert chained.message == "error"


class TestInvalidResult:
    """Tests for INVALID_RESULT sentinel."""

    def test_invalid_result_is_failure(self) -> None:
        """INVALID_RESULT should be a failure result."""
        assert INVALID_RESULT.is_failure() is True
        assert INVALID_RESULT.value is None
        assert "INVALID_RESULT" in INVALID_RESULT.message
