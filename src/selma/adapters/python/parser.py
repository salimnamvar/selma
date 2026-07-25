"""Tree-sitter Python parser adapter."""

import hashlib
from pathlib import Path

from tree_sitter import Language
from tree_sitter import Parser
from tree_sitter import Query
from tree_sitter import QueryCursor
from tree_sitter_python import language

from selma.adapters.python.queries import CLASS_QUERY
from selma.adapters.python.queries import FUNCTION_QUERY
from selma.adapters.python.queries import IMPORT_QUERY
from selma.core.entities.facts import DeclarationNode
from selma.core.entities.facts import FactDocument
from selma.core.entities.facts import LineNode
from selma.core.entities.facts import ParameterNode
from selma.core.ports.parser_port import AbstractParser


class TreeSitterPythonParser(AbstractParser):
    """Python parser using Tree-sitter."""

    def __init__(self) -> None:
        """Initialize the parser with Python language."""
        self.language = Language(language())
        self.parser = Parser(self.language)

    def extract(self, path: Path, requested_layers: list[str]) -> FactDocument:
        """Extract facts from a Python source file.

        Args:
            path: Path to the Python source file.
            requested_layers: List of fact layers to extract.

        Returns:
            FactDocument containing the extracted facts.
        """
        content = path.read_text(encoding="utf-8")
        file_hash = hashlib.sha256(content.encode()).hexdigest()

        tree = self.parser.parse(bytes(content, "utf-8"))

        layers: dict[str, list[LineNode | DeclarationNode]] = {}

        if "lines" in requested_layers:
            layers["lines"] = self._extract_lines(content)

        if "declarations" in requested_layers:
            layers["declarations"] = self._extract_declarations(tree)

        return FactDocument(
            file=str(path),
            language="python",
            hash=file_hash,
            layers=layers,
        )

    def _extract_lines(self, content: str) -> list[LineNode]:
        """Extract line nodes from content."""
        lines = []
        for i, line in enumerate(content.split("\n"), 1):
            lines.append(
                LineNode(
                    number=i,
                    content=line,
                    stripped=line.strip(),
                    indent=len(line) - len(line.lstrip()),
                ),
            )
        return lines

    def _extract_declarations(self, tree: object) -> list[DeclarationNode]:
        """Extract declaration nodes from the AST."""
        declarations: list[DeclarationNode] = []

        # Query functions
        func_query = Query(self.language, FUNCTION_QUERY)
        func_cursor = QueryCursor(func_query)
        func_matches = func_cursor.matches(tree.root_node)

        for _pattern_idx, captures in func_matches:
            func_def = captures.get("func_def")
            if func_def:
                match = func_def[0] if isinstance(func_def, list) else func_def
                name_node = match.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf-8")
                    start_line = match.start_point[0] + 1
                    end_line = match.end_point[0] + 1

                    # Extract parameters
                    params = self._extract_parameters(match)

                    declarations.append(
                        DeclarationNode(
                            kind="function",
                            name=name,
                            line=start_line,
                            end_line=end_line,
                            is_dunder=name.startswith("__") and name.endswith("__"),
                            has_decorator=self._has_decorator(match),
                            parameters=params,
                        ),
                    )

        # Query classes
        class_query = Query(self.language, CLASS_QUERY)
        class_cursor = QueryCursor(class_query)
        class_matches = class_cursor.matches(tree.root_node)

        for _pattern_idx, captures in class_matches:
            class_def = captures.get("class_def")
            if class_def:
                match = class_def[0] if isinstance(class_def, list) else class_def
                name_node = match.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf-8")
                    start_line = match.start_point[0] + 1
                    end_line = match.end_point[0] + 1

                    declarations.append(
                        DeclarationNode(
                            kind="class",
                            name=name,
                            line=start_line,
                            end_line=end_line,
                            is_dunder=name.startswith("__") and name.endswith("__"),
                            has_decorator=self._has_decorator(match),
                        ),
                    )

        # Query imports
        import_query = Query(self.language, IMPORT_QUERY)
        import_cursor = QueryCursor(import_query)
        import_matches = import_cursor.matches(tree.root_node)

        for _pattern_idx, captures in import_matches:
            import_node = captures.get("import") or captures.get("import_from")
            module_captures = captures.get("module")
            if import_node and module_captures:
                match = import_node[0] if isinstance(import_node, list) else import_node
                module_capture = module_captures[0] if isinstance(module_captures, list) else module_captures
                module_name = module_capture.text.decode("utf-8")
                start_line = match.start_point[0] + 1
                end_line = match.end_point[0] + 1

                declarations.append(
                    DeclarationNode(
                        kind="import",
                        name=module_name,
                        line=start_line,
                        end_line=end_line,
                        import_module=module_name,
                    ),
                )

        return declarations

    def _extract_parameters(self, func_node: object) -> list[ParameterNode]:
        """Extract parameters from a function node."""
        params: list[ParameterNode] = []
        params_node = func_node.child_by_field_name("parameters")

        if not params_node:
            return params

        for child in params_node.children:
            param = self._parse_param_node(child)
            if param:
                params.append(param)

        return params

    def _parse_param_node(self, child: object) -> ParameterNode | None:
        """Parse a single parameter node."""
        node_type = child.type
        if node_type == "identifier":
            return ParameterNode(
                name=child.text.decode("utf-8"),
                position="positional",
                has_default=False,
                line=child.start_point[0] + 1,
            )

        type_map = {
            "default_parameter": ("keyword_only", True),
            "list_splat_pattern": ("var_positional", False),
            "dictionary_splat_pattern": ("var_keyword", False),
        }

        if node_type not in type_map:
            return None

        position, has_default = type_map[node_type]
        for subchild in child.children:
            if subchild.type == "identifier":
                return ParameterNode(
                    name=subchild.text.decode("utf-8"),
                    position=position,
                    has_default=has_default,
                    line=subchild.start_point[0] + 1,
                )

        return None

    def _has_decorator(self, node: object) -> bool:
        """Check if a node has a decorator."""
        parent = node.parent
        return parent is not None and parent.type == "decorated_definition"
