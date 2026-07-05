# Universal Rule Governance Specification

**Version:** 5.0.0  
**Status:** Draft Standard  
**Date:** 2026-07-05

---

## 1. Introduction

### 1.1 Purpose

This specification defines a universal framework for creating, maintaining, and enforcing rules across any domain. The system is built on **three runtime primitives**:

1. **Directive Graph** — The human-authored source-of-truth specification
2. **Compiled Control DAG (CG-IR)** — The immutable executable intermediate representation
3. **Finding Event Stream** — The append-only audit log with read-only analytics

Everything else is a documentation, rendering, or analytics layer on top of these three primitives.

### 1.2 Scope

This standard applies to:
- Policy documents (prose rules, governance documents, standards)
- Machine-executable rules (automated enforcement, validation, compliance)
- Control derivation (translating directives into testable conditions)
- Inspection execution (evaluating targets against controls)
- Finding lifecycle (detection, disposition, remediation, closure)
- Systems that bridge human understanding and machine execution

### 1.3 Audience

- Policy authors and governance bodies
- Software engineers building rule engines
- Compliance officers and auditors
- Standards organizations

---

## 2. Architecture

### 2.1 Three Runtime Primitives

```
┌─────────────────────────────┐
│   1. Directive Graph        │
│   (source-of-truth spec)    │
│   - Human-authored rules    │
│   - Structured metadata     │
│   - Versioned as artifact   │
└──────────────┬──────────────┘
               │ compile (hermetic boundary)
               ▼
┌─────────────────────────────┐
│   2. Compiled Control DAG   │
│   (= CG-IR)                 │
│   - Content-addressed       │
│   - Incremental snapshots   │
│   - Frozen at publish time  │
└──────────────┬──────────────┘
               │ evaluate (pure functions)
               ▼
┌─────────────────────────────┐
│   3. Finding Event Stream   │
│   - Append-only events      │
│   - Computed state          │
│   - Read-only analytics     │
│   - Mediated feedback       │
└─────────────────────────────┘
```

### 2.2 The Directive Graph

The Directive Graph is the human-authored source of truth. It is a **structured, versioned artifact** that can be validated, diffed, and migrated.

| Aspect | Description |
| :--- | :--- |
| **Format** | Structured document (YAML/JSON with prose sections) |
| **Versioning** | Semantic versioning (MAJOR.MINOR.PATCH) |
| **Mutability** | Mutable (new revisions created on change) |
| **Content** | Directives, scope, priority, prose sections, metadata |
| **Validation** | Schema-validated at compile time |

### 2.3 The Compiled Control DAG (CG-IR)

The CG-IR is the immutable, executable intermediate representation. All directives compile into it. The Ruleset Version is its content-addressed hash.

| Aspect | Description |
| :--- | :--- |
| **Format** | Directed Acyclic Graph of control nodes |
| **Versioning** | Content-addressed (SHA-256 hash) |
| **Mutability** | Immutable once published |
| **Content** | Control nodes, edges (dependencies), evaluation logic |
| **Validation** | DAG structure validated at compile time |

**Incremental Compilation:**

Instead of full recompilation on every change, Selma supports delta CG-IR snapshots:

| Change Type | Compilation Strategy |
| :--- | :--- |
| Add new directive | Append new nodes to existing DAG; reuse unchanged subgraph |
| Modify directive | Recompile only affected nodes and their dependents |
| Remove directive | Mark nodes as deprecated; reuse rest of DAG |
| Change evaluator logic | Recompile only the affected node |
| Change dependency edges | Recompile affected edges; reuse node evaluations |

**Node-Level Version Inheritance:**

When a directive changes, only the nodes derived from it get new versions. Unchanged nodes inherit their previous version. This means:
- CG-IR snapshots share common subgraphs
- Historical inspections can reference specific node versions
- Storage cost scales with change frequency, not total rule count

### 2.4 The Hermetic Compilation Boundary

The boundary between Directive Graph and CG-IR is the **hermetic boundary**. The compilation environment is fully frozen to ensure reproducibility.

```
Directive Graph
        │
        ▼ compile(frozen_env)
   ┌─────────────────────────────────────┐
   │     HERMETIC COMPILATION BOUNDARY   │
   │                                     │
   │  Frozen environment:                │
   │  - Engine version                   │
   │  - Model weights (if AI-assisted)   │
   │  - System prompts (if AI-assisted)  │
   │  - Decoding parameters              │
   │  - Toolchain version                │
   │                                     │
   │  All outputs cached and serialized  │
   │  into CG-IR before publication      │
   └─────────────────────────────────────┘
        │
        ▼
   CG-IR (deterministic given frozen_env)
        │
        ▼ evaluate(pure_functions)
   Findings (deterministic)
```

**Hermeticity Rules:**
1. Compilation is reproducible only when the entire environment is frozen
2. The frozen environment is recorded in CG-IR provenance metadata
3. To reproduce a historical CG-IR, pin: engine version + model version + system prompt hash + toolchain version
4. AI-assisted compilation outputs are cached and serialized into CG-IR
5. Once CG-IR is published, it is immutable

**Reproducibility Guarantee:**

| Scenario | Reproducibility |
| :--- | :--- |
| Same Directive Graph + same frozen_env | Same CG-IR (guaranteed) |
| Same Directive Graph + different frozen_env | May differ (environment-dependent) |
| Same CG-IR + same target | Same findings (guaranteed) |
| Same CG-IR + different engine version | May fail (schema compatibility required) |

### 2.5 CG-IR Node Schema

Each node in the CG-IR DAG:

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | String | Unique identifier (e.g., `CTRL-REG-024-01`) |
| `directive_id` | String | Source directive identifier |
| `directive_revision` | String | Revision of source directive |
| `control_version` | String | Version of this node's evaluation logic |
| `description` | String | Human-readable description |
| `evaluator` | Object | Evaluation function specification (see Section 2.6) |
| `scope` | Object | Applicability context |
| `severity_default` | Enum | Default severity on failure |
| `depends_on` | Array | Node IDs that must be evaluated first |
| `status` | Enum | `active`, `deprecated` |

### 2.6 Formal Evaluator Contract

Evaluators are **pure functions** with strict constraints:

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
| **Determinism** | Same inputs always produce same outputs. |
| **Allowed operations** | String matching, regex, arithmetic, field extraction, comparison |
| **Prohibited operations** | HTTP calls, database queries, file reads, environment variable access |
| **Context object** | Read-only. Contains: target metadata, historical aggregates (see Section 2.7), domain constants |
| **Canonical serialization** | Inputs and outputs are JSON-serializable with deterministic key ordering |

**Evaluator Types:**

| Type | Description | Guarantee |
| :--- | :--- | :--- |
| `regex` | Pattern matching against target content | Fully deterministic |
| `field_check` | Validates specific fields in structured targets | Fully deterministic |
| `threshold` | Numeric comparison against configured limits | Fully deterministic |
| `composite` | Boolean combination of sub-evaluators | Fully deterministic |
| `cached_ai` | AI-generated logic, frozen at compile time | Deterministic given frozen CG-IR |

### 2.7 Context Object (State-Dependent Evaluation)

The context object provides read-only historical state to evaluators, enabling state-dependent rules without breaking purity:

| Field | Type | Description |
|-------|------|-------------|
| `target_metadata` | Object | Hash, type, submission time of current target |
| `domain_constants` | Object | Jurisdiction, domain, scope filters |
| `finding_aggregates` | Object | Pre-computed aggregates from Finding Event Stream |
| `previous_inspections` | Object | Summary of prior inspections for this target |

**Finding Aggregates (read-only):**

| Field | Type | Description |
|-------|------|-------------|
| `total_open_findings` | Integer | Count of open findings for this target |
| `findings_by_severity` | Map | `{ severity: count }` |
| `findings_by_control` | Map | `{ control_id: count }` |
| `last_inspection_date` | DateTime | When this target was last inspected |
| `recurrence_count` | Integer | How many times this control has failed for this target |

**No Write-Back:** Context is populated by the DAG Evaluation Engine from the Finding Event Stream at inspection time. Evaluators cannot modify context.

### 2.8 DAG Execution Semantics

| Aspect | Rule |
| :--- | :--- |
| **Evaluation Order** | Topological sort respecting `depends_on` edges |
| **Cycle Detection** | Enforced at compile time. Cycles cause compilation failure. |
| **Parallel Execution** | Nodes with no interdependency execute in parallel |
| **State Propagation** | Each node receives context (read-only) + target; no shared mutable state |
| **Failure Handling** | See Section 2.9 |
| **Timeout** | Each node has a configurable timeout (default: 30s) |
| **Retry** | No automatic retries; failed nodes produce `NeedsReview` findings |

### 2.9 Pipeline Failure Semantics

| Failure Mode | Behavior |
| :--- | :--- |
| **Single node timeout** | Node produces `NeedsReview` finding; other nodes continue |
| **Single node error** | Node produces `NeedsReview` finding; other nodes continue |
| **Dependency failure** | Dependent nodes are skipped; skip event logged |
| **Cycle detected** | Compilation fails; no CG-IR published |
| **Schema mismatch** | Compilation fails; migration required |
| **Engine version mismatch** | Evaluation fails; pinned engine version required |

**Pipeline is NOT atomic.** Partial results are valid. Each node's outcome is independent unless blocked by dependency failure.

### 2.10 Finding Event Stream

Findings are append-only event logs. Current state is computed by replaying events.

**Events:**

| Event Type | Fields | Description |
| :--- | :--- | :--- |
| `FindingCreated` | finding_id, inspection_id, control_id, severity, description, evidence, reasoning | Initial creation |
| `DispositionChanged` | finding_id, old_disposition, new_disposition, actor, reason, timestamp | Disposition update |
| `FindingClosed` | finding_id, actor, reason, timestamp | Lifecycle closure |

**Computed State (derived from event log):**

| Field | Source |
|-------|--------|
| `lifecycle_status` | Computed from `FindingCreated` + `FindingClosed` events |
| `disposition` | Computed from `DispositionChanged` events |
| `severity` | Set at creation, immutable |

**Read-Only Analytics View:**

The Finding Event Stream provides a read-only analytics substrate:

| Analytics | Description |
| :--- | :--- |
| `finding_aggregates` | Pre-computed aggregates fed into context object |
| `trend_analysis` | Finding rates over time (read-only, does not influence CG-IR) |
| `anomaly_detection` | Statistical outliers in finding patterns (read-only) |
| `compliance_dashboard` | Real-time compliance posture view |

**Mediated Feedback:**

The Finding Event Stream can inform human-driven policy evolution through an **external, auditable process**:

```
Finding Event Stream
    ↓ (read-only analytics)
Analytics Dashboard
    ↓ (human review + decision)
Regulatory Official
    ↓ (manual directive modification)
Directive Graph
    ↓ (recompile)
New CG-IR
```

**Rules for mediated feedback:**
1. Analytics are read-only; they never directly modify CG-IR
2. All policy changes go through the standard Directive Graph → CG-IR compilation path
3. The human decision is recorded as a provenance event on the directive revision
4. Feedback loops are auditable: every directive change can be traced to its triggering analytics

---

## 3. Layered Namespace Model

Each layer has a **typed namespace** with schema validation.

### 3.1 Namespace Structure

```
Directive Graph
├── prose/          (human-readable sections)
├── directives/     (structured rule definitions)
├── metadata/       (version, jurisdiction, domain)
└── traceability/   (machine IDs, anchor refs)

CG-IR
├── nodes/          (control nodes)
├── edges/          (dependency graph)
├── evaluators/     (evaluation logic)
└── provenance/     (compilation metadata, frozen_env)

Finding Event Stream
├── events/         (immutable event log)
├── computed/       (derived state projections)
└── analytics/      (read-only aggregate views)
```

### 3.2 Cross-Layer References

| From | To | Mechanism |
| :--- | :--- | :--- |
| Directive Graph → CG-IR | `compilation` | Directive ID + revision → CG-IR hash |
| CG-IR → Directive Graph | `provenance` | CG-IR node → directive_id + revision |
| CG-IR → Findings | `evaluation` | CG-IR hash + target_hash → finding events |
| Findings → CG-IR | `causal_chain` | Finding → control_id → CG-IR node |
| Findings → Context | `aggregates` | Pre-computed aggregates fed into evaluation context |

---

## 4. Version Compatibility Matrix

### 4.1 Version Axes

| Axis | Format | Mutability |
| :--- | :--- | :--- |
| Directive Graph Version | Semantic (MAJOR.MINOR.PATCH) | Mutable (new revisions) |
| CG-IR Schema Version | Semantic (MAJOR.MINOR.PATCH) | Immutable per snapshot |
| Engine Version | Semantic (MAJOR.MINOR.PATCH) | Immutable per release |
| Model Version | String (e.g., `llm-gpt4o-2024-05-13`) | Immutable per registration |
| Frozen Environment | Content hash of compilation environment | Immutable per compilation |

### 4.2 Compatibility Rules

| Scenario | Requirement |
| :--- | :--- |
| Evaluate CG-IR with engine | Engine version must support CG-IR schema version |
| Compile Directive Graph | Engine version must support Directive Graph schema version |
| Reproduce historical inspection | Pin: frozen_env hash + CG-IR hash + target hash |
| Reproduce historical CG-IR | Pin: frozen_env hash + Directive Graph version |
| Migrate legacy CG-IR | Use migration tool matching source → target schema versions |

---

## 5. Contamination Guards (Namespace Validation)

Each namespace is validated against its schema. Cross-namespace contamination is detected at compile time.

| Namespace | Forbidden Cross-References |
| :--- | :--- |
| `prose/` | Must not contain evaluator logic, parameters, conditions |
| `directives/` | Must not contain prose governance, principles, sanctions |
| `nodes/` | Must not contain human prose, governance processes |
| `events/` | Must not contain evaluation logic, directive definitions |

---

## 6. Policy Doctrine Contract

### 6.1 Structure

| Section | Required | Content Type | Purpose |
|---------|----------|--------------|---------|
| Preamble | Yes | Prose | Explain the existential need for these rules |
| Governance & Amendment | Yes | Prose | Define how this doctrine is changed |
| Definitions | Yes | Table | Define all terms used in the document |
| Foundational Principles | Yes | Prose or Table | State high-level morals or axioms |
| Directives | Yes | Mixed | List all rules and standards |
| Sanctions & Remedies | Yes | Table | State consequences of non-compliance |
| References & Annexes | No | Prose or Table | External sources and supplementary data |

### 6.2 Directive Tables

| Column | Type | Description |
|--------|------|-------------|
| Type | Enum | Obligation, Prohibition, Permission |
| Description | String | Human-readable rule description |
| Machine ID | String | Cross-reference label (e.g., TRAF-001) |
| Context / Conditions | String | When this rule applies |

### 6.3 Writing Principles

| ID | Title | Description |
|----|-------|-------------|
| WP-001 | Precision over Ambiguity | Use exact, imperative language |
| WP-002 | Definitions First | Define every atomic term before use |
| WP-003 | Structural Integrity | Do not exceed 3 levels of nested sections |
| WP-004 | Traceability | Every substantive paragraph must link to a Machine ID |
| WP-005 | Hierarchy of Authority | Declare how conflicts are resolved |

### 6.4 Priority Hierarchy

| Level | ID | Title | Description |
|-------|-----|-------|-------------|
| 1 | constitutional | Constitutional / Foundational | Core principles that cannot be overridden |
| 2 | statutory | Statutory / Legislative | Rules enacted by authorized governing bodies |
| 3 | regulatory | Regulatory / Administrative | Rules created by agencies to implement statutory requirements |
| 4 | operational | Operational / Procedural | Day-to-day procedures implementing higher-level rules |
| 5 | advisory | Advisory / Best Practice | Recommendations that are not mandatory |

**Conflict Resolution:**
1. Higher priority level wins
2. If same level: more specific rule wins
3. If same specificity: newer rule wins
4. If same age: rule with explicit conflict resolution wins

---

## 7. Rule Schema Contract

### 7.1 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Stable unique identifier |
| `type` | String | Classification (obligation, prohibition, permission, standard) |
| `message` | String | Human-readable output or description |

### 7.2 Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `target` | String | Who or what this rule applies to |
| `status` | String | Lifecycle state (draft, active, deprecated, superseded) |
| `anchor_ref` | String | Link back to human document section |
| `evaluator_hint` | String | How to evaluate (regex, field_check, threshold, composite) |
| `weight` | String | Priority/severity (critical, informative) |
| `depends_on` | Array | IDs of rules that must be evaluated first |
| `conflicts_with` | Array | IDs of rules that cannot coexist |
| `created_at` | DateTime | Timestamp of creation |
| `expires_at` | DateTime | Timestamp after which rule is obsolete |
| `parameters` | Object | Configuration key-value store |
| `conditions` | Object | Activation logic |
| `rationale` | String | Why this rule exists |
| `remediation` | String | What to do if violated |
| `complexity` | Object | Controls rule nesting and evaluation limits |
| `priority` | Enum | Authority level from policy hierarchy |

---

## 8. Inspection Model

### 8.1 Inspection Record

| Field | Type | Description |
|-------|------|-------------|
| `inspection_id` | String | Unique identifier |
| `target_id` | String | Reference to the submitted target |
| `target_hash` | String | Content hash of the target |
| `ruleset_version` | String | CG-IR hash used for evaluation |
| `frozen_env_hash` | String | Hash of the compilation environment |
| `engine_version` | String | Engine version used for evaluation |
| `inspector` | String | Actor who initiated the inspection |
| `started_at` | DateTime | When evaluation began (event time) |
| `completed_at` | DateTime | When evaluation finished (event time) |
| `status` | Enum | `completed`, `partial`, `failed` |
| `finding_count` | Integer | Total findings produced |
| `skipped_nodes` | Array | Nodes skipped due to dependency failures |
| `pipeline_trace` | Array | Ordered log of pipeline stages with timestamps |

### 8.2 Inspection Report

| Field | Type | Description |
|-------|------|-------------|
| `report_id` | String | Unique identifier |
| `inspection_id` | String | Reference to the inspection |
| `format` | Enum | `legal`, `technical`, `executive`, `json` |
| `generated_at` | DateTime | When the report was rendered |
| `findings` | Array | Findings included in this report |

---

## 9. Finding Model

### 9.1 Finding Event

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | String | Unique event identifier |
| `finding_id` | String | Finding identifier (stable across events) |
| `event_type` | Enum | `FindingCreated`, `DispositionChanged`, `FindingClosed` |
| `timestamp` | DateTime | When the event occurred |
| `actor` | String | Who triggered the event (system or human) |
| `payload` | Object | Event-specific data |

### 9.2 Finding Causal Chain

```
Finding → Control Node → Directive → Revision → Scope
```

---

## 10. Remediation Model

### 10.1 Remediation Record

| Field | Type | Description |
|-------|------|-------------|
| `remediation_id` | String | Unique identifier |
| `finding_id` | String | Reference to the finding |
| `status` | Enum | `in_progress`, `evidence_submitted`, `pending_verification`, `verified`, `closed` |
| `actor` | String | Who initiated remediation |
| `started_at` | DateTime | When remediation began |
| `evidence` | Array | Submitted evidence records |
| `verified_by` | String | Who verified the remediation |
| `verified_at` | DateTime | When verification occurred |
| `resolution` | Enum | `fixed`, `waived`, `rejected` |

---

## 11. Authorization Model

### 11.1 Role-Permission Matrix

| Role | Create Directive | Modify Directive | Retire Directive | View Findings | Acknowledge Finding | Submit Evidence | Approve Remediation | Waive Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Regulatory Official | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Compliance Representative | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |

### 11.2 Segregation of Duties

- Directive creator ≠ Finding waiver
- Evidence submitter ≠ Remediation approver

---

## 12. Conflict Resolution

### 12.1 Conflict Artifact

| Field | Type | Description |
|-------|------|-------------|
| `conflict_id` | String | Unique identifier |
| `conflict_type` | Enum | `directive_directive`, `control_control`, `finding_finding` |
| `entity_a` | String | First conflicting entity |
| `entity_b` | String | Second conflicting entity |
| `resolution_rule` | String | Which rule was applied |
| `resolved_by` | String | Actor or engine |
| `resolved_at` | DateTime | When resolved |
| `status` | Enum | `detected`, `resolved`, `escalated` |

---

## 13. System Invariants

| Invariant | Description |
| :--- | :--- |
| **Hermetic Compilation** | CG-IR reproducibility requires pinned frozen_env. Environment drift breaks reproducibility. |
| **CG-IR Immutability** | Once published, CG-IR is immutable. Changes produce new snapshots. |
| **Finding Event Immutability** | Finding event logs are append-only. No events modified or deleted. |
| **Inspection Immutability** | Completed inspections are never modified. |
| **Directive ID Immutability** | Directive identifiers never change across revisions. |
| **Ruleset Version Anchoring** | Every inspection references the exact CG-IR hash used. |
| **Causal Traceability** | Every finding traces: Finding → Control Node → Directive → Revision → Scope. |
| **Segregation of Duties** | Directive creator ≠ Finding waiver. |
| **DAG Acyclicity** | CG-IR dependency graph is acyclic. Enforced at compile time. |
| **Evaluator Purity** | Evaluators are pure functions: no IO, no randomness, no side effects. |
| **Mediated Feedback** | Analytics inform humans; humans modify directives; no direct finding → CG-IR path. |
| **Time Consistency** | All timestamps are event time. |

---

## 14. Validation

### 14.1 Directive Graph Validation

1. All required sections present
2. Schema validation passes
3. Machine IDs are unique
4. No cross-namespace contamination

### 14.2 CG-IR Validation

1. All nodes reference valid directives
2. Dependency graph is acyclic
3. All evaluators satisfy the pure function contract
4. Content hash matches ruleset version
5. No orphan nodes
6. Frozen environment metadata is complete

### 14.3 Evaluator Validation

1. No network calls, file I/O, or environment variable access in evaluator code
2. All inputs/outputs are JSON-serializable
3. Deterministic key ordering in serialized objects
4. `cached_ai` evaluators have frozen logic recorded in provenance

### 14.4 Inspection Validation

1. Target hash matches submitted target
2. CG-IR hash matches a published version
3. Frozen environment hash matches CG-IR provenance
4. Engine version supports CG-IR schema version
5. Pipeline trace is complete

---

## 15. References

- `docs/Regulation/policy_doctrine.yaml` — The policy contract
- `docs/Regulation/rule_schema.json` — The rule schema contract
- `docs/User_Story/User_Stories.md` — User stories defining the system behavior

---

## 16. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-07-04 | Initial specification |
| 2.0.0 | 2026-07-05 | Added Control Model, Inspection Pipeline, Finding Model |
| 3.0.0 | 2026-07-05 | Added CG-IR, Determinism Contract, Model Versioning |
| 4.0.0 | 2026-07-05 | Three runtime primitives, compile-time purity boundary, DAG execution |
| 5.0.0 | 2026-07-05 | Hermetic compilation, formal evaluator contract, context object, incremental compilation, mediated feedback, analytics substrate |
