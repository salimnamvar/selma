# Universal Rule Governance Specification

**Version:** 8.1.0  
**Status:** Draft Standard  
**Date:** 2026-07-05  
**Normative Source:** This document is the normative behavioral source for the Selma system.

---

## 1. Introduction

### 1.1 Purpose

This specification defines a universal framework for creating, maintaining, and enforcing rules across any domain. The system is built on **three runtime primitives**:

1. **Directive Graph** — The human-authored source-of-truth specification
2. **Compiled Control DAG (CG-IR)** — The immutable executable intermediate representation
3. **Finding Event Stream** — The append-only audit log with read-only analytics

### 1.2 Cross-Layer Binding Contract

The Selma system has three document layers with a strict dominance hierarchy:

| Layer | Document | Role | Authority |
| :--- | :--- | :--- | :--- |
| **Normative** | SPECIFICATION.md | Defines system behavior, invariants, and contracts | Highest — all other layers MUST conform |
| **Structural** | rule_schema.json | Structural projection of spec invariants | Derived from spec — MUST be valid JSON Schema encoding of spec |
| **Governance** | policy_doctrine.yaml | Governance intent description | Descriptive only — MUST NOT contradict spec invariants |

**Binding Rules:**
1. SPECIFICATION.md is the single normative source for all system behavior
2. rule_schema.json MUST be derivable from spec invariants — no schema element may contradict spec
3. policy_doctrine.yaml describes governance intent only — no executable fields
4. When spec and schema conflict, spec wins
5. Version synchronization is a compatibility matrix, not strict equality (see Section 5)
6. The engine validates schema against spec invariants at compile time

### 1.3 Scope

This standard applies to:
- Policy documents (prose rules, governance documents, standards)
- Machine-executable rules (automated enforcement, validation, compliance)
- Control derivation (translating directives into testable conditions)
- Inspection execution (evaluating targets against controls)
- Finding lifecycle (detection, disposition, remediation, closure)

---

## 2. Architecture

### 2.1 Three Runtime Primitives + Execution Artifact Layer

```
┌─────────────────────────────┐
│   1. Directive Graph        │
│   (source-of-truth spec)    │
└──────────────┬──────────────┘
               │ compile (hermetic boundary)
               ▼
┌─────────────────────────────┐
│   2. Compiled Control DAG   │
│   (= CG-IR)                 │
└──────────────┬──────────────┘
               │ evaluate (pure functions)
               ▼
┌─────────────────────────────┐
│   3. Finding Event Stream   │
│   - Append-only events      │
│   - Read-only analytics     │
│   - Mediated feedback       │
└──────────────┬──────────────┘
               │ serialize
               ▼
┌─────────────────────────────┐
│   4. Execution Artifacts    │
│   - Inspection snapshots    │
│   - System state hashes     │
│   - Pipeline traces         │
│   (immutable, reproducible) │
└─────────────────────────────┘
```

### 2.2 Canonical Identity Resolution

The identity model has two distinct ID types:

**Lineage ID (Immutable Root):**
- Assigned once at directive creation
- Never changes across revisions, forks, merges, or splits
- Used for audit trail and historical traceability
- Format: `^[A-Z][A-Z0-9]+-[0-9]+$` (e.g., `TRAF-001`)

**Execution ID (Active Node Identity):**
- May change on fork, merge, or split
- Used for CG-IR compilation and runtime evaluation
- Tracks the current active version of a directive
- Format: `^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$` (e.g., `TRAF-001-A`)

**Identity Mapping:**

| Layer | Lineage ID Field | Execution ID Field |
| :--- | :--- | :--- |
| Policy Doctrine | `Machine ID` → lineage_id | Not represented until fork/merge/split (then tracked in schema) |
| Rule Schema | `rule.lineage_id` | `rule.id` |
| CG-IR | `node.lineage_id` | `node.directive_id` |
| Finding | `finding.lineage_id` | `finding.control_id` → node |

**Invariant:** `rule.lineage_id` is immutable. `rule.id` is the active execution identity. On fork/merge/split, `rule.id` changes but `rule.lineage_id` is inherited from the parent.

**Lineage Tracking:**

```json
{
  "lineage_id": "TRAF-001",
  "id": "TRAF-001-A",
  "lineage": {
    "operation": "fork",
    "parent_lineage_ids": ["TRAF-001"],
    "parent_execution_ids": ["TRAF-001"],
    "timestamp": "2026-07-05T10:00:00Z"
  }
}
```

### 2.4 Canonical Transformation Pipeline

```
Policy Document (prose + directive tables)
    │
    │ Step 1: Parse directive tables
    │ Extract: Machine ID, Type, Description, Context
    ▼
Directive Graph (structured, versioned)
    │
    │ Step 2: Resolve identity
    │ Ensure Machine ID = rule.lineage_id (immutable root)
    │ Ensure rule.id = directive_id (active execution identity)
    │ Validate lineage (fork/merge/split)
    ▼
Rule Schema (machine-readable)
    │
    │ Step 3: Compile to CG-IR
    │ For each rule:
    │   - Generate control node
    │   - Attach pure evaluator
    │   - Resolve dependencies
    │   - Apply conflict resolution mapping
    │   - Pin frozen environment hash
    ▼
CG-IR (immutable snapshot)
    │
    │ Step 4: Evaluate targets
    │ Topological DAG execution with pure functions
    ▼
Finding Event Stream (append-only)
    │
    │ Step 5: Serialize execution artifacts
    │ Inspection snapshot, pipeline trace, system state hash
    ▼
Execution Artifacts (immutable, reproducible)
```

### 2.5 The Directive Graph

| Aspect | Description |
| :--- | :--- |
| **Format** | Structured document (YAML/JSON with prose sections) |
| **Versioning** | Semantic versioning (MAJOR.MINOR.PATCH) |
| **Mutability** | Mutable (new revisions created on change) |
| **Content** | Directives, scope, priority, prose sections, metadata |

### 2.6 The Compiled Control DAG (CG-IR)

| Aspect | Description |
| :--- | :--- |
| **Format** | Directed Acyclic Graph of control nodes |
| **Versioning** | Content-addressed (SHA-256 hash of snapshot) |
| **Mutability** | Immutable snapshots; compilation generates new snapshots |
| **Content** | Control nodes, edges, evaluation logic, provenance |

**CG-IR Snapshot vs Compilation Process:**

| Concept | Mutability | Description |
| :--- | :--- | :--- |
| **CG-IR Snapshot** | Immutable | A frozen, content-addressed instance of the DAG |
| **Compilation Process** | Transient | Generates a new snapshot; does not modify existing ones |

**Incremental Compilation:** The compilation process reuses unchanged subgraphs from previous snapshots, but the output is always a new, complete, immutable snapshot.

### 2.7 The Hermetic Compilation Boundary

```
Directive Graph
        │
        ▼ compile(frozen_env)
   ┌─────────────────────────────────────┐
   │     HERMETIC COMPILATION BOUNDARY   │
   │                                     │
   │  Frozen environment (all pinned):   │
   │  - Engine version                   │
   │  - Model weights (if AI-assisted)   │
   │  - System prompts (if AI-assisted)  │
   │  - Decoding parameters              │
   │  - Toolchain version                │
   │  - OS/runtime hash                  │
   │                                     │
   │  Output: CG-IR snapshot + provenance│
   └─────────────────────────────────────┘
```

**Hermeticity Rules:**
1. Compilation is reproducible only when the entire environment is frozen
2. The frozen environment hash is recorded in CG-IR provenance
3. To reproduce: pin all frozen_env dimensions
4. AI outputs are cached and serialized into CG-IR before publication
5. Once published, CG-IR snapshot is immutable

### 2.8 CG-IR Node Schema

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | String | Unique node identifier |
| `directive_id` | String | Canonical directive ID |
| `directive_revision` | String | Revision of source directive |
| `control_version` | String | Version of evaluation logic |
| `description` | String | Human-readable description |
| `evaluator` | Object | Pure evaluator specification |
| `scope` | Object | Applicability context |
| `severity_default` | Enum | Default severity on failure |
| `depends_on` | Array | Node IDs evaluated first |
| `status` | Enum | `active`, `deprecated` |

### 2.9 Formal Evaluator Contract

```
evaluate(node, target, context) → {
  outcome: Pass | Fail | Partial | NeedsReview,
  confidence: Float (0.0–1.0),
  evidence: String,
  reasoning: String
}
```

**Evaluator Constraints:**

| Constraint | Rule |
| :--- | :--- |
| **Purity** | No side effects. No network calls. No file I/O. No randomness. |
| **Determinism** | Same inputs → same outputs, always. |
| **Allowed operations** | String matching, regex, arithmetic, field extraction, comparison |
| **Prohibited operations** | HTTP calls, DB queries, file reads, environment variables |

**Evaluator Types (pure only):**

| Type | Description |
| :--- | :--- |
| `regex` | Pattern matching against target content |
| `field_check` | Validates specific fields in structured targets |
| `threshold` | Numeric comparison against configured limits |
| `composite` | Boolean combination of sub-evaluators |

### 2.10 Target Schema (Strict)

All targets must conform to:

```json
{
  "target_id": "string (required)",
  "target_type": "string (required, enum: [text, structured, binary])",
  "content_hash": "string (required, SHA-256)",
  "submitted_at": "datetime (required, ISO 8601, UTC)",
  "content": {
    "text": "string (for text targets)",
    "fields": "object (for structured targets)",
    "reference": "string (for binary targets, content-addressed)"
  },
  "metadata": {
    "domain": "string",
    "jurisdiction": "string",
    "format": "string"
  }
}
```

### 2.11 Context Object (Strict)

```json
{
  "target_metadata": {
    "target_id": "string",
    "target_type": "string",
    "content_hash": "string",
    "submitted_at": "datetime"
  },
  "domain_constants": {
    "domain": "string",
    "jurisdiction": "string",
    "scope_filters": "object"
  },
  "finding_aggregates": {
    "total_open_findings": "integer",
    "findings_by_severity": "object (enum keys: critical, high, medium, low, informational)",
    "findings_by_control": "object (control_id → count)",
    "last_inspection_date": "datetime",
    "recurrence_count": "integer"
  }
}
```

**No Write-Back:** Evaluators cannot modify context.

### 2.12 DAG Execution Semantics

| Aspect | Rule |
| :--- | :--- |
| **Evaluation Order** | Topological sort respecting `depends_on` |
| **Cycle Detection** | Enforced at compile time |
| **Parallel Execution** | Independent nodes execute in parallel |
| **State Propagation** | Read-only context; no shared mutable state |
| **Timeout** | Per-node configurable (default: 30s) |
| **Retry** | No retries; failed nodes → `NeedsReview` |

### 2.13 Inspection Consistency Model

An inspection produces a **point-in-time snapshot**:

| Aspect | Rule |
| :--- | :--- |
| **Snapshot** | Complete evaluation state at completion |
| **Partial execution** | Skipped nodes recorded; report marks partial results |
| **Report** | Consistent point-in-time view including partial results |
| **Reproducibility** | Same CG-IR + same target + same frozen_env = same snapshot |
| **Immutability** | Once completed, never modified |

### 2.14 Finding Event Stream

**Event Schema:**

```json
{
  "event_id": "string (required, UUID)",
  "finding_id": "string (required)",
  "event_type": "string (required, enum: [FindingCreated, DispositionChanged, FindingClosed])",
  "timestamp": "datetime (required, ISO 8601, UTC, event time)",
  "logical_clock": "object (required, hybrid logical clock)",
  "actor": "string (required, human ID or AI agent ID)",
  "payload": "object (event-specific data)",
  "event_hash": "string (required, SHA-256)"
}
```

**Hybrid Logical Clock (HLC):**

To handle distributed systems and clock skew, events use a Hybrid Logical Clock:

```json
{
  "logical_clock": {
    "physical_time": "datetime (wall clock, UTC)",
    "logical_counter": "integer (monotonic counter, starts at 0)",
    "node_id": "string (unique node identifier)"
  }
}
```

**Event Ordering:** Total ordering by `logical_clock`:
1. Compare `physical_time` first
2. If equal, compare `logical_counter`
3. If equal, compare `node_id` (lexicographic)
4. If all equal, compare `event_id` (lexicographic)

**HLC Clock Advancement (per node):**

```
on_local_event(physical_time_pt):
  l = max(l, last_logical_counter)
  if physical_time_pt > last_physical_time:
    last_physical_time = physical_time_pt
    last_logical_counter = 0
  else:
    last_logical_counter = last_logical_counter + 1
  emit { physical_time: last_physical_time, logical_counter: last_logical_counter, node_id }

on_receive_remote(remote_hlc):
  l = max(l, remote_hlc.logical_counter)
  if remote_hlc.physical_time > last_physical_time:
    last_physical_time = remote_hlc.physical_time
    last_logical_counter = remote_hlc.logical_counter
  else if remote_hlc.physical_time == last_physical_time:
    last_logical_counter = max(last_logical_counter, remote_hlc.logical_counter) + 1
  else:
    last_logical_counter = last_logical_counter + 1
```

**Monotonic Counter Rules:**
- `logical_counter` is a non-negative integer, initialized to 0 per node
- Counter resets to 0 only when `physical_time` advances strictly past the previous value
- Counter MUST NOT decrease; validation rejects regressive HLC tuples
- On node restart: load last persisted HLC state; if wall clock is behind persisted `physical_time`, retain persisted `physical_time` and increment `logical_counter`

**Multi-Node Reconciliation:**
- Each event carries the emitting node's HLC tuple; receivers apply `on_receive_remote` before appending
- Total order is reconstructed by sorting all events by the 4-level key (physical_time → logical_counter → node_id → event_id)
- Partition tolerance: nodes may diverge during partition; on heal, merged stream is re-sorted by total order key (no causal overwrite of committed events)
- Identical `node_id` with equal physical_time and logical_counter cannot occur from a single node; cross-node ties are broken by `node_id`, then `event_id`

**Event Immutability:** Once written, events are never modified. The `event_hash` ensures integrity.

**Read-Only Analytics:**

| Analytics | Description |
| :--- | :--- |
| `finding_aggregates` | Pre-computed for context object |
| `trend_analysis` | Finding rates over time (read-only) |
| `compliance_dashboard` | Real-time posture view |

**Mediated Feedback:**

```
Finding Event Stream → Read-only analytics → Human review → Directive Graph change → Recompile
```

### 2.15 Conflict Resolution Mapping

The declarative intent in policy is mapped to deterministic operators. **Explicit override takes precedence.**

| Intent (Policy) | Operator (CG-IR) | Implementation |
| :--- | :--- | :--- |
| "Higher priority wins" | `max(priority_level)` | Constitutional(1) > Statutory(2) > Regulatory(3) > Operational(4) > Advisory(5) |
| "More specific wins" | `specificity_score(rule_a) > specificity_score(rule_b)` | Count of scope constraints; higher = more specific |
| "Newer wins" | `max(created_at)` | ISO 8601 timestamp comparison |
| "Explicit override wins" | `has_field(conflict_resolution)` | Boolean: does rule have explicit override? Applied first, before computed factors |

**Cross-Layer Precedence Chain:**

| Layer | Role in Conflict Resolution |
| :--- | :--- |
| **Policy** | Declares governance intent (priority hierarchy, specificity preference, recency preference). No executable override fields. |
| **Schema** | Optional `conflict_resolution` field is a structural explicit override. Not an algorithm — a data carrier consumed by the engine. |
| **Spec (this document)** | Normative `resolve_conflict` algorithm. Explicit override checked first; computed resolution is deterministic fallback. |

**Unified Conflict Resolution Function:**

```
resolve_conflict(rule_a, rule_b) → winning_rule | Conflict Artifact

// Step 1: Explicit override takes precedence
1. if rule_a.conflict_resolution and not rule_b.conflict_resolution:
     return apply_strategy(rule_a.conflict_resolution, rule_a, rule_b)
2. if rule_b.conflict_resolution and not rule_a.conflict_resolution:
     return apply_strategy(rule_b.conflict_resolution, rule_b, rule_a)
3. if both have conflict_resolution:
     return Conflict Artifact (escalate — ambiguous override)

// Step 2: Computed resolution (when no explicit override)
4. if rule_a.priority != rule_b.priority:
     return rule with lower priority_level number
5. if specificity(rule_a) != specificity(rule_b):
     return rule with higher specificity score
6. if rule_a.created_at != rule_b.created_at:
     return rule with newer timestamp

// Step 3: Unresolvable
7. return Conflict Artifact (escalate to human)

apply_strategy(strategy, rule, other_rule) → winning_rule | Conflict Artifact:
  - "always_wins": return rule
  - "never_wins": return other_rule
  - "defer_to": 
      if target rule exists and is active:
        return rule with ID = strategy.defer_to
      else:
        return Conflict Artifact (target not found — fall through to computed resolution)

cycle_detection:
  If A defers_to B and B defers_to A → both overrides ignored → fall through to computed resolution
  If chain A → B → C → A → cycle detected → all overrides ignored → fall through to computed resolution

scope_boundary:
  Conflict resolution applies within same lineage_id.
  Cross-lineage conflicts are flagged as Conflict Artifacts for human review.
```

### 2.16 Deterministic Serialization Rules

For reproducibility, all hashing uses:

| Rule | Specification |
| :--- | :--- |
| **JSON key ordering** | Alphabetical (lexicographic) |
| **Number encoding** | Integer as integer, float as IEEE 754 double |
| **NaN/Infinity policy** | NOT permitted in serializable objects; validation rejects NaN/Infinity |
| **String encoding** | UTF-8, no BOM |
| **Datetime encoding** | ISO 8601 with UTC timezone (`YYYY-MM-DDTHH:MM:SSZ`) |
| **Null handling** | Explicit `null`, not omitted |
| **Array ordering** | Preserved as-is (insertion order) |
| **Float precision** | IEEE 754 double; no rounding before hashing |
| **Hash algorithm** | SHA-256 |

**Canonical JSON:** All objects are serialized with sorted keys before hashing.

**Recursive Structures:**
- **Composite evaluators:** `sub_evaluators` are serialized as an ordered array of canonical JSON objects
- **Lineage:** `parent_lineage_ids` and `parent_execution_ids` are sorted lexicographically before hashing
- **Schema references ($ref):** Resolved at schema validation time only; NOT included in canonical form for hashing
- **Map ordering:** Objects with `additionalProperties: true` have keys sorted lexicographically before hashing

**Evaluator Config Serialization by Type:**

| Type | Canonical Fields | Serialization |
| :--- | :--- | :--- |
| `regex` | `pattern`, `flags` | `{"flags":"","pattern":"..."}` (sorted keys) |
| `field_check` | `field`, `operator`, `value` | `{"field":"...","operator":"...","value":...}` |
| `threshold` | `field`, `operator`, `threshold` | `{"field":"...","operator":"...","threshold":...}` |
| `composite` | `logic`, `sub_evaluators` | Each sub_evaluator serialized recursively as `{"evaluator_config":{...},"evaluator_type":"..."}` |

### 2.17 Version Resolution Function

```
system_state_hash = SHA-256(canonical_json({
  directive_graph_version: "1.2.0",
  cg_ir_hash: "abc123...",
  frozen_env_hash: "def456...",
  engine_version: "3.0.0",
  target_hash: "789ghi..."
}))
```

To reproduce any historical inspection, pin all five dimensions.

### 2.18 Version Incompatibility Handling

| Scenario | Behavior |
| :--- | :--- |
| Engine version < CG-IR schema version | Reject with error: "Engine too old for this CG-IR" |
| Engine version > CG-IR schema version | Accept if backward-compatible; otherwise reject |
| Policy version != Schema policy_contract_version | Reject with warning; require synchronization |
| Frozen env mismatch | Reject with error: "Cannot reproduce without exact frozen_env" |

**Downgrade Policy:** Downgrades are not supported. The system only moves forward. Legacy CG-IR snapshots remain reproducible with pinned engine versions.

---

## 3. Execution Artifact Schema

### 3.1 Finding State Machine (FSM)

Findings follow a strict state transition model:

```
                    ┌─────────────┐
                    │   Created   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
               ┌────│    Open     │────┐
               │    └──────┬──────┘    │
               │           │           │
        ┌──────▼──────┐    │    ┌──────▼──────┐
        │  Acknowledged│    │    │  Dismissed  │
        │  (In Remedy) │    │    │  (Invalid)  │
        └──────┬──────┘    │    └─────────────┘
               │           │
        ┌──────▼──────┐    │
        │  Evidence    │    │
        │  Submitted   │    │
        └──────┬──────┘    │
               │           │
        ┌──────▼──────┐    │
        │  Pending     │    │
        │  Verification│    │
        └──────┬──────┘    │
               │           │
      ┌────────┴────────┐  │
      │                 │  │
┌─────▼─────┐    ┌──────▼──────┐
│  Verified  │    │  Rejected   │
│  (Resolved)│    │  (Reopen)   │
└─────┬─────┘    └──────┬──────┘
      │                 │
      │    ┌────────────┘
      │    │
┌─────▼─────┐
│   Closed  │
└───────────┘
```

**State Transitions:**

| From | To | Trigger | Allowed Actor |
| :--- | :--- | :--- | :--- |
| Created | Open | System (automatic) | System |
| Open | Acknowledged | S-12 (acknowledge) | Compliance Representative |
| Open | Dismissed | Disposition = Invalid | Regulatory Official |
| Acknowledged | Evidence Submitted | S-13 (submit evidence) | Compliance Representative |
| Evidence Submitted | Pending Verification | System (automatic) | System |
| Pending Verification | Verified | S-14 (approve) | Regulatory Official |
| Pending Verification | Rejected | S-14 (reject) | Regulatory Official |
| Rejected | Open | Reopen with comments | Regulatory Official |
| Verified | Closed | System (automatic) | System |

**Disposition Values:**

| Disposition | Meaning |
| :--- | :--- |
| `valid` | Finding is legitimate; requires remediation |
| `invalid` | Finding is incorrect; no action needed |
| `waived` | Finding is legitimate but accepted as risk |

### 3.2 Capability-Based Permission Model

| Capability | Regulatory Official | Compliance Representative | System |
| :--- | :---: | :---: | :---: |
| `directive.create` | ✅ | ❌ | ❌ |
| `directive.modify` | ✅ | ❌ | ❌ |
| `directive.retire` | ✅ | ❌ | ❌ |
| `directive.fork` | ✅ | ❌ | ❌ |
| `directive.merge` | ✅ | ❌ | ❌ |
| `directive.restore` | ✅ | ❌ | ❌ |
| `inspection.submit` | ❌ | ✅ | ✅ |
| `inspection.reinspect` | ❌ | ✅ | ❌ |
| `finding.view` | ✅ | ✅ | ✅ |
| `finding.acknowledge` | ❌ | ✅ | ❌ |
| `finding.dismiss` | ✅ | ❌ | ❌ |
| `finding.waive` | ✅ | ❌ | ❌ |
| `finding.approve_remediation` | ✅ | ❌ | ❌ |
| `finding.reject_remediation` | ✅ | ❌ | ❌ |
| `evidence.submit` | ❌ | ✅ | ❌ |
| `analytics.view` | ✅ | ✅ | ✅ |
| `conflict.resolve` | ✅ | ❌ | ❌ |

**Segregation of Duties:**
- Directive creator ≠ Finding waiver (same person cannot both create a rule and waive findings from it)
- Evidence submitter ≠ Remediation approver (same person cannot both submit evidence and approve it)

### 3.3 Execution Fault Taxonomy

| Fault Class | Type | Behavior | Retry |
| :--- | :--- | :--- | :--- |
| **Deterministic Evaluation** | Rule logic fails | Node → `Fail` finding | No |
| **Deterministic Partial** | Partial compliance | Node → `Partial` finding | No |
| **Ambiguous Evaluation** | Cannot determine | Node → `NeedsReview` finding | No |
| **Dependency Failure** | Upstream node failed | Node skipped → `Skipped` trace entry | No |
| **Timeout** | Node exceeds time limit | Node → `Timeout` finding | Configurable |
| **Resource Exhaustion** | Memory/CPU limits | Node → `ResourceExhausted` finding | No |
| **Schema Violation** | Target malformed | Pipeline → `SchemaError` | No |
| **CG-IR Corruption** | Snapshot integrity fails | Pipeline → `Fatal` (abort inspection) | No |

**Retry Policy:**
- Deterministic failures: No retries (permanent state)
- Timeouts: Configurable retry count (default: 0, max: 3)
- Resource exhaustion: No retries (escalate to operator)
- Schema violations: No retries (return error to submitter)

### 3.4 Concurrency Model for Compilation

**Directive Graph Locking:**
- Compilation acquires a read lock on the Directive Graph
- Concurrent compilations are allowed (read-only)
- Directive modifications acquire a write lock (exclusive)
- Write lock blocks compilation; compilation blocks writes

**CG-IR Snapshot Creation:**
- Snapshot creation is atomic (all-or-nothing)
- Two compilations cannot produce the same snapshot hash (content-addressed)
- If two compilations produce identical CG-IR, the second is a no-op (deduplication)

**Compilation Queue:**
- Multiple compilation requests are serialized through a queue
- Each request includes a request_id for tracking
- Duplicate requests (same Directive Graph version + same frozen_env) are deduplicated

### 3.5 CG-IR Storage and Hashing Granularity

**Storage Model:**

```
CG-IR Content-Addressed Store
├── snapshots/           (full DAG snapshots, keyed by hash)
│   └── {hash}/
│       ├── manifest.json    (snapshot metadata)
│       ├── nodes/           (individual node objects)
│       │   └── {node_hash}.json
│       └── edges/           (dependency graph)
│           └── {edge_hash}.json
└── shared/              (deduplicated node objects)
    └── {node_hash}.json
```

**Hashing Granularity:**

| Level | Hash Target | Use Case |
| :--- | :--- | :--- |
| **Node** | Individual control node content | Deduplication across snapshots |
| **Edge** | Dependency relationship | Graph structure verification |
| **Snapshot** | Full DAG manifest (includes node + edge hashes) | CG-IR version identity |
| **Frozen Env** | Entire compilation environment | Reproducibility guarantee |

**Deduplication Rules:**
- Nodes with identical content share storage (same node_hash)
- Edges are stored once per unique (source, target) pair
- Snapshots reference nodes/edges by hash, not copy
- Storage cost scales with unique content, not total rule count

**Retention Policy:**

| Artifact | Retention | Pruning |
| :--- | :--- | :--- |
| CG-IR Snapshots | Indefinite (immutable) | Never pruned |
| Node Objects | Indefinite (shared) | Never pruned |
| Inspection Snapshots | Configurable (default: 7 years) | Pruned after retention period |
| Finding Events | Indefinite (audit trail) | Never pruned |
| Pipeline Traces | Configurable (default: 1 year) | Pruned after retention period |

### 3.6 Inspection Snapshot

```json
{
  "inspection_id": "string (UUID)",
  "target_id": "string",
  "target_hash": "string (SHA-256)",
  "ruleset_version": "string (CG-IR hash)",
  "frozen_env_hash": "string",
  "engine_version": "string",
  "inspector": "string (actor ID)",
  "started_at": "datetime (ISO 8601, UTC)",
  "completed_at": "datetime (ISO 8601, UTC)",
  "status": "enum (completed, partial, failed)",
  "finding_count": "integer",
  "skipped_nodes": ["string (node_ids)"],
  "pipeline_trace": [
    {
      "stage": "string",
      "started_at": "datetime",
      "completed_at": "datetime",
      "status": "enum (success, skipped, failed)",
      "node_id": "string (optional)"
    }
  ],
  "system_state_hash": "string (SHA-256)"
}
```

### 3.2 Pipeline Trace Entry

```json
{
  "stage": "enum (normalize, classify, select_controls, evaluate, aggregate, report)",
  "node_id": "string (optional, for evaluate stage)",
  "started_at": "datetime",
  "completed_at": "datetime",
  "status": "enum (success, skipped, failed)",
  "error": "string (optional)",
  "duration_ms": "integer"
}
```

---

## 4. Layered Namespace Model

```
Directive Graph
├── prose/          (human-readable sections)
├── directives/     (structured rule definitions)
├── metadata/       (version, jurisdiction, domain)
└── traceability/   (Machine IDs, anchor refs, lineage)

CG-IR
├── nodes/          (control nodes)
├── edges/          (dependency graph)
├── evaluators/     (evaluation logic)
└── provenance/     (compilation metadata, frozen_env)

Finding Event Stream
├── events/         (immutable event log with hashes)
├── computed/       (derived state projections)
└── analytics/      (read-only aggregate views)

Execution Artifacts
├── inspections/    (inspection snapshots)
├── traces/         (pipeline traces)
└── hashes/         (system state hashes)
```

---

## 5. Version Compatibility Matrix

| Axis | Format | Mutability |
| :--- | :--- | :--- |
| Specification Version | Semantic (MAJOR.MINOR.PATCH) | Immutable per release |
| Directive Graph Version | Semantic (MAJOR.MINOR.PATCH) | Mutable |
| CG-IR Schema Version | Semantic | Immutable per snapshot |
| Engine Version | Semantic | Immutable per release |
| Frozen Environment | Content hash | Immutable per compilation |

**Version Compatibility Matrix (Decoupled):**

| Spec Version | Schema Version | Policy Version | Engine Compatibility |
| :--- | :--- | :--- | :--- |
| 8.x | 8.x | 8.x | Engine ≥ 8.0.0 |

**Version Compatibility Rules:**
1. Spec, schema, and policy versions MUST have the same MAJOR version
2. MINOR and PATCH versions may differ (independent evolution)
3. Engine version MUST be ≥ CG-IR schema MAJOR version
4. MAJOR version mismatch = incompatible (reject)
5. MINOR version mismatch = backward-compatible (accept with warning)
6. PATCH version mismatch = fully compatible (accept silently)

**Downgrade Policy:** Downgrades are not supported. The system only moves forward. Legacy CG-IR snapshots remain reproducible with pinned engine versions.

---

## 6. Policy Doctrine Contract

### 6.1 Structure

| Section | Required | Content Type | Purpose |
|---------|----------|--------------|---------|
| Preamble | Yes | Prose | Existential need |
| Governance & Amendment | Yes | Prose | Change process |
| Definitions | Yes | Table | Term definitions |
| Foundational Principles | Yes | Prose/Table | Axioms |
| Directives | Yes | Mixed | Rules and standards |
| Sanctions & Remedies | Yes | Table | Consequences |
| References & Annexes | No | Prose/Table | External sources |

### 6.2 Contamination Guard

**Prohibited fields in policy:** parameters, conditions, evaluator_hint, evaluator_type, evaluator_config, weight, depends_on, conflicts_with, status, created_at, expires_at, remediation, target, lineage

**Allowed:** Machine ID columns (cross-reference labels only)

**Cross-Layer Field Legality Matrix:**

| Field | Policy Layer | Schema Layer | Spec Layer |
| :--- | :--- | :--- | :--- |
| `Machine ID` / `rule.id` | ✅ Allowed | ✅ Required | ✅ Defined |
| `evaluator_type` | ❌ Prohibited | ✅ Required | ✅ Defined |
| `evaluator_config` | ❌ Prohibited | ✅ Required | ✅ Defined |
| `lineage` | ❌ Prohibited | ⚠️ Conditional | ✅ Defined |
| `priority_hierarchy` | ✅ Declarative | ✅ As `priority` field | ✅ Defined |
| `conflict_resolution_intent` | ✅ Declarative | ✅ As `conflict_resolution` field | ✅ Defined |
| `conflict_resolution` | ❌ Prohibited | ✅ Optional override | ✅ Defined |

**Note:** Priority hierarchy and conflict resolution are DECLARATIVE DESCRIPTIONS of governance intent in policy. The compilation engine translates intent into CG-IR logic via the Conflict Resolution Mapping (Section 2.15).

---

## 7. Rule Schema Contract

See `rule_schema.json` for the formal JSON Schema.

Key fields: `id` (canonical identity), `type`, `message`, `evaluator_type` (pure only), `evaluator_config`, `depends_on`, `priority`, `lineage` (fork/merge/split tracking).

---

## 8. System Invariants

| Invariant | Description |
| :--- | :--- |
| **Normative Source** | SPECIFICATION.md is the single normative source; schema and policy MUST conform |
| **Dual Identity** | Lineage ID (immutable root) + Execution ID (active node identity) |
| **Lineage ID Immutability** | Once assigned, lineage_id is never reused |
| **Execution ID Stability** | Execution ID changes only on fork/merge/split |
| **Hermetic Compilation** | CG-IR reproducibility requires pinned frozen_env |
| **CG-IR Snapshot Immutability** | Once published, a snapshot is immutable; compilation creates new snapshots |
| **CG-IR Content Addressing** | Snapshots are content-addressed; identical content produces identical hash |
| **Finding Event Immutability** | Append-only; event_hash ensures integrity |
| **Finding FSM** | Findings follow strict state transitions (see Section 3.1) |
| **Inspection Immutability** | Completed snapshots never modified |
| **Evaluator Purity** | Pure functions: no IO, no randomness |
| **Evaluator Type Safety** | evaluator_config MUST match evaluator_type (schema-enforced if/then) |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver; Evidence submitter ≠ Approver |
| **Capability Enforcement** | All actions checked against capability matrix |
| **Mediated Feedback** | Analytics inform humans; no direct finding → CG-IR |
| **Declarative Governance** | Policy describes intent; engine implements via Conflict Resolution Mapping |
| **Deterministic Serialization** | Canonical JSON with sorted keys; NaN/Infinity prohibited |
| **HLC Event Ordering** | physical_time → logical_counter → node_id → event_id; monotonic counter per node |
| **Version Compatibility** | MAJOR versions match across spec/schema/policy |
| **Cross-Layer Binding** | Schema MUST conform to spec; policy MUST NOT contradict spec |
| **Concurrency Safety** | Compilation = read lock; modification = write lock |

---

## 9. Validation

### 9.1 Identity Validation

1. Every lineage_id in policy exists as rule.lineage_id in schema
2. Every rule.lineage_id has a Machine ID in policy
3. Every CG-IR node.lineage_id matches a rule.lineage_id
4. No orphan lineage_ids in any layer
5. lineage_id matches pattern: `^[A-Z][A-Z0-9]+-[0-9]+$`
6. execution_id matches pattern: `^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$`
7. No duplicate lineage_id values within a ruleset
8. Lineage field is present for fork/merge/split operations
9. Lineage field is absent for revision/rename/retire operations

### 9.2 Evaluator Validation

1. All evaluators are pure functions (no IO detected)
2. evaluator_type is one of: regex, field_check, threshold, composite
3. evaluator_config matches evaluator_type (discriminated union):
   - `regex` requires `pattern` field
   - `field_check` requires `field`, `operator`, `value`
   - `threshold` requires `field`, `operator`, `threshold`
   - `composite` requires `logic`, `sub_evaluators`
4. All inputs/outputs JSON-serializable
5. Deterministic serialization verified

### 9.3 CG-IR Validation

1. All nodes reference valid lineage_ids
2. DAG is acyclic
3. Content hash matches ruleset version
4. Frozen environment metadata complete
5. Snapshot is immutable (no mutation after publish)
6. Node hashes are content-addressed (identical content = identical hash)

### 9.4 Inspection Validation

1. Target hash matches submitted target
2. CG-IR hash matches published version
3. Frozen environment hash matches CG-IR provenance
4. Pipeline trace complete
5. System state hash correctly computed
6. Finding FSM transitions are valid (no illegal state jumps)

### 9.5 Event Validation

1. All events have valid event_hash
2. Events follow HLC ordering (physical_time → logical_counter → node_id → event_id)
3. finding_id references valid finding
4. No duplicate event_ids
5. Finding state transitions follow FSM (Section 3.1)

### 9.6 Permission Validation

1. All actions checked against capability matrix (Section 3.2)
2. Segregation of duties enforced (creator ≠ waiver, submitter ≠ approver)
3. AI agent actions logged with actor identity

### 9.7 Cross-Layer Validation

1. Spec, schema, and policy MAJOR versions match
2. No schema element contradicts a spec invariant
3. No policy field violates contamination guard
4. evaluator_config fields match evaluator_type (no invalid state combinations)

---

## 10. References

- `docs/Regulation/policy_doctrine.yaml` — Policy contract (declarative governance)
- `docs/Regulation/rule_schema.json` — Rule schema (machine structure)
- `docs/User_Story/User_Stories.md` — User stories (behavioral contract)

---

## 11. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-07-04 | Initial specification |
| 2.0.0 | 2026-07-05 | Added Control Model, Inspection Pipeline |
| 3.0.0 | 2026-07-05 | Added CG-IR, Determinism Contract |
| 4.0.0 | 2026-07-05 | Three runtime primitives, hermetic boundary |
| 5.0.0 | 2026-07-05 | Incremental compilation, evaluator contract |
| 6.0.0 | 2026-07-05 | Canonical identity, transformation pipeline, declarative governance |
| 7.0.0 | 2026-07-05 | Identity lifecycle, execution artifact schema, deterministic serialization, conflict resolution mapping, event schema, version incompatibility handling, target/context strict schemas |
| 8.1.0 | 2026-07-05 | Cross-layer compliance audit: fixed identity mapping (Machine ID → lineage_id), HLC clock advancement and monotonic counter rules, cross-layer conflict resolution precedence chain, FSM human/system transition binding |
