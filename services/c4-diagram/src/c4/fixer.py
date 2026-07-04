"""C4 Auto-Fix Engine.

Applies deterministic transformations for violations.
Returns a (possibly modified) C4Diagram and the list of fixes applied.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from .ir import (
    CANONICAL_NAMES,
    C4Diagram,
    Edge,
    Node,
    Violation,
)


@dataclass
class FixResult:
    diagram: C4Diagram
    fixes_applied: list[dict] = field(default_factory=list)
    # High-level summary
    summary: dict[str, Any] = field(default_factory=dict)


def _norm(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _is_app_node(n: Node) -> bool:
    nid = _norm(n.id) + _norm(n.label)
    return "modelmanagement" in nid or nid in {"app", "application", "workloads"}


def _is_loki(n: Node) -> bool:
    return "loki" in _norm(n.id) + _norm(n.label)


def _is_grafana(n: Node) -> bool:
    return "grafana" in _norm(n.id) + _norm(n.label)


def _is_prom(n: Node) -> bool:
    return "prometheus" in _norm(n.id) + _norm(n.label)


def _find_or_create_observability_boundary(d: C4Diagram) -> str:
    """Ensure an ObservabilityPlatform boundary exists at top level. Return its id."""
    for bid, b in d.boundaries.items():
        if "observab" in _norm(bid) + _norm(b.label):
            return bid
    # Create a new one
    obs_id = "ObservabilityPlatform"
    from .ir import Boundary
    b = Boundary(id=obs_id, label="Observability Platform", type="System", level="C2")
    d.boundaries[obs_id] = b
    return obs_id


def _move_node_to_boundary(d: C4Diagram, node_id: str, target_boundary_id: str) -> bool:
    node = d.nodes.get(node_id)
    if not node:
        return False
    # Remove from old boundary children list
    if node.boundary and node.boundary in d.boundaries:
        old = d.boundaries[node.boundary]
        if node_id in old.children:
            old.children.remove(node_id)
    # Move
    node.boundary = target_boundary_id
    if target_boundary_id in d.boundaries:
        d.boundaries[target_boundary_id].children.append(node_id)
    else:
        # If target did not exist as proper boundary, just set it (degenerate case)
        pass
    return True


def _normalize_node_name(node: Node) -> bool:
    """Apply canonical naming to label if a match is known. Returns True if changed.
    Only for coarse elements; never mangle internal component stages.
    """
    COARSE = {"Person", "System", "SystemExt", "SystemDb", "SystemDbExt",
              "Container", "ContainerExt", "ContainerDb", "ContainerDbExt", "ContainerQueue"}
    if node.type not in COARSE:
        return False

    label_norm = _norm(node.label)
    id_norm = _norm(node.id)

    # Avoid renaming things that look like internal stages
    stage = ("output", "datasource", "ds", "input", "parser", "enricher", "buffer")
    if any(s in label_norm or s in id_norm for s in stage):
        return False

    for key in (label_norm, id_norm):
        if key in CANONICAL_NAMES:
            canon = CANONICAL_NAMES[key]
            if node.label != canon:
                node.label = canon
                return True
    return False


def _reverse_edge(e: Edge) -> None:
    e.source, e.target = e.target, e.source
    if e.label:
        # Best effort: invert language if obvious
        lab = e.label.lower()
        if "writes" in lab or "pushes" in lab or "ships" in lab:
            e.label = e.label.replace("writes", "is written by").replace("pushes", "is pushed by").replace("ships", "is shipped by")
        elif "pulls" in lab or "scrapes" in lab or "queries" in lab:
            # often already correct direction for pull
            pass


def _remove_edge(d: C4Diagram, e: Edge) -> None:
    try:
        d.edges.remove(e)
    except ValueError:
        # try by value match
        d.edges = [x for x in d.edges if not (x.source == e.source and x.target == e.target and x.label == e.label)]


def _insert_log_agent_if_missing(d: C4Diagram, app_node: Node, loki_node: Node) -> tuple[bool, str | None]:
    """Insert a LogAgent node and reroute App->Loki to App->LogAgent->Loki. Return (changed, agent_id)."""
    # Find if an agent already exists
    agent = None
    for n in d.nodes.values():
        if _norm(n.id) in {"logagent", "logagent"} or "log agent" in _norm(n.label):
            agent = n
            break

    created = False
    if not agent:
        from .ir import Node
        agent = Node(
            id="LogAgent",
            type="Container",
            label="Log Agent",
            description="Tails stdout/stderr, enriches labels, buffers, retries, pushes to Loki.",
            technology="Fluent Bit / Vector",
            boundary=None,  # will place in ObservabilityPlatform if present
        )
        d.nodes[agent.id] = agent
        created = True

    # Place agent in ObservabilityPlatform if we can
    obs = None
    for bid, b in d.boundaries.items():
        if "observab" in _norm(bid) + _norm(b.label):
            obs = bid
            break
    if obs:
        agent.boundary = obs
        if agent.id not in d.boundaries[obs].children:
            d.boundaries[obs].children.append(agent.id)

    # If there is a direct edge app -> loki, remove or keep and add via agent
    # Strategy: keep original for now, insert two new correct edges
    # Remove direct app->loki if present
    direct_edges = [e for e in d.edges if e.source == app_node.id and e.target == loki_node.id]
    for de in direct_edges:
        _remove_edge(d, de)

    # Insert App -> Runtime (stdout) if not present (defensive)
    # Insert LogAgent -> Loki
    has_agent_loki = any(
        e.source == agent.id and _is_loki(d.nodes.get(e.target) or type("tmp", (), {"label": ""})())
        for e in d.edges
    )

    if not any(e.source == agent.id and e.target == loki_node.id for e in d.edges):
        d.edges.append(Edge(
            source=agent.id,
            target=loki_node.id,
            label="pushes logs via HTTP API",
            technology="POST /loki/api/v1/push",
        ))

    # App should go to ContainerRuntime (stdout)
    # If no runtime node, we cannot invent one reliably here.
    # Ensure an edge from agent to runtime exists conceptually (best effort)
    runtime_id = None
    for nid, n in d.nodes.items():
        if "containerruntime" in _norm(nid) + _norm(n.label):
            runtime_id = nid
            break

    if runtime_id and not any(e.source == agent.id and e.target == runtime_id for e in d.edges):
        d.edges.append(Edge(
            source=agent.id,
            target=runtime_id,
            label="tails stdout/stderr streams",
            technology="CRI / journald / files",
        ))

    # Make sure App writes only to runtime (if we have it)
    if runtime_id and not any(e.source == app_node.id and e.target == runtime_id for e in d.edges):
        d.edges.append(Edge(
            source=app_node.id,
            target=runtime_id,
            label="writes structured logs to stdout/stderr",
            technology="stdout/stderr only",
        ))

    return True, agent.id


def apply_fixes(diagram: C4Diagram, violations: list[Violation]) -> FixResult:
    """Apply as many deterministic fixes as possible. Idempotent where reasonable."""
    d = copy.deepcopy(diagram)
    applied: list[dict] = []

    # Collect actionable violations
    for v in violations:
        action = v.fix_action or {}

        # NAME-001 normalize
        if v.rule_id == "NAME-001" and v.node:
            node = d.nodes.get(v.node)
            if node and _normalize_node_name(node):
                applied.append({
                    "type": "normalize_name",
                    "rule": v.rule_id,
                    "node": v.node,
                    "new_label": node.label,
                })

        # FLOW-001: reverse bad edges or delete direct app->observability
        if v.rule_id == "FLOW-001" and v.edge:
            src, tgt = v.edge
            for e in list(d.edges):
                if e.source == src and e.target == tgt:
                    # For critical flow errors we prefer to remove the bad direction
                    # or reverse when semantically a read was intended.
                    if "grafana" in _norm(src):
                        # Grafana should read, not write. Remove.
                        _remove_edge(d, e)
                        applied.append({"type": "remove_edge", "rule": v.rule_id, "edge": [src, tgt]})
                    else:
                        # Default: remove the push/write edge. Correct path is via agent or pull.
                        _remove_edge(d, e)
                        applied.append({"type": "remove_edge", "rule": v.rule_id, "edge": [src, tgt]})

        # OWN-002: insert LogAgent when direct App->Loki
        if v.rule_id == "OWN-002" and v.edge:
            src, tgt = v.edge
            app = d.nodes.get(src)
            loki = d.nodes.get(tgt)
            if app and loki and _is_app_node(app) and _is_loki(loki):
                changed, agent_id = _insert_log_agent_if_missing(d, app, loki)
                if changed:
                    applied.append({
                        "type": "insert_log_agent",
                        "rule": v.rule_id,
                        "app": src,
                        "loki": tgt,
                        "agent": agent_id,
                    })

        # BND-001: move observability nodes out of app boundary
        if v.rule_id == "BND-001" and v.node:
            node = d.nodes.get(v.node)
            if node and _looks_like_observability_node(node):
                obs_id = _find_or_create_observability_boundary(d)
                if _move_node_to_boundary(d, v.node, obs_id):
                    applied.append({
                        "type": "move_node",
                        "rule": v.rule_id,
                        "node": v.node,
                        "to_boundary": obs_id,
                    })

    # Additional global passes
    # 1) Normalize all names we can (coarse elements only)
    for n in d.nodes.values():
        if _normalize_node_name(n):
            applied.append({"type": "normalize_name", "node": n.id, "new_label": n.label})

    # 2) Ensure no App->Loki/Prom/Graf direct edges remain (sweep)
    for e in list(d.edges):
        srcn = d.nodes.get(e.source)
        tgtn = d.nodes.get(e.target)
        if srcn and tgtn:
            if _is_app_node(srcn) and (_is_loki(tgtn) or _is_prom(tgtn) or _is_grafana(tgtn)):
                _remove_edge(d, e)
                applied.append({"type": "remove_direct_app_to_obs", "edge": [e.source, e.target]})

    # Dedup applied
    seen = set()
    deduped = []
    for a in applied:
        key = str(a)
        if key not in seen:
            seen.add(key)
            deduped.append(a)

    result = FixResult(
        diagram=d,
        fixes_applied=deduped,
        summary={
            "total_fixes": len(deduped),
            "fix_types": sorted({a["type"] for a in deduped}),
        },
    )
    return result


def _looks_like_observability_node(n: Node) -> bool:
    s = _norm(n.id) + _norm(n.label)
    return any(x in s for x in ("loki", "prometheus", "grafana", "logagent"))
