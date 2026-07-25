"""Tests for LintRequest DTO — creation."""

from selma.application.dto.lint_request import LintRequest
from selma.domain.value_objects.file_path import FilePath


class TestLintRequestCreation:
    """LintRequest creation behavior."""

    def test_required_fields(self) -> None:
        """LintRequest should accept paths."""
        r = LintRequest(paths=(FilePath("/src/main.py"),))
        assert len(r.paths) == 1
        assert r.paths[0].value == "/src/main.py"

    def test_defaults(self) -> None:
        """LintRequest should have sensible defaults."""
        r = LintRequest(paths=())
        assert r.exclude_codes == frozenset()
        assert r.codes == frozenset()
        assert r.format == "default"
        assert r.guide is False
        assert r.skip_tools is False
        assert r.skip_ast is False
        assert r.only is None

    def test_multiple_paths(self) -> None:
        """LintRequest should accept multiple paths."""
        paths = (FilePath("/src/a.py"), FilePath("/src/b.py"))
        r = LintRequest(paths=paths)
        assert len(r.paths) == 2

    def test_with_exclude_codes(self) -> None:
        """LintRequest should accept exclude_codes."""
        r = LintRequest(
            paths=(FilePath("/src/main.py"),),
            exclude_codes=frozenset({"SC001", "SC002"}),
        )
        assert r.exclude_codes == frozenset({"SC001", "SC002"})

    def test_with_only(self) -> None:
        """LintRequest should accept only filter."""
        r = LintRequest(
            paths=(FilePath("/src/main.py"),),
            only="SC001",
        )
        assert r.only == "SC001"

    def test_frozen(self) -> None:
        """LintRequest should be immutable."""
        r = LintRequest(paths=())
        assert hasattr(r, "__pydantic_fields__")
        try:
            r.format = "json"  # type: ignore[misc]
            assert False, "Should have raised ValidationError"
        except Exception:
            pass
