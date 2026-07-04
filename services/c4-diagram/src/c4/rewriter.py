"""C4 Diagram Rewriter.

Emits corrected PlantUML source from the (fixed) IR.
The output is deterministic and valid C4-PlantUML.
It does not attempt 100% fidelity to original formatting.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .ir import Boundary, C4Diagram, Edge, Node


def _esc(s: str) -> str:
    # Escape double quotes inside labels for PlantUML
    if s is None:
        return ""
    return s.replace('"', '\\"')


def _render_node(n: Node) -> str:
    alias = n.id
    label = _esc(n.label)
    descr = _esc(n.description) if n.description else ""
    tech = _esc(n.technology) if n.technology else ""

    if n.type == "Person":
        if descr:
            return f'Person({alias}, "{label}", "{descr}")'
        return f'Person({alias}, "{label}")'

    if n.type in ("System", "SystemExt"):
        macro = "System_Ext" if n.is_external or n.type == "SystemExt" else "System"
        if tech and descr:
            return f'{macro}({alias}, "{label}", "{descr}", "{tech}")'
        if descr:
            return f'{macro}({alias}, "{label}", "{descr}")'
        return f'{macro}({alias}, "{label}")'

    if n.type in ("SystemDb", "SystemDbExt"):
        macro = "SystemDb_Ext" if n.is_external or n.type == "SystemDbExt" else "SystemDb"
        if tech and descr:
            return f'{macro}({alias}, "{label}", "{descr}", "{tech}")'
        if descr:
            return f'{macro}({alias}, "{label}", "{descr}")'
        return f'{macro}({alias}, "{label}")'

    if n.type == "Container":
        if tech and descr:
            return f'Container({alias}, "{label}", "{tech}", "{descr}")'
        if tech:
            return f'Container({alias}, "{label}", "{tech}")'
        return f'Container({alias}, "{label}")'

    if n.type == "ContainerExt":
        if tech and descr:
            return f'Container_Ext({alias}, "{label}", "{tech}", "{descr}")'
        if tech:
            return f'Container_Ext({alias}, "{label}", "{tech}")'
        return f'Container_Ext({alias}, "{label}")'

    if n.type == "ContainerDb":
        if tech and descr:
            return f'ContainerDb({alias}, "{label}", "{tech}", "{descr}")'
        if tech:
            return f'ContainerDb({alias}, "{label}", "{tech}")'
        return f'ContainerDb({alias}, "{label}")'

    if n.type == "ContainerDbExt":
        if tech and descr:
            return f'ContainerDb_Ext({alias}, "{label}", "{tech}", "{descr}")'
        if tech:
            return f'ContainerDb_Ext({alias}, "{label}", "{tech}")'
        return f'ContainerDb_Ext({alias}, "{label}")'

    if n.type == "ContainerQueue":
        if tech and descr:
            return f'ContainerQueue({alias}, "{label}", "{tech}", "{descr}")'
        if tech:
            return f'ContainerQueue({alias}, "{label}", "{tech}")'
        return f'ContainerQueue({alias}, "{label}")'

    if n.type == "Component":
        if tech and descr:
            return f'Component({alias}, "{label}", "{tech}", "{descr}")'
        if tech:
            return f'Component({alias}, "{label}", "{tech}")'
        return f'Component({alias}, "{label}")'

    if n.type == "ComponentExt":
        if tech and descr:
            return f'Component_Ext({alias}, "{label}", "{tech}", "{descr}")'
        if tech:
            return f'Component_Ext({alias}, "{label}", "{tech}")'
        return f'Component_Ext({alias}, "{label}")'

    # Fallback
    return f'System({alias}, "{label}")'


def _render_edge(e: Edge) -> str:
    macro = e.rel_macro or "Rel"
    src = e.source
    tgt = e.target
    label = _esc(e.label) if e.label else ""
    tech = _esc(e.technology) if e.technology else ""

    if tech and label:
        return f'{macro}({src}, {tgt}, "{label}", "{tech}")'
    if label:
        return f'{macro}({src}, {tgt}, "{label}")'
    return f'{macro}({src}, {tgt})'


def _topological_boundaries(boundaries: dict[str, Boundary]) -> list[str]:
    """Return boundary ids in order such that parents come before children."""
    # Simple Kahn-like for small graphs
    indeg: dict[str, int] = {bid: 0 for bid in boundaries}
    children: dict[str, list[str]] = {bid: [] for bid in boundaries}
    for bid, b in boundaries.items():
        if b.parent and b.parent in indeg:
            indeg[bid] += 1
            children[b.parent].append(bid)

    ready = [bid for bid, deg in indeg.items() if deg == 0]
    order: list[str] = []
    while ready:
        bid = ready.pop(0)
        order.append(bid)
        for ch in children.get(bid, []):
            indeg[ch] -= 1
            if indeg[ch] == 0:
                ready.append(ch)
    # Any remaining (cycles or orphans) append
    for bid in boundaries:
        if bid not in order:
            order.append(bid)
    return order


def rewrite_diagram(diagram: C4Diagram, include_header: bool = True, prefer_original_include: bool = True) -> str:
    """Produce corrected PlantUML text.

    Tries to preserve the original C4 include when possible and emits a clean,
    deterministic representation. For pure naming fixes the result is still
    semantically equivalent.
    """
    lines: list[str] = []

    if include_header:
        lines.append("@startuml")
        lines.append("")

    # Decide include - strongly prefer the original one the author used
    orig_inc = diagram.info.original_include
    levels = diagram.info.levels
    if prefer_original_include and orig_inc:
        inc = orig_inc
    else:
        if "C3" in levels:
            inc = "C4_Component.puml"
        elif "C2" in levels:
            inc = "C4_Container.puml"
        else:
            inc = "C4_Context.puml"

    lines.append(f"!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/{inc}")
    lines.append("")
    lines.append("LAYOUT_LEFT_RIGHT()")
    lines.append("LAYOUT_WITH_LEGEND()")
    lines.append("")

    title_line = f'title {diagram.info.title}' if diagram.info.title else f'title {Path(diagram.info.filename).name if diagram.info.filename else "C4 Diagram"}'
    lines.append(title_line)
    lines.append("")

    emitted_nodes: set[str] = set()
    emitted_boundaries: set[str] = set()

    # Helper: get children in original declaration order when available
    def _ordered_children(bid: str, child_ids: list[str]) -> list[Node]:
        order = diagram.boundary_child_order.get(bid) or []
        if order:
            ordered = [nid for nid in order if nid in child_ids]
            # append any that were missed
            for nid in child_ids:
                if nid not in ordered:
                    ordered.append(nid)
            return [diagram.nodes[nid] for nid in ordered if nid in diagram.nodes]
        # fallback: by node_order if present
        if diagram.node_order:
            pos = {nid: i for i, nid in enumerate(diagram.node_order)}
            return sorted(
                (diagram.nodes[nid] for nid in child_ids if nid in diagram.nodes),
                key=lambda n: pos.get(n.id, 9999),
            )
        return sorted((diagram.nodes[nid] for nid in child_ids if nid in diagram.nodes), key=lambda x: x.id)

    # Emit top level nodes (preserve appearance order)
    top_ids = [nid for nid in (diagram.node_order or []) if nid in diagram.nodes and diagram.nodes[nid].boundary is None]
    seen_top = set(top_ids)
    for nid in top_ids:
        n = diagram.nodes[nid]
        lines.append(_render_node(n))
        emitted_nodes.add(n.id)
    # any missed top level
    for n in (diagram.nodes.values()):
        if n.boundary is None and n.id not in emitted_nodes:
            lines.append(_render_node(n))
            emitted_nodes.add(n.id)

    ordered_bids = _topological_boundaries(diagram.boundaries)

    def emit_boundary(bid: str, indent: int = 0) -> None:
        b = diagram.boundaries.get(bid)
        if not b or bid in emitted_boundaries:
            return
        emitted_boundaries.add(bid)
        pad = "    " * indent

        if b.type == "System":
            lines.append(f'{pad}System_Boundary({bid}, "{_esc(b.label)}") {{')
        elif b.type == "Container":
            lines.append(f'{pad}Container_Boundary({bid}, "{_esc(b.label)}") {{')
        else:
            lines.append(f'{pad}Boundary({bid}, "{_esc(b.label)}") {{')

        # Children in original order
        child_nids = [nid for nid in b.children if nid in diagram.nodes]
        for cn in _ordered_children(bid, child_nids):
            lines.append(("    " + pad) + _render_node(cn))
            emitted_nodes.add(cn.id)

        # Recurse into nested (keep topological for structure, but within siblings try node_order)
        nested = [nbid for nbid, nb in diagram.boundaries.items() if nb.parent == bid]
        if diagram.node_order:
            pos = {nid: i for i, nid in enumerate(diagram.node_order)}
            nested.sort(key=lambda x: pos.get(x, 9999))
        else:
            nested.sort()
        for nbid in nested:
            emit_boundary(nbid, indent + 1)

        lines.append(f"{pad}}}")
        lines.append("")

    for bid in ordered_bids:
        if diagram.boundaries[bid].parent is None:
            emit_boundary(bid, 0)

    # Any stragglers (top level or otherwise)
    for nid in (diagram.node_order or []):
        n = diagram.nodes.get(nid)
        if n and nid not in emitted_nodes:
            lines.append(_render_node(n))
            emitted_nodes.add(nid)
    for n in diagram.nodes.values():
        if n.id not in emitted_nodes:
            lines.append(_render_node(n))
            emitted_nodes.add(n.id)

    lines.append("")

    # Edges: try to preserve original relative order
    seen = set()
    rels_out = []
    # Build a position map from the parsed edge_order if available
    edge_pos = {key: i for i, key in enumerate(diagram.edge_order)} if diagram.edge_order else {}

    def _edge_key(e: Edge):
        return (e.source, e.target, e.label or "", e.technology or "")

    sorted_edges = sorted(diagram.edges, key=lambda e: edge_pos.get(_edge_key(e), 999999))
    for e in sorted_edges:
        key = _edge_key(e)
        if key in seen:
            continue
        seen.add(key)
        rels_out.append(_render_edge(e))

    for r in rels_out:
        lines.append(r)

    if include_header:
        lines.append("")
        lines.append("@enduml")

    return "\n".join(lines).rstrip() + "\n"
