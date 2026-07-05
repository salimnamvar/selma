# Universal Rule Governance Specification

**Version:** 7.0.0  
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
5. All three documents MUST share synchronized versions (all at 7.0.0)
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

One directive has ONE identifier across all layers:

| Layer | Field | Example |
| :--- | :--- | :--- |
| Policy Doctrine | `Machine ID` | `TRAF-001` |
| Rule Schema | `rule.id` | `TRAF-001` |
| CG-IR | `node.directive_id` | `TRAF-001` |
| Finding | `finding.control_id` → node | `TRAF-001` |

**Invariant:** `Machine ID` = `rule.id` = `node.directive_id`.

### 2.3 Identity Lifecycle Rules

| Operation | Rule | New ID Required |
| :--- | :--- | :--- |
| **Revision** | Changes description, parameters, scope, or evaluator within same semantic intent | No — same ID, new revision |
| **Fork** | Splits one directive into two with distinct semantic intent | Yes — two new IDs |
| **Merge** | Combines two directives into one with unified semantic intent | Yes — one new ID; old IDs deprecated |
| **Split** | Restructures a directive into multiple independent directives | Yes — new IDs for each; old ID deprecated |
| **Rename** | Changes display name but not semantic intent | No — same ID |
| **Retire** | Removes from active enforcement | No — ID preserved, status = deprecated |

**Identity Immutability:** Once a Machine ID is assigned, it is never reused. Deprecated IDs remain in the audit trail forever.

**Lineage Tracking:** When a directive is forked/merged/split, the `lineage` field records the parent IDs:

```json
{
  "id": "TRAF-001-A",
  "lineage": {
    "operation": "fork",
    "parent_ids": ["TRAF-001"],
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
    │ Ensure Machine ID = rule.id = directive_id
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
  "actor": "string (required, human ID or AI agent ID)",
  "payload": "object (event-specific data)",
  "event_hash": "string (required, SHA-256 of event_id + finding_id + event_type + timestamp + payload)"
}
```

**Event Ordering:** Strict total ordering by timestamp. Ties broken by event_id (lexicographic).

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
| "Explicit override wins" | `has_field(conflict_resolution)` | Boolean: does rule have explicit override? |

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

apply_strategy(strategy, rule, other_rule) → winning_rule:
  - "always_wins": return rule
  - "never_wins": return other_rule
  - "defer_to": return rule with ID = strategy.defer_to
```

### 2.16 Deterministic Serialization Rules

For reproducibility, all hashing uses:

| Rule | Specification |
| :--- | :--- |
| **JSON key ordering** | Alphabetical (lexicographic) |
| **Number encoding** | Integer as integer, float as IEEE 754 double |
| **String encoding** | UTF-8, no BOM |
| **Datetime encoding** | ISO 8601 with UTC timezone (`YYYY-MM-DDTHH:MM:SSZ`) |
| **Null handling** | Explicit `null`, not omitted |
| **Array ordering** | Preserved as-is (insertion order) |
| **Float precision** | IEEE 754 double; no rounding before hashing |
| **Hash algorithm** | SHA-256 |

**Canonical JSON:** All objects are serialized with sorted keys before hashing.

**Recursive Structures:**
- **Composite evaluators:** `sub_evaluators` are serialized as an ordered array of canonical JSON objects
- **Lineage:** `parent_ids` are sorted lexicographically before hashing
- **Schema references ($ref):** Resolved at schema validation time only; NOT included in canonical form for hashing

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

### 3.1 Inspection Snapshot

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

**Version Synchronization Rule:** SPECIFICATION.md version, rule_schema.json version, and policy_doctrine.yaml version MUST be identical (e.g., all at 7.0.0). The engine rejects version mismatches.

**Compatibility Rules:**

| Scenario | Requirement |
| :--- | :--- |
| Evaluate CG-IR | Engine version must be >= CG-IR schema version |
| Compile Directive Graph | Engine version must support Directive Graph schema |
| Reproduce inspection | Pin: frozen_env_hash + CG-IR hash + target_hash + engine_version |
| Migrate schema | Use migration tool; legacy snapshots remain with pinned engine |
| Version mismatch | Spec version = schema version = policy version; engine rejects mismatches |

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
| **Canonical Identity** | One ID across all layers: Machine ID = rule.id = directive_id |
| **Identity Immutability** | Once assigned, a Machine ID is never reused |
| **Identity Uniqueness** | rule.id MUST be unique within a ruleset (enforced by pattern + validation) |
| **Hermetic Compilation** | CG-IR reproducibility requires pinned frozen_env |
| **CG-IR Snapshot Immutability** | Once published, a snapshot is immutable; compilation creates new snapshots |
| **Finding Event Immutability** | Append-only; event_hash ensures integrity |
| **Inspection Immutability** | Completed snapshots never modified |
| **Evaluator Purity** | Pure functions: no IO, no randomness |
| **Evaluator Type Safety** | evaluator_config MUST match evaluator_type (discriminated union) |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver |
| **Mediated Feedback** | Analytics inform humans; no direct finding → CG-IR |
| **Declarative Governance** | Policy describes intent; engine implements logic |
| **Deterministic Serialization** | Canonical JSON with sorted keys for all hashing |
| **Event Ordering** | Strict total order by timestamp; ties by event_id |
| **Version Forward-Only** | No downgrades; legacy snapshots pinned to engine versions |
| **Version Synchronization** | Spec version = schema version = policy version |
| **Cross-Layer Binding** | Schema MUST be derivable from spec invariants; no independent semantics |
| **Lineage Enforcement** | Fork/merge/split MUST have lineage field; revision/rename/retire MUST NOT |

---

## 9. Validation

### 9.1 Identity Validation

1. Every Machine ID in policy exists as rule.id in schema
2. Every rule.id has a Machine ID in policy
3. Every CG-IR node.directive_id matches a rule.id
4. No orphan IDs in any layer
5. rule.id matches pattern: `^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$`
6. No duplicate rule.id values within a ruleset
7. Lineage field is present for fork/merge/split operations
8. Lineage field is absent for revision/rename/retire operations

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

1. All nodes reference valid directive_ids
2. DAG is acyclic
3. Content hash matches ruleset version
4. Frozen environment metadata complete
5. Snapshot is immutable (no mutation after publish)

### 9.4 Inspection Validation

1. Target hash matches submitted target
2. CG-IR hash matches published version
3. Frozen environment hash matches CG-IR provenance
4. Pipeline trace complete
5. System state hash correctly computed

### 9.5 Event Validation

1. All events have valid event_hash
2. Events are in strict timestamp order
3. finding_id references valid finding
4. No duplicate event_ids

### 9.6 Cross-Layer Validation

1. Schema version = spec version = policy version
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
