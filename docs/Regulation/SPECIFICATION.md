# Universal Rule Governance Specification

**Version:** 8.2.1
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
7. **Policy runtime prohibition:** policy_doctrine.yaml MUST NOT be read during inspection, evaluation, finding FSM transitions, or conflict resolution at runtime. Policy influences execution only indirectly: human authors use it when writing directives, and compile-time validators check that schema fields (e.g., `priority`, `conflict_resolution`) conform to spec — never by interpreting policy prose as executable logic

### 1.3 Terminology

The following terms are normatively defined for use across all layers:

| Term | Definition |
| :--- | :--- |
| **Normative** | Binding system behavior defined exclusively in this specification. Schema and policy MUST conform; policy prose is never normative at runtime. |
| **Structural Projection** | `rule_schema.json` encoding of spec invariants. Carries data; does not define algorithms. |
| **Compile-Time** | Directive Graph validation, schema validation, CG-IR generation, and cross-field semantic checks. Policy MAY influence authors; engines MUST NOT read policy prose. |
| **Inspection** | Point-in-time evaluation of a target against a frozen CG-IR snapshot. Produces immutable execution artifacts. |
| **Evaluation** | Pure evaluator invocation within an inspection. No IO, no randomness. |
| **Context** | Read-only object (§2.11) passed to evaluators. Evaluators MUST NOT mutate it. |
| **Scope** | Applicability constraints compiled into CG-IR `scope`. Participates in specificity scoring (§2.15). |
| **Target** | Submitted artifact conforming to §2.10. The subject of inspection. |
| **Semantic Intent** | Human-declared purpose of a directive. Stable across revision/rename; changes on fork/split. |
| **Conflict Artifact** | Escalation record when `resolve_conflict` cannot deterministically select a winner. Requires human review via `conflict.resolve` capability. |
| **Authorized Governing Body** | Entity with ratification authority over policy amendments (§6.1 Governance & Amendment). |
| **Finding FSM** | Strict state machine governing finding lifecycle (§3.1). |

### 1.4 Scope

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

### 2.2 Identity Lifecycle Operations

Lifecycle operations transform directive identity. Each operation MUST record provenance in the `lineage` field when required by schema.

#### 2.2.1 Operation Semantics

| Operation | `lineage_id` | `id` (execution) | `lineage` field |
| :--- | :--- | :--- | :--- |
| **revision** | Unchanged | Unchanged | NOT required |
| **fork** | Inherited (shared) | Two new unique IDs | REQUIRED (`operation=fork`) |
| **merge** | New root (see §2.2.2) | One new unique ID | REQUIRED (`operation=merge`) |
| **split** | Inherited (shared) | Multiple new unique IDs | REQUIRED (`operation=split`) |
| **rename** | Unchanged | Unchanged | NOT required |
| **retire** | Unchanged | Unchanged; `status=deprecated` | NOT required |

#### 2.2.2 Deterministic Merge Semantics

When two directives merge, identity selection is fully deterministic:

```
merge(parent_a, parent_b) → merged_rule:

1. lineage_id := MIN(parent_a.lineage_id, parent_b.lineage_id) lexicographically
   // The lexicographically smaller parent lineage_id becomes the merged root.
   // The other parent lineage_id is recorded only in lineage.parent_lineage_ids.

2. id := lineage_id + "-M" + SHA-256(canonical_json({
     parent_lineage_ids: sorted([parent_a.lineage_id, parent_b.lineage_id]),
     parent_execution_ids: sorted([parent_a.id, parent_b.id]),
     operation: "merge"
   }))[0:8].uppercase()
   // Example: TRAF-001-M3A7F2B1

3. lineage.parent_lineage_ids := sorted unique([parent_a.lineage_id, parent_b.lineage_id])
4. lineage.parent_execution_ids := sorted unique([parent_a.id, parent_b.id])
5. Both parent rules transition to status=deprecated
```

**Invariant:** The merged `lineage_id` equals the lexicographically minimum parent `lineage_id`. The non-surviving parent `lineage_id` remains in audit history via `lineage.parent_lineage_ids` but is never reused as an active root.

#### 2.2.3 Lineage DAG Invariants

The lineage ancestry graph MUST satisfy:

1. **Acyclicity:** No directed cycle in `(parent_lineage_ids → child lineage_id)` edges
2. **Single root per active rule:** Each active rule has exactly one `lineage_id`
3. **Parent existence:** Every ID in `parent_lineage_ids` and `parent_execution_ids` MUST reference a rule that existed at `lineage.timestamp`
4. **Operation consistency:**
   - `fork`/`split`: exactly one entry in `parent_lineage_ids` (the inherited root)
   - `merge`: exactly two entries in `parent_lineage_ids` (both parents)
5. **No self-reference:** A rule MUST NOT list its own `lineage_id` or `id` as a parent
6. **Depth bound:** Maximum ancestry depth = 64 operations from any leaf to root (compile-time rejection beyond limit)
7. **Temporal ordering:** `lineage.timestamp` MUST be ≥ max(parent timestamps) when parent lineage records exist

Pathological sequences (fork → merge → fork → merge chains) are permitted provided invariants 1–7 hold. Compile-time validation MUST reject cycles and depth violations.

#### 2.2.4 Deprecation and Supersession

| Transition | Semantics |
| :--- | :--- |
| `active` → `deprecated` | Rule retired; audit trail preserved; CG-IR nodes marked deprecated |
| `active` → `superseded` | Rule replaced by another rule; `metadata.migration.superseded_by` MUST reference the successor `id` |
| Successor binding | Compile-time validator MUST verify `superseded_by` references an active or draft rule |

### 2.3 Canonical Identity Resolution

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
- **Pattern relationship:** Execution ID extends lineage_id pattern by appending zero or more `-SUFFIX` segments. The base `[A-Z][A-Z0-9]+-[0-9]+` is shared. On first creation, execution_id equals lineage_id (zero suffix segments). After fork/merge/split, suffix segments are appended.

**Identity Mapping:**

| Layer | Lineage ID Field | Execution ID Field |
| :--- | :--- | :--- |
| Policy Doctrine | `Machine ID` → lineage_id | Not represented (assigned at schema compile as `rule.id`) |
| Rule Schema | `rule.lineage_id` | `rule.id` |
| CG-IR | `node.lineage_id` | `node.directive_id` |
| Finding | `finding.lineage_id` | `finding.control_id` → node |

**Invariant:** `rule.lineage_id` is immutable. `rule.id` is the active execution identity. On fork/merge/split, `rule.id` changes but `rule.lineage_id` is inherited from the parent.

**Machine ID — Single Interpretation:**

`Machine ID` has exactly one meaning across all layers: the **stable external lineage identifier** assigned at directive authoring time.

| Property | Rule |
| :--- | :--- |
| **What it is** | Human-assigned lineage root label in policy directive tables |
| **What it is not** | An execution ID, a compile-time artifact, or a runtime lookup key |
| **Assignment** | Assigned once when a directive is first authored; never reassigned |
| **Compile binding** | At schema compile: `rule.lineage_id = Machine ID` (1:1 bijective at lineage-root level) |
| **Initial execution ID** | On first creation: `rule.id = rule.lineage_id` |
| **After fork/merge/split** | `rule.lineage_id` unchanged or inherited; `rule.id` diverges per lifecycle rules |
| **Referential integrity** | Every `Machine ID` in policy MUST map to exactly one lineage root `lineage_id`; every lineage root `lineage_id` MUST have exactly one `Machine ID`. After fork/split, multiple active rules may share the same `lineage_id` — the bijection is at the root-assignment level, not at the per-rule-uniqueness level. |
| **Runtime** | Engine uses `rule.lineage_id` / `node.lineage_id` — never reads policy tables |

**Lineage-Uniqueness Refinement:**

The invariant `lineage_id MUST be unique within a ruleset` (§9.1 item 7) is scoped as follows:
- **Root uniqueness:** No two *distinct* lineage roots may share the same `lineage_id`. Once assigned, a `lineage_id` root is never reused.
- **Post-fork/split sharing:** After fork or split, multiple active rules may legitimately share the same `lineage_id` while having distinct `id` (execution ID) values.
- **Primary key:** Rule identity within a ruleset is uniquely identified by `(lineage_id, id)`. The `id` field alone is also unique (execution ID uniqueness is global).
- **Conflict resolution scope:** `resolve_conflict` operates on the set of active rules sharing a `lineage_id`. Cross-lineage conflicts produce Conflict Artifacts (§2.15).

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

**CG-IR Node Hashing Scope (Local Content Identity):**

Node identity is **local** — a node hash depends only on the node's own canonical content, not on global DAG position or neighbor context.

**Dual Hash Model:**

| Hash | Input | Purpose |
| :--- | :--- | :--- |
| **semantic_hash** | `semantic_body` (evaluator, scope, depends_on, priority, conflict_resolution, status, severity_default) | Compilation cache identity; unchanged by editorial description edits |
| **presentation_hash** | `presentation_body` (description, directive_revision, control_version) | Audit/display drift detection |
| **node_hash** | SHA-256(canonical_json({semantic_hash, presentation_hash})) | Content-addressed storage key |

```
semantic_body = {
  directive_id, lineage_id,
  evaluator, scope, severity_default,
  depends_on,           // sorted array (§2.16)
  priority, conflict_resolution, status
}

presentation_body = {
  description, directive_revision, control_version
}

node_hash = SHA-256(canonical_json({
  semantic_hash: SHA-256(canonical_json(semantic_body)),
  presentation_hash: SHA-256(canonical_json(presentation_body))
}))
// Excluded from all hashes: graph edges, snapshot manifest position, neighbor hashes
```

**Incremental reuse:** Unchanged `semantic_body` produces identical `semantic_hash` even when `description` changes. Downstream compilation MAY reuse evaluator subgraphs keyed on `semantic_hash`.

| Hash Level | Input | Scope | Purpose |
| :--- | :--- | :--- | :--- |
| **Node** | `node_body` only | Local content | Deduplication across snapshots; stable under incremental reuse |
| **Edge** | `edge_body` (see formula below) | Pair identity | Graph structure separate from node content |
| **Snapshot** | `{node_hashes: sorted[], edge_hashes: sorted[], provenance}` | Global composition | Snapshot identity; structure without embedding neighbors in node hash |

**Edge Hash Formula:**

```
edge_hash = SHA-256(canonical_json(edge_body))

edge_body = {
  source: directive_id,    // string, the dependency source
  target: directive_id     // string, the dependency target
}
```

- Edges are directional: `edge_body = {source: "A", target: "B"}` ≠ `{source: "B", target: "A"}`
- Duplicate edges (same source, same target) produce identical `edge_hash` values
- The edge hash is independent of node body content — graph structure and node identity are fully decoupled
- Edge ordering in the snapshot manifest is canonicalized by sorted `edge_hash[]` (not insertion order)

**CG-IR Snapshot Hash Composition:**

```
cg_ir_snapshot_hash = SHA-256(canonical_json({
  node_hashes: sorted[],        // sorted array of node_hash values
  edge_hashes: sorted[],        // sorted array of edge_hash values
  provenance: {
    engine_version: string,     // pinned engine version
    frozen_env_hash: string,    // SHA-256 of frozen environment
    directive_graph_version: string
    // Note: compiled_at is NOT included here — it is execution artifact
    // metadata only. Including it would break snapshot hash determinism.
  }
}))
```

**compiled_at** is recorded in execution artifact metadata (inspection snapshots, pipeline traces) but NOT in the snapshot hash. This ensures that two compilations with identical directive graph content, engine version, and frozen environment produce the same `cg_ir_snapshot_hash` regardless of wall clock time.

**Determinism guarantee:** Given identical directive graph content, engine version, and frozen environment, the snapshot hash is identical. The hash is **not a function of wall clock time, compilation node identity, or request context**.

**Provenance Canonicalization Requirement:** All provenance fields MUST be canonicalized (normalized to canonical form) before inclusion in the snapshot hash input. Provenance fields MUST NOT be appended in non-deterministic order. Specifically:
- `engine_version` and `frozen_env_hash` are normalized strings (no trailing whitespace, case-insensitive where applicable)
- `directive_graph_version` follows semver normalization
- `compiled_at` is NOT part of the snapshot hash input — it is recorded in execution artifact metadata only. Two compilations with identical directive graph content, engine version, and frozen environment produce the same `cg_ir_snapshot_hash` regardless of wall clock time
- If future extensions add provenance fields, each field MUST be declared with a canonical form before inclusion in hash computation

**Incremental Reuse Guarantee:** If `node_body` is byte-identical across compilations, `node_hash` is identical regardless of which snapshot references it. Conflict resolution metadata (`priority`, `conflict_resolution`) is part of `node_body` — not lost by local hashing. Graph context (which nodes depend on which) is captured in edge hashes and the snapshot manifest only.

**Cycle Safety:** `depends_on` stores directive_id references as a sorted string array. Edges are validated for acyclicity at compile time. Hashing does not recursively embed neighbor node content — no cyclic hash dependency.

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
| **Type Safety** | `evaluator_config` MUST match `evaluator_type` (schema if/then). This is a semantic invariant — intermediate validators that only validate subschemas may not catch invalid pairings. Compile-time validation MUST check cross-field consistency. |

**Evaluator Portability Constraints (cross-runtime determinism):**

| Constraint | Rule | Rationale |
| :--- | :--- | :--- |
| **Regex dialect** | Engines MUST use RE2-compatible regex syntax. PCRE-only features (backreferences, lookaheads beyond lookahead/lookbehind, atomic groups) are PROHIBITED in evaluator patterns. Flags limited to: `i` (case-insensitive), `m` (multiline), `s` (dot-all). | RE2 guarantees linear-time matching and consistent behavior across implementations (Go, C++, Java, Python via `google-re2`). PCRE features create cross-runtime divergence. |
| **Numeric normalization** | All numeric comparisons use IEEE 754 double-precision arithmetic. NaN and Infinity are NOT permitted in evaluator configs or target values (schema rejects). Float comparison uses exact IEEE 754 bitwise equality — no epsilon tolerance unless explicitly configured. | Prevents silent divergence across CPU architectures and language runtimes. |
| **Timestamp handling** | All timestamp comparisons in evaluators use UTC (ISO 8601). Timezone-aware conversions are NOT permitted within evaluator logic. Target `submitted_at` and context `last_inspection_date` are always UTC-normalized before evaluator invocation. | Eliminates DST/timezone ambiguity across evaluation environments. |
| **String comparison** | String equality and ordering use Unicode codepoint comparison (NFC-normalized). No locale-dependent collation. | Prevents locale-sensitive ordering divergence. |

**Evaluator Types (pure only):**

| Type | Description |
| :--- | :--- |
| `regex` | Pattern matching against target content |
| `field_check` | Validates specific fields in structured targets |
| `threshold` | Numeric comparison against configured limits |
| `composite` | Boolean combination of sub-evaluators |

**Evaluator Complexity Limits (compile-time enforced):**

| Limit | Value | Violation |
| :--- | :--- | :--- |
| Maximum composite recursion depth | 32 levels | `SchemaError: evaluator depth exceeded` |
| Maximum total evaluator nodes per rule | 256 (including root) | `SchemaError: evaluator count exceeded` |
| Maximum composite DAG width (`sub_evaluators` count at any level) | 64 | `SchemaError: evaluator width exceeded` |
| Maximum regex pattern length | 4 096 characters | `SchemaError: pattern too long` |
| Maximum `metadata` serialized size per rule | 16 KiB | `SchemaError: metadata too large` |

**Regex catastrophic backtracking mitigation:** All regex patterns MUST be RE2-compatible (§2.9 portability). Compile-time validation MUST reject patterns exceeding length limit. Runtime engines SHOULD enforce per-node evaluation timeout (§2.12).

**Discriminator Validation:** `evaluator_type` ↔ `evaluator_config` consistency is a semantic invariant. JSON Schema `if`/`then` alone is insufficient — compile-time validation MUST apply dependent-schema checks equivalent to:

```
when evaluator_type = T → evaluator_config MUST match $defs for T exclusively
reject any oneOf match where x-evaluator-type ≠ evaluator_type
```

Engines MUST NOT rely on partial subschema validation for evaluator pairing.

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

**HLC State (per node):** Persisted tuple `(pt, lc)` where `pt` = last emitted physical_time, `lc` = last emitted logical_counter.

**HLC Clock Advancement:**

```
// pt_wall = current wall clock (UTC). May regress due to NTP/VM migration.
function hlc_send(pt_wall):
  pt_new = max(pt, pt_wall)
  if pt_new > pt:
    lc_new = 0
  else:
    lc_new = lc + 1
  pt, lc = pt_new, lc_new
  return { physical_time: pt, logical_counter: lc, node_id }

function hlc_receive(remote_pt, remote_lc, pt_wall):
  pt_new = max(pt, pt_wall, remote_pt)
  if pt_new > pt:
    lc_new = 0
  else if pt_new == pt:
    lc_new = max(lc, remote_lc) + 1
  else:
    lc_new = lc + 1
  pt, lc = pt_new, lc_new
  return { physical_time: pt, logical_counter: lc, node_id }
```

**Monotonicity Guarantee (per node_id):**
- The emitted tuple `(physical_time, logical_counter)` is **strictly lexicographically non-decreasing** across all events from the same `node_id`
- `physical_time` in the persisted state NEVER decreases — wall clock regression is absorbed by incrementing `logical_counter` instead
- `logical_counter` NEVER decreases
- Counter resets to 0 **only** when `physical_time` strictly advances (`pt_new > pt`); never because wall clock alone regressed
- On node restart: load persisted `(pt, lc)`; apply `hlc_send` with current wall clock — if `pt_wall < pt`, tuple becomes `(pt, lc+1)` preserving monotonicity

**Multi-Node Reconciliation:**
- Each event carries the emitting node's HLC tuple; receivers apply `hlc_receive` before appending locally originated events
- Total order is reconstructed by sorting all events by the 4-level key (physical_time → logical_counter → node_id → event_id)
- Partition tolerance: nodes may diverge during partition; on heal, merged stream is re-sorted by total order key (no overwrite of committed events)
- Cross-node ties at equal `(physical_time, logical_counter)` are broken by `node_id`, then `event_id`
- Validation rejects any event where the new tuple is lexicographically less than the node's previous tuple

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

**Explicit override takes precedence.** The runtime engine executes ONLY the algorithm below over schema/CG-IR fields. Policy prose is never consulted at runtime.

**Temporal Binding Guarantee:** The `created_at` field used in conflict resolution is the directive's authoring timestamp, frozen into `node_body` at compilation time. It is a static property of the CG-IR node — NOT evaluation time, NOT wall clock time. For a given CG-IR snapshot, conflict resolution outcomes are fully deterministic because all inputs (`priority`, `conflict_resolution`, `created_at`, `scope` for specificity) are frozen in the immutable snapshot. Two evaluations of the same CG-IR snapshot against the same target always produce identical conflict outcomes, regardless of when evaluation occurs.

| Intent (Policy — authoring only) | Schema Field | Operator (CG-IR — runtime) | Implementation |
| :--- | :--- | :--- | :--- |
| "Higher priority wins" | `priority` | `max(priority_level)` | Constitutional(1) > Statutory(2) > Regulatory(3) > Operational(4) > Advisory(5) |
| "More specific wins" | `target`, scope constraints | `specificity_score(rule) > specificity_score(other)` | Formal algorithm below |
| "Newer wins" | `created_at` | `max(created_at)` | ISO 8601 timestamp comparison |
| N/A (schema-only) | `conflict_resolution` | `has_field(conflict_resolution)` | Checked first, before all computed factors |

**Cross-Layer Precedence Chain:**

| Layer | Role | Runtime Influence |
| :--- | :--- | :--- |
| **Policy** | Declares governance intent for human authors. Documents what priority levels mean. | **None.** Not read at inspection, evaluation, or conflict resolution runtime. |
| **Schema** | Encodes `priority`, `created_at`, `conflict_resolution` as structural fields. | **Data carrier only.** Fields are read by the engine; schema itself is not an algorithm. |
| **Spec (this document)** | Normative `resolve_conflict` algorithm. | **Sole executable source.** All runtime conflict decisions flow through this function. |

**Compile-Time Translation (not runtime):** When compiling policy prose to schema, authors set `priority` and optional `conflict_resolution` fields. A compile-time validator MAY check that priority assignments are consistent with policy intent — but this validation produces errors/warnings at compile time only; it does not create a second runtime decision path.

**Specificity Score Algorithm (normative):**

```
specificity_score(rule) → non-negative integer

score = 0

// 1. Target constraint specificity
if rule.target is present and non-empty:
  score += 1000 + len(rule.target)

// 2. Scope constraint depth (compiled from CG-IR scope object)
for each key in canonical_sorted(scope.keys()):
  score += 100
  if scope[key] is object:
    score += depth(scope[key]) * 10    // nested keys add depth
  else:
    score += 1

// 3. Evaluator field binding (more constrained = more specific)
score += count_bound_fields(rule.evaluator)   // regex pattern=1, field_check=3, threshold=3, composite=sum(children)

// 4. Explicit priority within same level does NOT affect specificity (handled by priority step)

Tie on equal score → proceed to recency step
```

`count_bound_fields` recursively counts required evaluator config fields. Composite evaluators sum child scores. Two engines implementing this algorithm MUST produce identical scores for identical CG-IR node bodies.

**Priority Level Mapping (internal integer):**

| Schema `priority` enum | `priority_level` integer |
| :--- | :--- |
| `constitutional` | 1 |
| `statutory` | 2 |
| `regulatory` | 3 |
| `operational` | 4 |
| `advisory` | 5 |

Enum values are presentation; all comparisons use `priority_level` integers.

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
| **Array ordering** | Classified per §2.16.1 — ordered arrays preserve insertion order; unordered arrays sorted lexicographically before hashing |
| **Float precision** | IEEE 754 double; no rounding before hashing |
| **Hash algorithm** | SHA-256 |

**Canonical JSON:** All objects are serialized with sorted keys before hashing.

**Normalization Rules (pre-serialization):**
- Objects with `additionalProperties: true` have their keys sorted lexicographically before hashing
- Schema `$ref` references are resolved at validation time only; NOT included in canonical form for hashing
- Default values specified in schema are NOT injected into canonical form — only explicit values in the instance participate in hashing
- Explicit `null` values are preserved (not omitted)

#### 2.16.1 Array Ordering Classification

| Array Field | Ordering | Serialization Rule |
| :--- | :--- | :--- |
| `sub_evaluators` | **Ordered** | Preserve author insertion order (logic evaluation order matters) |
| `depends_on` | **Unordered (semantic set)** | Sort `directive_id` strings lexicographically |
| `conflicts_with` | **Unordered (semantic set)** | Sort strings lexicographically |
| `parent_lineage_ids` | **Unordered (semantic set)** | Sort lexicographically |
| `parent_execution_ids` | **Unordered (semantic set)** | Sort lexicographically |
| `node_hashes` (snapshot) | **Unordered (semantic set)** | Sort lexicographically |
| `edge_hashes` (snapshot) | **Unordered (semantic set)** | Sort lexicographically |
| `skipped_nodes` (inspection) | **Ordered** | Preserve pipeline execution order |
| `pipeline_trace` | **Ordered** | Preserve chronological order |

**Recursive Structures:**
- **Composite evaluators:** `sub_evaluators` are serialized as an **ordered** array of canonical JSON objects
- **Lineage:** `parent_lineage_ids` and `parent_execution_ids` are **unordered** — sorted lexicographically before hashing
- **Schema references ($ref):** Resolved at schema validation time only; NOT included in canonical form for hashing
- **Map ordering:** Objects with `additionalProperties: true` have keys sorted lexicographically before hashing

**DAG Reference Hashing (CG-IR):**
- `depends_on` is serialized as a sorted array of `directive_id` strings — neighbor node content is NOT embedded
- Edge objects hash `{source, target}` directive_id pairs independently of node bodies
- Snapshot manifest composes sorted `node_hash[]` + sorted `edge_hash[]` — shared node reuse across snapshots preserves hash identity (see Section 2.6)
- Acyclicity is enforced at compile time before hashing; no cycle-chasing in hash computation

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

**Intentional Exclusion — Event Stream Ordering:** The `system_state_hash` captures inspection reproducibility, NOT event stream ordering. Event ordering is guaranteed by the HLC (§2.14) and is recorded independently in the Finding Event Stream via `event_hash` and `logical_clock` fields. Including event stream state in `system_state_hash` would create a circular dependency (inspection depends on events, events depend on inspection). The five dimensions above are sufficient to reproduce any inspection deterministically.

**CG-IR Hash Binding Clarification:** The `cg_ir_hash` used in the system_state_hash formula refers to `cg_ir_snapshot_hash` as defined in §2.6. The `system_state_hash` is a second-level composition that additionally includes `target_hash` and `directive_graph_version`. This ensures full inspection reproducibility across directive state, execution target, compiled CG-IR snapshot, and engine + environment context.

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
               ┌────│    Open     │────┐────────┐
               │    └──────┬──────┘    │        │
               │           │           │        │
        ┌──────▼──────┐    │    ┌──────▼──────┐ │  ┌──────────┐
        │  Acknowledged│    │    │  Dismissed  │ │  │  Waived  │
        │  (In Remedy) │    │    │  (Invalid)  │ │  │  (Risk)  │
        └──────┬──────┘    │    └─────────────┘ │  └────┬─────┘
               │           │                    │       │
        ┌──────▼──────┐    │                    │       │
        │  Evidence    │    │                    │       │
        │  Submitted   │    │                    │       │
        └──────┬──────┘    │                    │       │
               │           │                    │       │
        ┌──────▼──────┐    │                    │       │
        │  Pending     │    │                    │       │
        │  Verification│    │                    │       │
        └──────┬──────┘    │                    │       │
               │           │                    │       │
      ┌────────┴────────┐  │                    │       │
      │                 │  │                    │       │
┌─────▼─────┐    ┌──────▼──────┐              │       │
│  Verified  │    │  Rejected   │              │       │
│  (Resolved)│    │  (Reopen)   │              │       │
└─────┬─────┘    └──────┬──────┘              │       │
      │                 │                     │       │
      │    ┌────────────┘                     │       │
      │    │                                  │       │
┌─────▼─────┐                                 │       │
│   Closed  │◄────────────────────────────────┘       │
└───────────┘                                         │
      ▲                                               │
      └───────────────────────────────────────────────┘
```

**State Transitions:**

| From | To | Trigger | Allowed Actor |
| :--- | :--- | :--- | :--- |
| Created | Open | System (automatic) | System |
| Open | Acknowledged | S-12 (acknowledge) | Compliance Representative |
| Open | Dismissed | Disposition = Invalid | Regulatory Official |
| Open | Waived | S-25 (waive) | Regulatory Official |
| Acknowledged | Evidence Submitted | S-13 (submit evidence) | Compliance Representative |
| Evidence Submitted | Pending Verification | System (automatic) | System |
| Pending Verification | Verified | S-14 (approve) | Regulatory Official |
| Pending Verification | Rejected | S-14 (reject) | Regulatory Official |
| Rejected | Open | Reopen with comments | Regulatory Official |
| Verified | Closed | System (automatic) | System |
| Waived | Closed | System (automatic) | System |

**Disposition Values:**

| Disposition | Meaning |
| :--- | :--- |
| `valid` | Finding is legitimate; requires remediation |
| `invalid` | Finding is incorrect; no action needed |
| `waived` | Finding is legitimate but accepted as risk |

**Finding Object Schema:**

```json
{
  "finding_id": "string (required, UUID)",
  "lineage_id": "string (required, → CG-IR node lineage_id)",
  "control_id": "string (required, → CG-IR node directive_id)",
  "inspection_id": "string (required, UUID)",
  "fsm_state": "enum (required, Created | Open | Acknowledged | Evidence Submitted | Pending Verification | Verified | Rejected | Dismissed | Waived | Closed)",
  "disposition": "enum (valid | invalid | waived)",
  "severity": "enum (critical | high | medium | low | informational)",
  "outcome": "enum (Pass | Fail | Partial | NeedsReview, from evaluator contract §2.9)",
  "confidence": "float (0.0–1.0, from evaluator contract §2.9)",
  "evidence": "string (from evaluator contract §2.9)",
  "reasoning": "string (from evaluator contract §2.9)",
  "created_at": "datetime (required, ISO 8601, UTC)",
  "updated_at": "datetime (required, ISO 8601, UTC)",
  "actor": "string (actor ID of last state transition)"
}
```

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

**Runtime Enforcement Points:**

| Pipeline Stage | Gate | Capabilities Checked | Failure Semantics |
| :--- | :--- | :--- | :--- |
| **Request ingress** | API Gateway / Command Handler | All mutating capabilities before dispatch | `403 CapabilityDenied`; no state mutation; audit log entry with actor, requested action, denial reason |
| **Directive mutations** | Directive Drafting / Compilation Engine | `directive.*` capabilities | Reject before write lock acquired; no partial Directive Graph update |
| **Inspection submit** | Inspection Pipeline entry | `inspection.submit`, `inspection.reinspect` | Reject before target validation; no inspection snapshot created |
| **Finding FSM transitions** | Finding FSM Engine | Per-transition capability (e.g., `finding.acknowledge`, `finding.approve_remediation`) | Reject transition; FSM state unchanged; no event appended |
| **Conflict resolution** | Conflict Resolution Engine | `conflict.resolve` | Reject; Conflict Artifact remains open |
| **Analytics** | Analytics Engine | `analytics.view` | Reject; no aggregate data returned |

**Failure Semantics (uniform):**
- Deny = hard reject; no partial writes, no compensating events, no degraded-mode execution
- All denials produce an append-only audit record: `{actor, capability, action, outcome: denied, timestamp, reason}`
- Escalation is NOT automatic on denial; caller receives error and decides next action

**Delegation Model:** Not supported in v8.1.0. Capabilities bind directly to authenticated actor identity. AI agents use the same capability matrix with `actor` set to agent ID.

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
- Nodes with identical `node_body` share storage (same `node_hash`) — hash is local to node content (Section 2.6)
- Edges are stored once per unique (source, target) pair
- Snapshots reference nodes/edges by hash, not copy
- Incremental compilation reuses prior `node_hash` values when `node_body` is unchanged; snapshot hash still changes if graph topology or provenance differs
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
  "cg_ir_snapshot_hash": "string (SHA-256 of CG-IR snapshot, per §2.6)",
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

### 3.7 Pipeline Trace Entry

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
| `Machine ID` / `rule.lineage_id` | ✅ Allowed (lineage root only) | ✅ Required | ✅ Defined |
| `rule.id` (execution ID) | ❌ Not represented | ✅ Required | ✅ Defined |
| `evaluator_type` | ❌ Prohibited | ✅ Required | ✅ Defined |
| `evaluator_config` | ❌ Prohibited | ✅ Required | ✅ Defined |
| `lineage` | ❌ Prohibited | ⚠️ Conditional | ✅ Defined |
| `priority_hierarchy` | ✅ Declarative | ✅ As `priority` field | ✅ Defined |
| `conflict_resolution_intent` | ✅ Declarative | ✅ As `conflict_resolution` field | ✅ Defined |
| `conflict_resolution` | ❌ Prohibited | ✅ Optional override | ✅ Defined |

**Note:** Priority hierarchy and conflict resolution are DECLARATIVE DESCRIPTIONS of governance intent in policy. Human authors use them when setting schema fields (`priority`, `conflict_resolution`). The runtime engine executes ONLY Section 2.15 over schema/CG-IR fields — policy prose is never read at runtime.

---

## 7. Rule Schema Contract

See `rule_schema.json` for the formal JSON Schema.

Key fields: `id` (canonical identity), `type`, `message`, `evaluator_type` (pure only), `evaluator_config`, `depends_on`, `priority`, `lineage` (fork/merge/split tracking).

### 7.1 Metadata Namespacing

The root `metadata` object and per-rule `metadata` (if present) are **informational only**. They MUST NOT contain executable hints, evaluator configuration, or runtime flags.

**Required namespace structure:**

```json
{
  "metadata": {
    "audit": {
      "authored_by": "string (actor ID)",
      "approved_by": "string (actor ID, optional)",
      "approved_at": "datetime (ISO 8601 UTC, optional)"
    },
    "vendor": {},
    "author": {},
    "migration": {
      "superseded_by": "string (rule id, when status=superseded)",
      "migration_notes": "string (optional)"
    }
  }
}
```

- `additionalProperties` outside declared namespaces is PROHIBITED at root `metadata`
- Unknown keys within a namespace MAY be rejected with warning at compile time
- Metadata does NOT participate in `semantic_hash` unless explicitly declared in a future spec version

### 7.2 Anchor Reference Syntax

`anchor_ref` MUST conform to:

```
anchor_ref ::= section_ref | json_pointer

section_ref ::= "section:" section_id ["/" subsection_id]

section_id ::= "preamble" | "governance" | "definitions" | "principles"
             | "directives" | "sanctions" | "references"

json_pointer ::= "/" path_segment ("/" path_segment)*
```

**Examples:**
- `section:directives/specific_directives`
- `section:definitions`
- `/directives/TRAF-001`

Compile-time validation MUST verify `section:` references against policy document structure. Invalid references produce warnings; missing policy sections produce errors.

---

## 8. System Invariants

| Invariant | Description |
| :--- | :--- |
| **Normative Source** | SPECIFICATION.md is the single normative source; schema and policy MUST conform |
| **Dual Identity** | Lineage ID (immutable root) + Execution ID (active node identity) |
| **Lineage ID Immutability** | Once assigned, lineage_id root is never reused; multiple active rules may share lineage_id after fork/split |
| **Execution ID Stability** | Execution ID changes only on fork/merge/split; globally unique within ruleset |
| **Rule-Level Uniqueness** | (lineage_id, id) pair is unique; id alone is also globally unique |
| **Hermetic Compilation** | CG-IR reproducibility requires pinned frozen_env |
| **CG-IR Snapshot Immutability** | Once published, a snapshot is immutable; compilation creates new snapshots |
| **CG-IR Content Addressing** | Snapshot hash = SHA-256(sorted node_hashes + sorted edge_hashes + provenance). Identical inputs → identical hash (§2.6). |
| **CG-IR Snapshot Hash Determinism** | cg_ir_snapshot_hash is a function of directive graph content, engine version, and frozen env only. compiled_at is NOT included in snapshot hash (execution artifact metadata only). |
| **CG-IR Edge Hash Formula** | edge_hash = SHA-256(canonical_json({source: directive_id, target: directive_id})). Directional. Independent of node content. |
| **Provenance Canonicalization** | All provenance fields MUST be canonicalized before inclusion in hash computation; no non-deterministic ordering |
| **Finding Event Immutability** | Append-only; event_hash ensures integrity |
| **Finding FSM** | Findings follow strict state transitions (see Section 3.1) |
| **Inspection Immutability** | Completed snapshots never modified |
| **Evaluator Purity** | Pure functions: no IO, no randomness |
| **Evaluator Type Safety** | evaluator_config MUST match evaluator_type (schema-enforced if/then) |
| **Evaluator Portability** | RE2-compatible regex only; IEEE 754 strict numerics; UTC-only timestamps; NFC-normalized strings |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver; Evidence submitter ≠ Approver |
| **Capability Enforcement** | All actions checked against capability matrix |
| **Mediated Feedback** | Analytics inform humans; no direct finding → CG-IR |
| **Declarative Governance** | Policy describes authoring intent only; runtime engine reads schema/CG-IR fields via spec algorithm |
| **Policy Runtime Prohibition** | policy_doctrine.yaml MUST NOT be read during inspection, evaluation, or FSM transitions |
| **Machine ID Semantics** | Machine ID = stable lineage root; bijective at root-assignment level; fork/split allows shared lineage_id with distinct execution_ids |
| **CG-IR Local Node Hashing** | node_hash depends on node_body only; graph context captured in edges and snapshot manifest |
| **Deterministic Serialization** | Canonical JSON with sorted keys; NaN/Infinity prohibited; DAG refs by sorted directive_id |
| **HLC Event Ordering** | physical_time → logical_counter → node_id → event_id; per-node tuple strictly non-decreasing |
| **system_state_hash Scope** | Captures inspection reproducibility only; event ordering excluded (circular dependency avoidance) |
| **Conflict Resolution Temporal Binding** | created_at is frozen in CG-IR node_body; conflict outcomes are snapshot-bound, not evaluation-time-dependent |
| **Version Compatibility** | MAJOR versions match across spec/schema/policy |
| **Cross-Layer Binding** | Schema MUST conform to spec; policy MUST NOT contradict spec |
| **Concurrency Safety** | Compilation = read lock; modification = write lock |
| **Evaluator Complexity Bounds** | Depth ≤ 32, total nodes ≤ 256, width ≤ 64, regex ≤ 4096 chars (§2.9) |
| **Lineage DAG Acyclicity** | Ancestry graph acyclic; max depth 64 (§2.2.3) |
| **Specificity Determinism** | `specificity_score` algorithm in §2.15 is normative |
| **Semantic/Presentation Hash Split** | `semantic_hash` excludes description; `node_hash` composes both (§2.6) |
| **Array Ordering Classification** | Ordered vs unordered arrays per §2.16.1 |
| **Metadata Informational Only** | Namespaced metadata; no executable content (§7.1) |
| **Merge Identity Determinism** | Merged `lineage_id` = lexicographic min of parents (§2.2.2) |

---

## 9. Validation

### 9.1 Identity Validation

1. Every lineage_id in policy exists as rule.lineage_id in schema
2. Every rule.lineage_id has a Machine ID in policy
3. Every CG-IR node.lineage_id matches a rule.lineage_id
4. No orphan lineage_ids in any layer
5. lineage_id matches pattern: `^[A-Z][A-Z0-9]+-[0-9]+$`
6. execution_id matches pattern: `^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$`
7. No duplicate lineage_id ROOT values within a ruleset (post-fork/split, multiple active rules may share the same lineage_id with distinct execution_ids)
8. Lineage field is present for fork/merge/split operations
9. Lineage field is absent for revision/rename/retire operations
10. Machine ID ↔ lineage_id root is bijective within ruleset (no duplicate roots, no orphan lineage roots)
11. On first creation, rule.id equals rule.lineage_id unless lineage operation dictates otherwise
12. Rule-level uniqueness: `(lineage_id, id)` pair is unique within a ruleset
13. Execution ID uniqueness: `id` is globally unique within a ruleset (no two active rules share the same execution_id)

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
6. Regex patterns validated for RE2 compatibility (no backreferences, no atomic groups, no PCRE-only features)
7. Regex flags limited to: `i`, `m`, `s`
8. No NaN or Infinity in evaluator_config numeric values
9. No timezone-dependent operations in evaluator logic
10. Composite recursion depth ≤ 32
11. Total evaluator nodes per rule ≤ 256
12. Composite width (`sub_evaluators` count) ≤ 64 at any level
13. Regex pattern length ≤ 4096 characters
14. Cross-field discriminator: `evaluator_type` ↔ `evaluator_config` verified by compile-time validator (not partial subschema validation alone)

### 9.3 CG-IR Validation

1. All nodes reference valid lineage_ids
2. DAG is acyclic
3. Content hash matches ruleset version
4. Frozen environment metadata complete
5. Snapshot is immutable (no mutation after publish)
6. Node hashes are content-addressed (identical `node_body` = identical `node_hash`)
7. `node_hash` excludes graph position and neighbor content (local scope only)
8. `depends_on` contains sorted directive_id references only
9. Incremental reuse preserves `node_hash` when `node_body` unchanged across snapshots

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
6. Per-node HLC tuple is strictly lexicographically non-decreasing
7. Wall clock regression does not produce a regressive HLC tuple

### 9.6 Permission Validation

1. All actions checked against capability matrix (Section 3.2) at defined enforcement gates
2. Segregation of duties enforced (creator ≠ waiver, submitter ≠ approver)
3. AI agent actions logged with actor identity
4. Denied requests produce no partial state mutation and no compensating events
5. Capability checks occur before FSM transition and before Directive Graph write lock

### 9.7 Cross-Layer Validation

1. Spec, schema, and policy MAJOR versions match
2. No schema element contradicts a spec invariant
3. No policy field violates contamination guard
4. evaluator_config fields match evaluator_type (no invalid state combinations)
5. Runtime engines do not read policy_doctrine.yaml (verified by architecture audit)
6. Conflict resolution at runtime uses spec algorithm over schema/CG-IR fields only
7. `anchor_ref` conforms to §7.2 syntax
8. `metadata` uses declared namespaces only; no executable hints
9. Lineage DAG satisfies §2.2.3 invariants (acyclicity, depth ≤ 64)
10. Merge operations produce lineage_id per §2.2.2 deterministic algorithm

### 9.8 Schema Annotation Status

All `x-*` keys in `rule_schema.json` are **informative and non-normative**. They document cross-layer bindings for human maintainers. On conflict between an `x-*` annotation and this specification, **this specification wins**.

---

## 10. References

- `docs/Regulation/policy_doctrine.yaml` — Policy contract (declarative governance)
- `docs/Regulation/rule_schema.json` — Rule schema (machine structure)
- `docs/User-Story/User_Stories.md` — User stories (behavioral contract)

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
| 8.1.1 | 2026-07-05 | Architectural review: policy runtime prohibition, Machine ID single interpretation, HLC monotonicity under clock regression, CG-IR local node hashing scope, capability enforcement gates, DAG reference hashing |
| 8.1.2 | 2026-07-05 | CG-IR snapshot hash determinism: explicit composition formula (node_hashes + edge_hashes + provenance), system_state_hash binding clarification, snapshot hash determinism invariant |
| 8.2.0 | 2026-07-05 | Design review corrections: identity model refinement (bijection at root-assignment level, fork/split shared lineage_id), explicit edge hash formula, provenance canonicalization requirement, evaluator portability constraints (RE2 regex, IEEE 754, UTC timestamps, NFC strings), conflict resolution temporal binding guarantee, system_state_hash intentional exclusion documentation, compiled_at removed from snapshot hash |
| 8.2.1 | 2026-07-05 | Architecture audit corrections: formal specificity algorithm, deterministic merge semantics, lineage DAG invariants, evaluator complexity limits, semantic/presentation hash split, ordered/unordered array classification, metadata namespacing, anchor_ref syntax, terminology glossary, x-* informative-only declaration, discriminator validation requirement |
