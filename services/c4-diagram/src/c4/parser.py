"""PlantUML C4 Parser.

Extracts nodes, boundaries, and edges from C4-PlantUML source into the IR.
Focuses on the C4 stdlib macros. Best-effort on real-world authored diagrams.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .ir import (
    Boundary,
    BoundaryType,
    C4Diagram,
    DiagramInfo,
    Edge,
    Node,
    NodeType,
)


# Known C4 element macros (order matters for matching)
ELEMENT_MACROS = [
    "Person",
    "System",
    "System_Ext",
    "SystemDb",
    "SystemDb_Ext",
    "Container",
    "Container_Ext",
    "ContainerDb",
    "ContainerDb_Ext",
    "ContainerQueue",
    "Component",
    "Component_Ext",
    # Boundary openers
    "System_Boundary",
    "Container_Boundary",
    "Boundary",  # sub-boundary inside Container_Boundary
]

# Relationship macros (all treated as edges)
REL_MACROS = [
    "Rel",
    "Rel_U",
    "Rel_D",
    "Rel_L",
    "Rel_R",
    "Rel_Back",
    "Rel_Neighbor",
]

# Regex to find a macro call start
MACRO_START_RE = re.compile(
    r"^\s*(?P<macro>[A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE
)

# Match title
TITLE_RE = re.compile(r"^\s*title\s+(.+)$", re.IGNORECASE | re.MULTILINE)

# Detect C4 include
C4_INCLUDE_RE = re.compile(r"C4_(Context|Container|Component)\.puml", re.IGNORECASE)


def _strip_comments(text: str) -> str:
    # Remove single-line ' comments (PlantUML style). Be careful with URLs.
    # We only strip lines starting with ' or after significant content on ' not in strings.
    lines = []
    for line in text.splitlines():
        # Strip full-line comments starting with '
        stripped = line.strip()
        if stripped.startswith("'"):
            lines.append("")  # keep line count stable for simple cases
            continue
        # Remove trailing ' comment if not inside quotes (simple heuristic)
        # We look for ' that is not preceded by :// and is outside "
        in_quote = False
        out = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == '"':
                in_quote = not in_quote
                out.append(ch)
                i += 1
                continue
            if not in_quote and ch == "'" and "://" not in line[max(0, i - 8):i + 3]:
                # rest is comment
                break
            out.append(ch)
            i += 1
        lines.append("".join(out).rstrip())
    return "\n".join(lines)


def _extract_balanced(text: str, start_idx: int) -> tuple[str, int]:
    """Extract content inside balanced parentheses starting after '(' at start_idx."""
    depth = 1
    i = start_idx
    result = []
    in_quote = False
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == '"':
            in_quote = not in_quote
            result.append(ch)
        elif not in_quote:
            if ch == "(":
                depth += 1
                result.append(ch)
            elif ch == ")":
                depth -= 1
                if depth > 0:
                    result.append(ch)
            else:
                result.append(ch)
        else:
            result.append(ch)
        i += 1
    content = "".join(result[:-1]) if result and text[start_idx - 1] == "(" else "".join(result)
    # If we stopped because ), the last ) was not appended when depth==0
    # Adjust: content should be inside the outer ()
    # We started at the char right after the opening '(', so we collected until before final )
    return content, i


def _split_top_level_args(argstr: str) -> list[str]:
    """Split arguments on top-level commas, respecting double quotes."""
    args: list[str] = []
    current: list[str] = []
    in_quote = False
    i = 0
    while i < len(argstr):
        ch = argstr[i]
        if ch == '"':
            in_quote = not in_quote
            current.append(ch)
        elif ch == "," and not in_quote:
            arg = "".join(current).strip()
            if arg:
                args.append(arg)
            current = []
        else:
            current.append(ch)
        i += 1
    last = "".join(current).strip()
    if last:
        args.append(last)
    return args


def _strip_quotes(s: str) -> str:
    s = s.strip()
    # Repeatedly strip matching outer quotes (defensive for quote artifacts)
    while len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    return s.strip()


def _parse_tags(arg: str) -> list[str]:
    # $tags="foo" or $tags="a,b"
    m = re.search(r"\$tags\s*=\s*\"([^\"]+)\"", arg, re.IGNORECASE)
    if not m:
        return []
    raw = m.group(1)
    return [t.strip() for t in raw.split(",") if t.strip()]


def _classify_node_type(macro: str) -> tuple[NodeType, bool]:
    m = macro
    ext = "Ext" in m or "_Ext" in m
    if m == "Person":
        return "Person", False
    if m in ("System", "System_Ext"):
        return "SystemExt" if ext else "System", ext
    if m in ("SystemDb", "SystemDb_Ext"):
        return "SystemDbExt" if ext else "SystemDb", ext
    if m == "Container":
        return "Container", False
    if m == "Container_Ext":
        return "ContainerExt", True
    if m == "ContainerDb":
        return "ContainerDb", False
    if m == "ContainerDb_Ext":
        return "ContainerDbExt", True
    if m == "ContainerQueue":
        return "ContainerQueue", False
    if m == "Component":
        return "Component", False
    if m == "Component_Ext":
        return "ComponentExt", True
    return "System", False  # fallback


def _classify_boundary_type(macro: str) -> BoundaryType:
    if macro == "System_Boundary":
        return "System"
    if macro == "Container_Boundary":
        return "Container"
    if macro == "Boundary":
        return "Component"  # subgroup, but treat as generic component boundary
    return "Generic"


def _infer_level_from_macro_stack(macro_stack: list[str]) -> Optional[str]:
    """Rough C4 level inference based on nesting."""
    has_system_b = any("System_Boundary" in m for m in macro_stack)
    has_container_b = any("Container_Boundary" in m for m in macro_stack)
    has_component = any(m in ("Component", "Component_Ext", "Boundary") for m in macro_stack)
    if has_component or has_container_b:
        # If we saw a Component or entered a Container_Boundary, likely C3
        return "C3"
    if has_system_b:
        return "C2"
    return "C1"


def _normalize_id(s: str) -> str:
    # Keep original alias as id (they are identifiers)
    return s.strip()


def parse_text(text: str, filename: str = "<memory>") -> C4Diagram:
    cleaned = _strip_comments(text)
    inc_match = C4_INCLUDE_RE.search(text)
    original_inc = None
    if inc_match:
        # Try to capture the full "C4_xxx.puml"
        full = re.search(r'C4_(Context|Container|Component)\.puml', text, re.IGNORECASE)
        if full:
            original_inc = full.group(0)
    info = DiagramInfo(
        filename=filename,
        title="",
        includes_c4=bool(inc_match),
        original_include=original_inc,
    )

    title_m = TITLE_RE.search(text)
    if title_m:
        info.title = _strip_quotes(title_m.group(1).strip())

    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    boundaries: dict[str, Boundary] = {}

    node_order: list[str] = []
    edge_keys: list[tuple[str, str, str, str]] = []
    boundary_child_order: dict[str, list[str]] = {}

    def _record_node_order(nid: str) -> None:
        if nid not in node_order:
            node_order.append(nid)

    def _record_edge(e: Edge) -> None:
        key = (e.source, e.target, e.label or "", e.technology or "")
        if key not in edge_keys:
            edge_keys.append(key)

    def _record_child(bid: str | None, nid: str) -> None:
        if not bid:
            return
        if bid not in boundary_child_order:
            boundary_child_order[bid] = []
        if nid not in boundary_child_order[bid]:
            boundary_child_order[bid].append(nid)

    # boundary_stack holds alias of currently open boundaries (outer -> inner)
    boundary_stack: list[str] = []

    # We need to walk the text, find macros, but also track { and } for boundaries.
    # Strategy: scan sequentially, when we see a boundary macro we open after its '{'.
    # When we see '}' we pop if we are inside a boundary.

    pos = 0
    n = len(cleaned)

    def current_boundary() -> str | None:
        return boundary_stack[-1] if boundary_stack else None

    def skip_ws(i: int) -> int:
        while i < n and cleaned[i] in " \t\r\n":
            i += 1
        return i

    while pos < n:
        m = MACRO_START_RE.search(cleaned, pos)
        if not m:
            break

        # Advance over any structural braces between last macro and this one
        between = cleaned[pos : m.start()]
        open_braces = between.count("{")
        close_braces = between.count("}")
        for _ in range(close_braces):
            if boundary_stack:
                boundary_stack.pop()

        macro = m.group("macro")
        start_paren = m.end()
        content, end_pos = _extract_balanced(cleaned, start_paren)

        # After the macro invocation, look ahead for '{' for boundary openers
        after = skip_ws(end_pos)
        is_boundary_opener = macro.endswith("_Boundary") or macro == "Boundary"

        if is_boundary_opener:
            args = _split_top_level_args(content)
            if args:
                alias = _normalize_id(args[0])
                label = _strip_quotes(args[1]) if len(args) > 1 else alias
                label = label.strip().strip('"').strip()
                btype = _classify_boundary_type(macro)
                parent = current_boundary()
                b = Boundary(id=alias, label=label, type=btype, parent=parent, level=None)
                boundaries[alias] = b
                if alias not in node_order:
                    node_order.append(alias)
                # Expect a { soon. If present, push.
                if after < n and cleaned[after] == "{":
                    boundary_stack.append(alias)
                    # skip the {
                    end_pos = after + 1
                else:
                    # Some authors put { on next line; we will catch via between logic on next iteration
                    # For robustness, if next non-ws non-comment char is {, consume it.
                    j = after
                    while j < n and cleaned[j] in " \t\r\n'":
                        if cleaned[j] == "'":
                            # skip to end of line
                            while j < n and cleaned[j] != "\n":
                                j += 1
                        j += 1
                    if j < n and cleaned[j] == "{":
                        boundary_stack.append(alias)
                        end_pos = j + 1

        elif macro in ELEMENT_MACROS:
            args = _split_top_level_args(content)
            if args:
                alias = _normalize_id(args[0])
                label = _strip_quotes(args[1]) if len(args) > 1 else alias
                label = label.strip().strip('"').strip()
                ntype, is_ext = _classify_node_type(macro)
                # C4-PlantUML arg order is inconsistent:
                #   System*/Person: (alias, label, [descr, [tech]])
                #   Container*/Component*: (alias, label, [tech, [descr]])
                description = ""
                technology = ""
                if len(args) > 2:
                    a2 = _strip_quotes(args[2])
                    raw_a3 = args[3] if len(args) > 3 else ""
                    a3 = _strip_quotes(raw_a3) if not raw_a3.strip().startswith("$") else ""
                    if ntype.startswith("Container") or ntype.startswith("Component"):
                        technology = a2
                        description = a3
                    else:
                        description = a2
                        technology = a3
                tags = _parse_tags(content)
                # Final aggressive cleanup (some diagrams produce stray quote chars)
                description = (description or "").strip().strip('"').strip()
                technology = (technology or "").strip().strip('"').strip()
                node = Node(
                    id=alias,
                    type=ntype,
                    label=label,
                    description=description,
                    technology=technology,
                    tags=tags,
                    boundary=current_boundary(),
                    is_external=is_ext,
                )
                nodes[alias] = node
                _record_node_order(alias)
                _record_child(current_boundary(), alias)

        elif macro in REL_MACROS:
            args = _split_top_level_args(content)
            if len(args) >= 2:
                src = _normalize_id(args[0])
                tgt = _normalize_id(args[1])
                label = _strip_quotes(args[2]) if len(args) > 2 else ""
                label = label.strip().strip('"').strip()
                tech = _strip_quotes(args[3]) if len(args) > 3 and not args[3].strip().startswith("$") else ""
                tech = tech.strip().strip('"').strip()
                tags = _parse_tags(content)
                e = Edge(
                    source=src,
                    target=tgt,
                    label=label,
                    technology=tech,
                    tags=tags,
                    rel_macro=macro,
                )
                edges.append(e)
                _record_edge(e)

        # Also account for any closing braces that appear immediately after this statement
        after2 = skip_ws(end_pos)
        close_after = 0
        j = after2
        while j < n and cleaned[j] in " \t\r\n}":
            if cleaned[j] == "}":
                close_after += 1
            j += 1
        for _ in range(close_after):
            if boundary_stack:
                boundary_stack.pop()

        pos = max(end_pos, j if close_after else end_pos)

    # Any remaining closes at end of file
    # (already handled incrementally)

    # Post-process: attach children lists
    for node in list(nodes.values()):
        if node.boundary and node.boundary in boundaries:
            boundaries[node.boundary].children.append(node.id)

    # Level inference
    levels: set[str] = set()
    has_component = any(n.type in ("Component", "ComponentExt") for n in nodes.values())
    has_container = any(n.type.startswith("Container") for n in nodes.values())
    has_system_b = any(b.type == "System" for b in boundaries.values())
    has_container_b = any(b.type == "Container" for b in boundaries.values())

    if has_component or has_container_b:
        levels.add("C3")
    if has_container or has_system_b:
        levels.add("C2")
    if not levels:
        levels.add("C1")

    info.levels = sorted(levels)

    for b in boundaries.values():
        if b.type == "System":
            b.level = "C1"
        elif b.type == "Container":
            b.level = "C2"
        elif b.type == "Component":
            b.level = "C3"

    # If we didn't capture child orders via the live mechanism, backfill from current children (best effort)
    for bid, b in boundaries.items():
        if bid not in boundary_child_order or not boundary_child_order[bid]:
            boundary_child_order[bid] = list(b.children)

    return C4Diagram(
        info=info,
        nodes=nodes,
        edges=edges,
        boundaries=boundaries,
        source_text=text,
        node_order=node_order,
        edge_order=edge_keys,
        boundary_child_order=boundary_child_order,
    )


def parse_file(path: str) -> C4Diagram:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return parse_text(text, filename=path)
