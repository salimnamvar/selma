"""Tests for Python parser integration."""

from pathlib import Path

from selma.adapters.python.parser import TreeSitterPythonParser
from selma.core.entities.facts import FactDocument


class TestTreeSitterPythonParser:
    """Integration tests for Tree-sitter Python parser."""

    def setup_method(self):
        self.parser = TreeSitterPythonParser()
        self.fixture_path = Path(__file__).parent.parent / "fixtures" / "sample.py"

    def test_parse_sample_file(self):
        document = self.parser.extract(self.fixture_path, ["lines", "declarations"])

        assert isinstance(document, FactDocument)
        assert document.language == "python"
        assert document.file == str(self.fixture_path)
        assert len(document.hash) == 64  # SHA-256 hex digest

    def test_extract_lines(self):
        document = self.parser.extract(self.fixture_path, ["lines"])

        lines = document.layers.get("lines", [])
        assert len(lines) > 0
        assert lines[0].number == 1

    def test_extract_declarations(self):
        document = self.parser.extract(self.fixture_path, ["declarations"])

        declarations = document.layers.get("declarations", [])
        assert len(declarations) > 0

        # Check we found functions
        functions = [d for d in declarations if d.kind == "function"]
        assert len(functions) > 0

        # Check hello_world function
        hello = next((f for f in functions if f.name == "hello_world"), None)
        assert hello is not None
        assert hello.is_dunder is False

    def test_extract_classes(self):
        document = self.parser.extract(self.fixture_path, ["declarations"])

        declarations = document.layers.get("declarations", [])
        classes = [d for d in declarations if d.kind == "class"]
        assert len(classes) > 0

        calc = next((c for c in classes if c.name == "Calculator"), None)
        assert calc is not None

    def test_extract_imports(self):
        document = self.parser.extract(self.fixture_path, ["declarations"])

        declarations = document.layers.get("declarations", [])
        imports = [d for d in declarations if d.kind == "import"]
        assert len(imports) > 0

    def test_dunder_detection(self):
        document = self.parser.extract(self.fixture_path, ["declarations"])

        declarations = document.layers.get("declarations", [])
        functions = [d for d in declarations if d.kind == "function"]

        dunder = next((f for f in functions if f.name == "__dunder_method__"), None)
        assert dunder is not None
        assert dunder.is_dunder is True

    def test_parameters_extraction(self):
        document = self.parser.extract(self.fixture_path, ["declarations"])

        declarations = document.layers.get("declarations", [])
        functions = [d for d in declarations if d.kind == "function"]

        complex_func = next((f for f in functions if f.name == "complex_func"), None)
        assert complex_func is not None
        assert len(complex_func.parameters) > 0
