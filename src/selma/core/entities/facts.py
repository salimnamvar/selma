"""Universal Fact Document model for Selma."""

from pydantic import BaseModel

class ParameterNode(BaseModel):
    """Represents a function parameter."""

    name: str
    # positional_only, positional, var_positional, keyword_only, var_keyword
    position: str
    has_default: bool
    type_annotation: str | None = None
    line: int


class DeclarationNode(BaseModel):
    """Represents a code declaration (function, class, import, etc.)."""

    kind: str  # function, class, import, etc.
    name: str
    line: int
    end_line: int
    parent: str | None = None
    # Function specifics
    is_dunder: bool = False
    has_decorator: bool = False
    parameters: list[ParameterNode] = []
    # Import specifics
    import_module: str | None = None


class LineNode(BaseModel):
    """Represents a single line of source code."""

    number: int
    content: str
    stripped: str
    indent: int


class FactDocument(BaseModel):
    """Universal Fact Document - the output of parsing."""

    schema_version: str = "1.0.0"
    file: str
    language: str
    hash: str
    layers: dict[str, list[LineNode | DeclarationNode]]
