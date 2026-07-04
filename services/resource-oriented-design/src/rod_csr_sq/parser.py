"""Parser for RoD-CSR-SQ combined analysis.

Extracts CSR layer info, RoD method/resource info, and SQ structural info from PlantUML files.
"""
from __future__ import annotations

import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from design_common.puml import load_basic_diagram, strip_puml_comments

from .ir import CSRAnalysis, RoDAnalysis, SQStructureAnalysis, RodCsrSqDiagram


PARTICIPANT_RE = re.compile(
    r'(?:participant|actor|boundary|control|entity|database|collections)\s+'
    r'["\']?([^"\']+)["\']?',
    re.IGNORECASE,
)
ACTOR_RE = re.compile(r'\bactor\b', re.IGNORECASE)
MESSAGE_RE = re.compile(r'(\w+)\s*(?:->|-->>|->>)\s*(\w+)\s*:\s*(.+)', re.IGNORECASE)
ACTIVATE_RE = re.compile(r'\b(activate|deactivate)\s+(\w+)', re.IGNORECASE)
REF_RE = re.compile(r'ref\s+(?:over\s+)?[^:]*:\s*([A-Z]{2,5}-\d{2,})', re.IGNORECASE)
NOTE_RE = re.compile(r'note\s+(?:over|left|right)\s+[^:]*:\s*\n?(.*?)(?:end\s+note|\Z)', re.IGNORECASE | re.DOTALL)
HTTP_VERB_RE = re.compile(r'\b(GET|POST|PATCH|PUT|DELETE)\s+/v?1?/', re.IGNORECASE)
RESOURCE_NAME_RE = re.compile(r'(?:name|resource)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
PAGE_SIZE_RE = re.compile(r'page_size|pageSize|page_token|pageToken|nextPageToken|next_page_token', re.IGNORECASE)
UPDATE_MASK_RE = re.compile(r'update_mask|updateMask|fieldMask|field_mask', re.IGNORECASE)
STATE_TRANSITION_RE = re.compile(r'(?:state|transition)\s*[:=]\s*(\w+)\s*(?:→|->|to)\s*(\w+)', re.IGNORECASE)
SQL_RE = re.compile(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b', re.IGNORECASE)


def _extract_csr_analysis(source: str, participants: list[str]) -> CSRAnalysis:
    """Analyze CSR layer interactions from diagram source."""
    csr = CSRAnalysis()

    source_lower = source.lower()

    # Detect actors
    csr.has_actor = bool(ACTOR_RE.search(source))
    for kw in ["user", "developer", "operator", "httpclient", "mcp client", "http client"]:
        if kw in source_lower:
            csr.actor_name = kw
            break

    # Detect CSR participants
    participant_lower = " ".join(p.lower() for p in participants)
    csr.has_controller = any(k in participant_lower for k in [
        "controller", "router", "ctrl", "apischema", "argparser",
        "slashcommandhandler", "serverapp", "serverrouter", "renderer",
    ])
    csr.has_service = any(k in participant_lower for k in [
        "service", "svc", "orchestrator", "agentorchestrator",
        "renderer", "metricscollector", "mcpdiscovery", "mcpcontroller",
        "configloader", "pipelineorchestrator", "safetycoordinator",
        "contextgraph", "contextprioritizer", "tokenbudgettracker",
        "toolregistry", "hookmanager", "pluginloader", "providerfactory",
        "modelrouter", "fallbackchain", "sandboxexecutor", "memorystore",
        "memoryscope", "memoryindex", "structuredlogger", "logredactor",
        "tracecorrelator", "dualoutputadapter", "wirelog", "wireappender",
        "strategyselector", "editsuccesschecker", "shellrunner",
        "permissiongate", "approvalgate", "sandboxpolicy",
    ])
    csr.has_repository = any(k in participant_lower for k in [
        "repository", "repo", "store", "database", "db", "persistence",
        "adapter", "gateway", "cache", "registry", "filesystem", "fs",
        "sandbox runtime", "host filesystem", "git repository", "git",
        "session directory", "global yaml", "project yaml", "env vars",
        "stdout", "stderr", "mcp server", "conversationhistory",
        "memoryindex", "symbolgraph", "sessionsearch", "fts5",
        "memorystore", "memoryscope", "configloader", "errorboundary",
        "toolregistry", "hookmanager", "pluginloader", "providerfactory",
        "injectionscanner", "egressinspector", "permissiongate",
        "slashcommandhandler", "modelrouter", "fallbackchain",
        "providercapabilities", "safetycoordinator",
    ])

    # Detect infrastructure-access pattern:
    # When there is NO service layer but Controller→Repository/Infrastructure calls exist
    # OR the diagram explicitly declares @csr-exempt service in header
    csr.is_infra_access = False

    # Check explicit header exemption first — overrides all auto-detection
    if re.search(r"'?\s*@csr-exempt\s+service", source, re.IGNORECASE):
        csr.is_infra_access = True
    elif not csr.has_service:
        # Auto-detect: if controller talks to repository/infra without service
        if csr.has_controller and csr.has_repository and csr.controller_to_repo_calls:
            csr.is_infra_access = True
    csr.has_database = any(k in participant_lower for k in ["database", "db", "postgresql", "mysql", "mongo"])

    # Detect forbidden controller→repo calls
    for m in MESSAGE_RE.finditer(source):
        src, dst, msg = m.group(1), m.group(2), m.group(3)
        src_lower = src.lower()
        dst_lower = dst.lower()
        if any(k in src_lower for k in ["controller", "router", "ctrl"]) and \
           any(k in dst_lower for k in ["repository", "repo", "store"]):
            csr.controller_to_repo_calls.append(msg.strip())

    # Detect repo→service calls (forbidden)
    for m in MESSAGE_RE.finditer(source):
        src, dst, msg = m.group(1), m.group(2), m.group(3)
        src_lower = src.lower()
        dst_lower = dst.lower()
        if any(k in src_lower for k in ["repository", "repo", "store"]) and \
           any(k in dst_lower for k in ["service", "svc"]):
            csr.repo_to_service_calls.append(msg.strip())

    # Detect validation phases
    if "validate" in source_lower or "validation" in source_lower:
        csr.validation_phases.append("validation_detected")

    # Detect DTO transformations
    if "dto" in source_lower or "->" in source and "DTO" in source:
        dto_matches = re.findall(r'(\w+DTO)', source)
        csr.dto_transformations.extend(dto_matches)

    return csr


def _extract_rod_analysis(source: str, title: str) -> RoDAnalysis:
    """Analyze RoD method/resource patterns from diagram source."""
    rod = RoDAnalysis()

    # Detect HTTP verb and URI
    verb_match = HTTP_VERB_RE.search(source)
    if verb_match:
        rod.http_verb = verb_match.group(1).upper()

    # Detect method type from title or source
    title_lower = title.lower()
    source_lower = source.lower()

    # Standard CRUD methods
    for method in ["create", "get", "list", "update", "delete"]:
        if method in title_lower:
            rod.method_type = method.capitalize()
            break

    # Custom methods (state transitions, domain actions)
    if not rod.method_type:
        custom_methods = [
            "cancel", "approve", "activate", "rollback", "publish", "archive",
            "process", "select", "dispatch", "register", "load", "stream",
            "record", "correlate", "export", "expose", "redact", "connect",
            "discover", "adapt", "index", "build", "rank", "inject", "embed",
            "search", "compact", "distill", "track", "enable", "disable",
            "validate", "apply", "stage", "check", "coordinate", "detect",
            "persist", "recall", "scope", "restore", "snapshot", "revert",
            "branch", "fetch", "grep", "glob", "find", "spawn", "append",
            "seek", "fork", "checkpoint", "isolate", "limit", "monitor",
            "request", "prompt", "switch", "queue", "delegate", "handle",
            "wrap", "render", "format",
        ]
        for method in custom_methods:
            if method in title_lower:
                rod.method_type = "Custom"
                rod.custom_method_name = method
                break

    # If still no method type, check if there's a UC_ID pattern in title
    if not rod.method_type and re.search(r'[A-Z]{2,5}-\d{2,}', title):
        rod.method_type = "Custom"

    # Detect pagination
    rod.has_pagination = bool(PAGE_SIZE_RE.search(source))

    # Detect update mask
    rod.has_update_mask = bool(UPDATE_MASK_RE.search(source))

    # Detect state transitions
    state_match = STATE_TRANSITION_RE.search(source)
    if state_match:
        rod.has_state_transition = True
        rod.state_from = state_match.group(1)
        rod.state_to = state_match.group(2)

    # Detect resource names in messages
    for m in RESOURCE_NAME_RE.finditer(source):
        rod.resource_names_in_messages.append(m.group(1))

    # Detect method names in service calls
    for m in MESSAGE_RE.finditer(source):
        src, dst, msg = m.group(1), m.group(2), m.group(3)
        dst_lower = dst.lower()
        if any(k in dst_lower for k in ["service", "svc"]):
            rod.method_names_in_service_calls.append(msg.strip())

    # Detect verb-as-path anti-patterns
    for m in re.finditer(r'(?:POST|GET|PUT|PATCH|DELETE)\s+/v?\d*/([\w/]+)', source):
        path = m.group(1)
        verbs = {"do", "run", "process", "handle", "execute", "perform", "activate", "set"}
        parts = path.split("/")
        if parts and parts[-1].lower() in verbs:
            rod.verb_as_path.append(path)

    return rod


def _extract_sq_structure(source: str) -> SQStructureAnalysis:
    """Analyze SQ diagram structural elements."""
    sq = SQStructureAnalysis()

    source_lower = source.lower()

    # Detect intro and summary notes
    notes = re.findall(r'note\s+(?:over|left|right)\s+[^:]*\n(.*?)(?:end\s+note)', source, re.DOTALL | re.IGNORECASE)
    for note in notes:
        note_lower = note.lower()
        if "scope:" in note_lower:
            sq.has_intro_note = True
            for field in ["scope", "preconditions", "contexts", "excludes", "rollback", "design", "returns"]:
                if field + ":" in note_lower:
                    sq.intro_fields.append(field)
        if "flow:" in note_lower:
            sq.has_summary_note = True
            for field in ["flow", "state", "success", "failure"]:
                if field + ":" in note_lower:
                    sq.summary_fields.append(field)

    # Detect activation bars
    sq.has_activation_bars = bool(ACTIVATE_RE.search(source))

    # Detect failure paths
    if "break" in source_lower:
        sq.failure_paths.append("break_blocks_detected")
    if "alt" in source_lower:
        sq.failure_paths.append("alt_blocks_detected")

    # Detect HTTP codes on returns
    http_code_re = re.compile(r'-->\s*\w+\s*:\s*\d{3}\s', re.IGNORECASE)
    sq.http_codes_on_returns = [m.group(0).strip() for m in http_code_re.finditer(source)]

    # Detect ref targets
    for m in REF_RE.finditer(source):
        sq.ref_targets.append(m.group(1))

    return sq


def parse_rod_csr_sq(path: str | Path) -> RodCsrSqDiagram:
    """Parse a PlantUML file into a combined RoD-CSR-SQ analysis."""
    p = Path(path)
    basic = load_basic_diagram(p)
    cleaned = strip_puml_comments(basic.source)

    # Extract title: prefer 'title' keyword, fallback to comment header
    title = basic.title
    if not title or title.startswith("actor ") or title.startswith("participant "):
        # Try to extract from comment header
        title_match = re.search(r"^'\s*Title:\s*(.+)$", basic.source, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Try to extract from @startuml line
            start_match = re.search(r"@startuml\s+(.+)$", basic.source, re.MULTILINE)
            if start_match:
                title = start_match.group(1).strip()

    # Check for @csr-exempt in original source (before comment stripping)
    has_csr_exempt = bool(re.search(r"'?\s*@csr-exempt\s+service", basic.source))

    participants = [m.group(1).strip() for m in PARTICIPANT_RE.finditer(cleaned)]

    messages = []
    for m in MESSAGE_RE.finditer(cleaned):
        messages.append(f"{m.group(1)} -> {m.group(2)}: {m.group(3).strip()}")

    return RodCsrSqDiagram(
        filename=str(p),
        source=cleaned,
        title=title,
        csr=_extract_csr_analysis(cleaned, participants),
        rod=_extract_rod_analysis(cleaned, title),
        sq=_extract_sq_structure(cleaned),
        raw_participants=participants,
        raw_messages=messages,
    )
