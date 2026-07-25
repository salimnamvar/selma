"""Tests for SourceFile entity — creation."""

from selma.domain.entities.source_file import SourceFile
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.source_hash import SourceHash


class TestSourceFileCreation:
    """SourceFile creation behavior."""

    def test_required_fields(self) -> None:
        """SourceFile should accept path and hash."""
        fp = FilePath("/src/main.py")
        sh = SourceHash("abc123")
        sf = SourceFile(path=fp, hash=sh)
        assert sf.path == fp
        assert sf.hash == sh

    def test_defaults(self) -> None:
        """SourceFile should have sensible defaults."""
        sf = SourceFile(path=FilePath("/src/main.py"), hash=SourceHash("abc"))
        assert sf.language == "python"
        assert sf.content == ""

    def test_extension_delegates_to_path(self) -> None:
        """extension property should delegate to path.extension."""
        sf = SourceFile(path=FilePath("/src/main.py"), hash=SourceHash("abc"))
        assert sf.extension == ".py"

    def test_extension_no_suffix(self) -> None:
        """extension returns empty for files without suffix."""
        sf = SourceFile(path=FilePath("/src/Makefile"), hash=SourceHash("abc"))
        assert sf.extension == ""

    def test_custom_language(self) -> None:
        """language can be set to non-default value."""
        sf = SourceFile(
            path=FilePath("/src/main.js"),
            hash=SourceHash("abc"),
            language="javascript",
        )
        assert sf.language == "javascript"

    def test_content_stored(self) -> None:
        """content should be stored as provided."""
        sf = SourceFile(
            path=FilePath("/src/main.py"),
            hash=SourceHash("abc"),
            content="print('hello')",
        )
        assert sf.content == "print('hello')"
