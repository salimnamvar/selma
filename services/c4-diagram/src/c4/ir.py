"""C4 Intermediate Representation (IR).

Normalized graph model for validation and fixing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


NodeType = Literal[
    "Person",
    "System",
    "SystemExt",
    "SystemDb",
    "SystemDbExt",
    "Container",
    "ContainerExt",
    "ContainerDb",
    "ContainerDbExt",
    "ContainerQueue",
    "Component",
    "ComponentExt",
]

BoundaryType = Literal["System", "Container", "Component", "Generic"]


@dataclass
class Node:
    id: str
    type: NodeType
    label: str
    description: str = ""
    technology: str = ""
    tags: list[str] = field(default_factory=list)
    boundary: Optional[str] = None  # parent boundary id or None (top-level)
    is_external: bool = False


@dataclass
class Edge:
    source: str
    target: str
    label: str = ""
    technology: str = ""
    tags: list[str] = field(default_factory=list)
    # Original macro used (Rel, Rel_L, etc.) for round-tripping if needed
    rel_macro: str = "Rel"


@dataclass
class Boundary:
    id: str
    label: str
    type: BoundaryType = "Generic"
    children: list[str] = field(default_factory=list)  # node ids directly contained
    parent: Optional[str] = None
    # Inferred C4 level for the boundary content (C1/C2/C3)
    level: Optional[str] = None


@dataclass
class DiagramInfo:
    filename: str
    title: str = ""
    includes_c4: bool = False
    original_include: Optional[str] = None  # e.g. "C4_Context.puml"
    # Primary detected level(s). A diagram may be pure or mixed.
    levels: list[str] = field(default_factory=list)


@dataclass
class C4Diagram:
    info: DiagramInfo
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    boundaries: dict[str, Boundary] = field(default_factory=dict)
    # Raw original text (for diff/rewrite)
    source_text: str = ""
    # Preserve original declaration order for stable rewrites (minimal diffs)
    node_order: list[str] = field(default_factory=list)
    edge_order: list[tuple[str, str, str, str]] = field(default_factory=list)  # (src, tgt, label, tech) approx key
    boundary_child_order: dict[str, list[str]] = field(default_factory=dict)  # boundary_id -> ordered child node ids

    def get_nodes_in_boundary(self, boundary_id: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.boundary == boundary_id]

    def get_top_level_nodes(self) -> list[Node]:
        return [n for n in self.nodes.values() if n.boundary is None]

    def find_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def find_boundary_containing(self, node_id: str) -> Optional[Boundary]:
        node = self.nodes.get(node_id)
        if not node or not node.boundary:
            return None
        return self.boundaries.get(node.boundary)


@dataclass
class Violation:
    rule_id: str
    severity: str  # critical | high | medium
    type: str  # boundary | flow | ownership | naming | structure
    message: str
    node: Optional[str] = None
    edge: Optional[tuple[str, str]] = None  # (source, target)
    fix_suggestion: str = ""
    # For fix engine
    fix_action: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "type": self.type,
            "message": self.message,
            "node": self.node,
            "edge": list(self.edge) if self.edge else None,
            "fix_suggestion": self.fix_suggestion,
        }


# Canonical naming hints (for NAME-001 and OWNERSHIP)
CANONICAL_NAMES: dict[str, str] = {
    # App side
    "modelmanagement": "Model Management Application",
    "modelmanagementapp": "Model Management Application",
    "model management application": "Model Management Application",
    "model management service": "Model Management Service",
    "modelmanagementservice": "Model Management Service",
    # Logging
    "logagent": "Log Agent",
    "logagentoutput": "Log Agent",
    "log agent": "Log Agent",
    "fluentbit": "Log Agent",
    "vector": "Log Agent",
    # Observability
    "loki": "Loki",
    "lokioutput": "Loki",
    "lokidatasource": "Loki",
    "prometheus": "Prometheus",
    "prometheusdatasource": "Prometheus",
    "grafana": "Grafana",
    "grafanadatasource": "Grafana",
    "observabilityplatform": "Observability Platform",
    "observability platform": "Observability Platform",
    "observability service": "Observability Platform",
    "containerruntime": "Container Runtime",
    "container runtime": "Container Runtime",
}

# Names that indicate "application" workloads (for flow/boundary rules)
APP_NODE_HINTS = {
    "modelmanagementapp",
    "model management application",
    "modelmanagement",
    "app",
    "application",
    "workloads",
}

# Forbidden direct targets from apps (FLOW-001)
FORBIDDEN_APP_TARGETS = {"loki", "prometheus", "grafana"}

# Nodes that must be passive (BND-002)
PASSIVE_RUNTIME_HINTS = {"containerruntime", "container runtime", "kubernetes", "docker"}

# Observability internal nodes that must not live inside app boundaries (BND-001)
OBSERVABILITY_IN_APP_FORBIDDEN = {"loki", "prometheus", "grafana", "logagent"}

# Log ownership
LOG_AGENT_HINTS = {"logagent", "log agent"}
LOG_TAIL_VERBS = {"tail", "tails", "ship", "buffer", "buffers", "enrich"}
APP_BAD_LOG_VERBS = {"tail", "tails", "buffer", "buffers", "ship", "ships", "push logs", "pushes logs"}
