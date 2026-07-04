"""C4 Validation Engine.

Deterministic rules per the C4 linter spec.
Bound to rules/selma/c4.md .
"""
from __future__ import annotations

import re
from typing import Iterable

from .ir import (
    APP_BAD_LOG_VERBS,
    APP_NODE_HINTS,
    CANONICAL_NAMES,
    FORBIDDEN_APP_TARGETS,
    LOG_AGENT_HINTS,
    OBSERVABILITY_IN_APP_FORBIDDEN,
    PASSIVE_RUNTIME_HINTS,
    C4Diagram,
    Violation,
)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _looks_like_app(node_id: str, label: str) -> bool:
    nid = _norm(node_id)
    nlabel = _norm(label)
    return nid in APP_NODE_HINTS or nlabel in APP_NODE_HINTS or "modelmanagement" in nid or "modelmanagement" in nlabel


def _looks_like_log_agent(node_id: str, label: str) -> bool:
    nid = _norm(node_id)
    nlabel = _norm(label)
    return nid in LOG_AGENT_HINTS or nlabel in LOG_AGENT_HINTS


def _looks_like_observability(name: str) -> bool:
    n = _norm(name)
    return n in {"loki", "prometheus", "grafana", "logagent"}


def _is_runtime(name: str) -> bool:
    n = _norm(name)
    return any(h in n for h in PASSIVE_RUNTIME_HINTS)


def _has_bad_log_verb(text: str) -> bool:
    t = text.lower()
    return any(v in t for v in APP_BAD_LOG_VERBS)


def _find_canonical(label: str, node_id: str) -> Optional[str]:
    key = _norm(label)
    if key in CANONICAL_NAMES:
        return CANONICAL_NAMES[key]
    key2 = _norm(node_id)
    if key2 in CANONICAL_NAMES:
        return CANONICAL_NAMES[key2]
    return None


def _get_all_nodes_in_tree(diagram: C4Diagram, boundary_id: str) -> list[str]:
    """Return node ids contained directly or indirectly under a boundary."""
    result = []
    direct = diagram.boundaries.get(boundary_id)
    if not direct:
        return result
    for nid in direct.children:
        result.append(nid)
    # children boundaries
    for bid, b in diagram.boundaries.items():
        if b.parent == boundary_id:
            result.extend(_get_all_nodes_in_tree(diagram, bid))
    return result


def validate(diagram: C4Diagram) -> list[Violation]:
    violations: list[Violation] = []

    # Precompute quick lookups
    node_list = list(diagram.nodes.values())
    edge_list = diagram.edges

    # ============================================================
    # RULE GROUP A — C4 STRUCTURE
    # ============================================================

    # C4-C1-001: Context diagram MUST NOT contain containers or components
    if "C1" in diagram.info.levels or not diagram.boundaries:
        # Heuristic: if diagram declares C1 or has no container/component nesting
        for n in node_list:
            if n.type in ("Container", "ContainerExt", "ContainerDb", "ContainerDbExt", "ContainerQueue",
                          "Component", "ComponentExt"):
                violations.append(Violation(
                    rule_id="C4-C1-001",
                    severity="critical",
                    type="structure",
                    message=f"Context-level diagram contains non-context element: {n.id} ({n.type})",
                    node=n.id,
                    fix_suggestion="Convert Container/Component to System/System_Ext (or move to proper C2/C3 diagram).",
                ))

    # C4-C2-001: Container diagram must not include components inside system boundary that are not deployable units
    # Heuristic: if we see Components directly under a System_Boundary (not under a Container_Boundary)
    for b in diagram.boundaries.values():
        if b.type == "System":
            for nid in b.children:
                n = diagram.nodes.get(nid)
                if n and n.type in ("Component", "ComponentExt"):
                    violations.append(Violation(
                        rule_id="C4-C2-001",
                        severity="high",
                        type="structure",
                        message=f"Component '{nid}' appears directly inside System boundary '{b.id}' (C2 should only contain Containers)",
                        node=nid,
                        fix_suggestion="Move component to a C3 diagram under its owning Container, or collapse description into the Container.",
                    ))

    # C4-C3-001: Component diagram must belong to exactly ONE container
    component_nodes = [n for n in node_list if n.type in ("Component", "ComponentExt")]
    if component_nodes:
        # Find all container-level boundaries present
        container_boundaries = {bid: b for bid, b in diagram.boundaries.items() if b.type == "Container"}

        def find_owning_container(node: "Node") -> str | None:
            # Walk up the boundary parent chain
            cur = node.boundary
            visited = set()
            while cur and cur not in visited:
                visited.add(cur)
                bb = diagram.boundaries.get(cur)
                if bb and bb.type == "Container":
                    return cur
                cur = bb.parent if bb else None
            # If no parent chain hit a Container, but there is exactly one Container_Boundary
            # in the whole diagram, assume these components belong to it (common pattern with
            # inner Boundary(subgroup) inside a single Container_Boundary).
            if len(container_boundaries) == 1:
                return next(iter(container_boundaries.keys()))
            return None

        owning = set()
        unscoped = []
        for n in component_nodes:
            owner = find_owning_container(n)
            if owner:
                owning.add(owner)
            else:
                unscoped.append(n.id)
                violations.append(Violation(
                    rule_id="C4-C3-001",
                    severity="high",
                    type="structure",
                    message=f"Component '{n.id}' is not inside any Container_Boundary",
                    node=n.id,
                    fix_suggestion="Wrap components inside exactly one Container_Boundary in the component diagram.",
                ))
        if len(owning) > 1:
            violations.append(Violation(
                rule_id="C4-C3-001",
                severity="high",
                type="structure",
                message=f"Components span multiple Container boundaries: {sorted(owning)}. A C3 diagram should belong to exactly one container.",
                fix_suggestion="Split into per-container C3 diagrams or re-scope boundaries.",
            ))

    # ============================================================
    # RULE GROUP B — BOUNDARY VALIDATION
    # ============================================================

    # BND-001: Observability tools cannot exist inside application boundary
    for bid, b in diagram.boundaries.items():
        bnorm = _norm(b.label) + _norm(bid)
        is_app_boundary = "workload" in bnorm or "application" in bnorm or "modelmanagement" in bnorm
        if not is_app_boundary:
            continue
        contained = _get_all_nodes_in_tree(diagram, bid)
        for nid in contained:
            n = diagram.nodes.get(nid)
            if n and _looks_like_observability(n.id) or _looks_like_observability(n.label):
                violations.append(Violation(
                    rule_id="BND-001",
                    severity="critical",
                    type="boundary",
                    message=f"Observability element '{n.id}' placed inside application/workload boundary '{bid}'",
                    node=n.id,
                    fix_suggestion="Move Loki/Prometheus/Grafana/LogAgent into ObservabilityPlatform (or equivalent) boundary.",
                ))

    # Also check top-level nodes directly inside wrong System_Boundary
    for n in node_list:
        if n.boundary:
            bb = diagram.boundaries.get(n.boundary)
            if bb and _norm(bb.label + bb.id) in {"workloads", "applicationworkloads", "modelmanagement"}:
                if _looks_like_observability(n.id) or _looks_like_observability(n.label):
                    violations.append(Violation(
                        rule_id="BND-001",
                        severity="critical",
                        type="boundary",
                        message=f"Observability element '{n.id}' inside app boundary",
                        node=n.id,
                        fix_suggestion="Move to ObservabilityPlatform boundary.",
                    ))

    # BND-002: Runtime systems are passive (ContainerRuntime should not act as active processor)
    for n in node_list:
        if _is_runtime(n.id) or _is_runtime(n.label):
            # Look for outgoing edges where runtime is source and looks like "processing"
            for e in edge_list:
                if e.source == n.id and e.label:
                    if any(word in e.label.lower() for word in ["process", "run", "execute", "handle", "orchestrate"]):
                        violations.append(Violation(
                            rule_id="BND-002",
                            severity="high",
                            type="boundary",
                            message=f"Runtime '{n.id}' appears to act as active processor",
                            node=n.id,
                            fix_suggestion="Mark ContainerRuntime as passive (System_Ext / Container_Ext). Remove processor semantics.",
                        ))

    # ============================================================
    # RULE GROUP C — FLOW DIRECTION (CRITICAL)
    # ============================================================

    for e in edge_list:
        src = diagram.find_node(e.source)
        tgt = diagram.find_node(e.target)
        src_label = (src.label if src else e.source).lower()
        tgt_label = (tgt.label if tgt else e.target).lower()
        src_norm = _norm(e.source) + _norm(src_label)
        tgt_norm = _norm(e.target) + _norm(tgt_label)

        # App -> Loki / Prometheus / Grafana direct is forbidden
        if _looks_like_app(e.source, src_label or ""):
            if any(f in tgt_norm for f in FORBIDDEN_APP_TARGETS):
                violations.append(Violation(
                    rule_id="FLOW-001",
                    severity="critical",
                    type="flow",
                    message=f"Invalid flow: application writes to observability store '{e.target}'",
                    edge=(e.source, e.target),
                    fix_suggestion="Route via LogAgent (for logs) or use pull scrape (for metrics). Reverse or remove edge.",
                ))

        # Grafana -> App writes forbidden
        if "grafana" in src_norm:
            if _looks_like_app(e.target, tgt_label or "") or "write" in e.label.lower() or "push" in e.label.lower():
                violations.append(Violation(
                    rule_id="FLOW-001",
                    severity="critical",
                    type="flow",
                    message=f"Invalid flow: Grafana writing to application '{e.target}'",
                    edge=(e.source, e.target),
                    fix_suggestion="Grafana must only query (read). Remove or reverse the edge.",
                ))

        # Loki/Prometheus -> App push forbidden
        if any(x in src_norm for x in ["loki", "prometheus"]):
            if _looks_like_app(e.target, tgt_label or ""):
                if "push" in e.label.lower() or "write" in e.label.lower() or not e.label:
                    violations.append(Violation(
                        rule_id="FLOW-001",
                        severity="critical",
                        type="flow",
                        message=f"Invalid flow: {e.source} pushing to application",
                        edge=(e.source, e.target),
                        fix_suggestion="Observability stores do not push to apps. Use pull or agent model. Remove edge.",
                    ))

    # ============================================================
    # RULE GROUP D — OWNERSHIP MODEL
    # ============================================================

    # OWN-001: App must NOT tail/buffer/ship logs (only real log flows)
    for e in edge_list:
        src = diagram.find_node(e.source)
        if src and _looks_like_app(e.source, src.label):
            lab = (e.label or "").lower()
            tgt_n = _norm(e.target) + _norm( (diagram.find_node(e.target).label if diagram.find_node(e.target) else "") )
            if _has_bad_log_verb(e.label):
                # require that the edge is actually about logging / observability target
                if any(k in lab for k in ("log", "stdout", "loki", "grafana", "prom")) or any(k in tgt_n for k in ("log", "loki", "observ")):
                    violations.append(Violation(
                        rule_id="OWN-001",
                        severity="high",
                        type="ownership",
                        message=f"Application '{e.source}' owns log shipping/tailing responsibility via '{e.label}'",
                        edge=(e.source, e.target),
                        fix_suggestion="Move responsibility to LogAgent. App should only write to stdout/stderr (ContainerRuntime).",
                    ))

    # OWN-002: If App -> Loki direct exists, LogAgent should be present and used
    has_direct_app_loki = False
    for e in edge_list:
        src = diagram.find_node(e.source)
        tgt = diagram.find_node(e.target)
        if _looks_like_app(e.source, src.label if src else "") and "loki" in _norm(e.target) + _norm(tgt.label if tgt else ""):
            has_direct_app_loki = True
            violations.append(Violation(
                rule_id="OWN-002",
                severity="high",
                type="ownership",
                message=f"Direct App to Loki edge without LogAgent mediation: {e.source} -> {e.target}",
                edge=(e.source, e.target),
                fix_suggestion="Insert LogAgent between application and Loki. LogAgent tails, enriches, buffers, pushes.",
            ))

    # Check that if a LogAgent node is declared, it actually does the right things (presence check on edges)
    # Only enforce in diagrams that are primarily about the workloads/overall logging flow, not
    # in the internal component diagrams of Loki itself or the agent sub-components.
    diagram_focus = _norm(diagram.info.title) + _norm(diagram.info.filename)
    is_agent_or_loki_component_diagram = "logagent" in diagram_focus or "loki" in diagram_focus or any(
        b.label and _norm(b.label) in {"log agent", "loki"} for b in diagram.boundaries.values()
    )

    log_agent_nodes = [n for n in node_list if _looks_like_log_agent(n.id, n.label)]
    if log_agent_nodes and not is_agent_or_loki_component_diagram:
        # Look for expected behavior edges from the agent
        agent_ids = {n.id for n in log_agent_nodes}
        agent_does_tail = False
        agent_does_push = False
        for e in edge_list:
            if e.source in agent_ids:
                lab = e.label.lower()
                if "tail" in lab or "cr i" in lab or "cri" in lab:
                    agent_does_tail = True
                if "push" in lab or "loki" in _norm(e.target):
                    agent_does_push = True
        if not agent_does_tail:
            violations.append(Violation(
                rule_id="OWN-002",
                severity="medium",
                type="ownership",
                message="LogAgent declared but no evidence of tailing stdout/stderr from runtime",
                fix_suggestion="Add edge from LogAgent to ContainerRuntime with 'tails stdout/stderr'.",
            ))
        if not agent_does_push:
            violations.append(Violation(
                rule_id="OWN-002",
                severity="medium",
                type="ownership",
                message="LogAgent declared but no evidence of pushing to Loki",
                fix_suggestion="Add edge from LogAgent to Loki with 'pushes logs'.",
            ))

    # ============================================================
    # RULE GROUP E — CONSISTENCY
    # ============================================================

    # NAME-001: Same *coarse-grained entity* must have consistent naming across diagrams.
    # We deliberately ignore Component-level plugin/output/datasource stages
    # (e.g. "Loki Output", "LokiDS", "PromDS") — they are not the external systems.
    COARSE_TYPES = {"Person", "System", "SystemExt", "SystemDb", "SystemDbExt",
                    "Container", "ContainerExt", "ContainerDb", "ContainerDbExt", "ContainerQueue"}

    def _is_coarse(n: "Node") -> bool:
        return n.type in COARSE_TYPES

    def _looks_like_internal_stage(label: str, nid: str) -> bool:
        s = _norm(label) + _norm(nid)
        stage_words = ("output", "datasource", "ds", "input", "tail", "parser", "enrich",
                       "buffer", "validator", "distributor", "query", "chunk", "compactor",
                       "alert", "dashboard")
        return any(w in s for w in stage_words)

    seen: dict[str, set[str]] = {}
    for n in node_list:
        if not _is_coarse(n):
            continue
        if _looks_like_internal_stage(n.label, n.id):
            continue
        canon = _find_canonical(n.label, n.id)
        if canon:
            seen.setdefault(canon, set()).add(n.label)
        # Only exact key matches
        for k, v in CANONICAL_NAMES.items():
            nk = _norm(n.id)
            nl = _norm(n.label)
            if k == nk or k == nl:
                seen.setdefault(v, set()).add(n.label or n.id)

    for canon, variants in seen.items():
        variants = set(variants)
        if len(variants) > 1:
            violations.append(Violation(
                rule_id="NAME-001",
                severity="medium",
                type="naming",
                message=f"Inconsistent naming for '{canon}': {sorted(variants)}",
                fix_suggestion=f"Use canonical name '{canon}' everywhere.",
            ))
        elif list(variants)[0] != canon:
            # Single use of a non-canonical label for a known entity
            bad = list(variants)[0]
            violations.append(Violation(
                rule_id="NAME-001",
                severity="medium",
                type="naming",
                message=f"Non-canonical name '{bad}' for '{canon}'",
                node=bad if bad in [nn.id for nn in node_list] else None,
                fix_suggestion=f"Use canonical name '{canon}'.",
            ))

    # Deduplicate identical violations (can happen from multiple checks)
    unique: dict[tuple, Violation] = {}
    for v in violations:
        key = (v.rule_id, v.node, v.edge, v.message[:80])
        if key not in unique:
            unique[key] = v
    return list(unique.values())
