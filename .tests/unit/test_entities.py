"""Tests for entities."""

from selma.core.entities.facts import DeclarationNode
from selma.core.entities.facts import FactDocument
from selma.core.entities.facts import LineNode
from selma.core.entities.facts import ParameterNode
from selma.core.entities.finding import Finding
from selma.core.entities.finding import Weight
from selma.core.entities.rule import EvaluatorConfig
from selma.core.entities.rule import Rule


class TestParameterNode:
    """Tests for ParameterNode."""

    def test_creation(self):
        param = ParameterNode(
            name="x",
            position="positional",
            has_default=False,
            line=10,
        )
        assert param.name == "x"
        assert param.position == "positional"
        assert param.has_default is False

    def test_with_annotation(self):
        param = ParameterNode(
            name="x",
            position="positional",
            has_default=False,
            type_annotation="int",
            line=10,
        )
        assert param.type_annotation == "int"


class TestDeclarationNode:
    """Tests for DeclarationNode."""

    def test_function(self):
        decl = DeclarationNode(
            kind="function",
            name="hello",
            line=1,
            end_line=5,
            is_dunder=False,
            has_decorator=False,
        )
        assert decl.kind == "function"
        assert decl.name == "hello"

    def test_with_parameters(self):
        params = [
            ParameterNode(name="a", position="positional", has_default=False, line=1),
            ParameterNode(name="b", position="keyword_only", has_default=True, line=1),
        ]
        decl = DeclarationNode(
            kind="function",
            name="complex",
            line=1,
            end_line=10,
            parameters=params,
        )
        assert len(decl.parameters) == 2


class TestLineNode:
    """Tests for LineNode."""

    def test_creation(self):
        line = LineNode(
            number=1,
            content="  x = 1",
            stripped="x = 1",
            indent=2,
        )
        assert line.number == 1
        assert line.indent == 2


class TestFactDocument:
    """Tests for FactDocument."""

    def test_creation(self):
        doc = FactDocument(
            file="/path/to/file.py",
            language="python",
            hash="abc123",
            layers={"lines": [], "declarations": []},
        )
        assert doc.schema_version == "1.0.0"
        assert doc.language == "python"


class TestFinding:
    """Tests for Finding."""

    def test_creation(self):
        finding = Finding(
            rule_id="RULE-001",
            file="test.py",
            line=10,
            message="Test finding",
            weight=Weight.HIGH,
        )
        assert finding.rule_id == "RULE-001"
        assert finding.weight == Weight.HIGH


class TestRule:
    """Tests for Rule."""

    def test_creation(self):
        rule = Rule(
            id="RULE-001",
            message="Test rule",
            evaluator_type="field_check",
            evaluator_config=EvaluatorConfig(field="name", operator="eq", value="test"),
        )
        assert rule.id == "RULE-001"
        assert rule.weight == "medium"
