"""Tests for InspectRequest DTO."""

from selma.application.dto.inspect_request import InspectRequest
from selma.domain.value_objects.file_path import FilePath


def test_defaults() -> None:
    """Test defaults."""
    req = InspectRequest()
    assert req.paths == ()
    assert req.codes == frozenset()
    assert req.format == "default"


def test_with_paths() -> None:
    """Test with paths."""
    req = InspectRequest(paths=(FilePath("a.py"),), codes=frozenset({"SC-001"}))
    assert len(req.paths) == 1
    assert "SC-001" in req.codes
