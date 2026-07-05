# Universal Rule Governance Specification

**Version:** 4.0.0  
**Status:** Draft Standard  
**Date:** 2026-07-05

---

## 1. Introduction

### 1.1 Purpose

This specification defines a universal framework for creating, maintaining, and enforcing rules across any domain. The system is built on **three runtime primitives**:

1. **Directive Graph** — The human-authored source-of-truth specification
2. **Compiled Control DAG (CG-IR)** — The immutable executable intermediate representation
3. **Finding Event Stream** — The append-only audit log

Everything else (policy prose, schema definitions, tooling, reports) is a documentation or rendering layer on top of these three primitives.

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

The entire system reduces to three primitives:

```
┌─────────────────────────────┐
│   1. Directive Graph        │
│   (source-of-truth spec)    │
│                             │
│   - Human-authored rules    │
│   - Structured metadata     │
│   - Versioned as artifact   │
└──────────────┬──────────────┘
               │ compile (deterministic boundary)
               ▼
┌─────────────────────────────┐
│   2. Compiled Control DAG   │
│   (= CG-IR)                 │
│   (immutable executable)    │
│                             │
│   - Content-addressed       │
│   - DAG of control nodes    │
│   - Frozen at publish time  │
└──────────────┬──────────────┘
               │ evaluate (deterministic)
               ▼
┌─────────────────────────────┐
│   3. Finding Event Stream   │
│   (append-only audit log)   │
│                             │
│   - Immutable events        │
│   - Computed state          │
│   - No feedback to CG-IR    │
└─────────────────────────────┘
```

### 2.2 The Directive Graph

The Directive Graph is the human-authored source of truth. Unlike pure prose, it is a **structured, versioned artifact** that can be validated, diffed, and migrated.

| Aspect | Description |
| :--- | :--- |
| **Format** | Structured document (YAML/JSON with prose sections) |
| **Versioning** | Semantic versioning (MAJOR.MINOR.PATCH) |
| **Mutability** | Mutable (new revisions created on change) |
| **Content** | Directives, scope, priority, prose sections, metadata |
| **Validation** | Schema-validated at compile time |

**Policy Versioning:** The Directive Graph is versioned as a structured artifact, not just prose. This enables:
- Automated diff between versions
- Migration scripts for schema evolution
- Backward compatibility checking

### 2.3 The Compiled Control DAG (CG-IR)

The CG-IR is the immutable, executable intermediate representation. All directives compile into it. The Ruleset Version is its content-addressed hash.

| Aspect | Description |
| :--- | :--- |
| **Format** | Directed Acyclic Graph of control nodes |
| **Versioning** | Content-addressed (SHA-256 hash) |
| **Mutability** | Immutable once published |
| **Content** | Control nodes, edges (dependencies), evaluation logic |
| **Validation** | DAG structure validated at compile time |

**CG-IR Schema Evolution:**

| Change Type | Strategy |
| :--- | :--- |
| Add new control node | Backward-compatible (new CG-IR, old still valid) |
| Remove control node | Breaking change (new MAJOR version required) |
| Change evaluation logic | New control version (new CG-IR hash) |
| Change dependency edges | New CG-IR (hash changes) |
| Schema format change | Migration required (versioned schema with compatibility matrix) |

**Backward Compatibility Rules:**
- New CG-IR versions must be evaluable by engine versions that support the schema version
- Legacy CG-IR versions remain reproducible by pinning engine version
- Schema migration is explicit and versioned

### 2.4 The Compile-Time Purity Boundary

The boundary between Directive Graph and CG-IR is the **purity boundary**. Everything downstream of CG-IR must be deterministic.

```
Directive Graph (may contain AI-assisted content)
        │
        ▼ compile()
   ┌─────────────────────────────────────┐
   │     COMPILE-TIME PURITY BOUNDARY    │
   │                                     │
   │  - All AI outputs cached here       │
   │  - All non-determinism resolved     │
   │  - CG-IR is frozen                  │
   └─────────────────────────────────────┘
        │
        ▼
   CG-IR (fully deterministic)
        │
        ▼ evaluate()
   Findings (fully deterministic)
```

**Rules:**
1. AI-assisted compilation is allowed ONLY at the Directive Graph → CG-IR boundary
2. AI outputs are cached and serialized into CG-IR before publication
3. Once CG-IR is published, it is immutable and fully deterministic
4. No AI, randomness, or external calls are permitted during CG-IR → Findings evaluation
5. Findings must NEVER influence future CG-IR compilation (no feedback loops)

### 2.5 CG-IR Node Schema

Each node in the CG-IR DAG:

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | String | Unique identifier (e.g., `CTRL-REG-024-01`) |
| `directive_id` | String | Source directive identifier |
| `directive_revision` | String | Revision of source directive |
| `control_version` | String | Version of this node's evaluation logic |
| `description` | String | Human-readable description |
| `evaluation_type` | Enum | `deterministic`, `cached_ai` |
| `evaluator` | Object | Evaluation function specification |
| `scope` | Object | Applicability context |
| `severity_default` | Enum | Default severity on failure |
| `depends_on` | Array | Node IDs that must be evaluated first |
| `status` | Enum | `active`, `deprecated` |

**Evaluator Function Signature:**

```
evaluate(node, target, context) → {
  outcome: Pass | Fail | Partial | NeedsReview,
  confidence: Float (0.0–1.0),
  evidence: String,
  reasoning: String
}
```

### 2.6 DAG Execution Semantics

The CG-IR is executed as a DAG with these semantics:

| Aspect | Rule |
| :--- | :--- |
| **Evaluation Order** | Topological sort respecting `depends_on` edges |
| **Cycle Detection** | Enforced at compile time. Cycles cause compilation failure. |
| **Parallel Execution** | Nodes with no interdependency may execute in parallel |
| **State Propagation** | Each node receives only its declared inputs; no shared mutable state |
| **Failure Handling** | See Section 2.7 |
| **Timeout** | Each node has a configurable timeout (default: 30s) |
| **Retry** | No automatic retries; failed nodes produce `NeedsReview` findings |

### 2.7 Pipeline Failure Semantics

| Failure Mode | Behavior |
| :--- | :--- |
| **Single node timeout** | Node produces `NeedsReview` finding; other nodes continue |
| **Single node error** | Node produces `NeedsReview` finding; other nodes continue |
| **Dependency failure** | Dependent nodes are skipped; skip event logged |
| **Cycle detected** | Compilation fails; no CG-IR published |
| **Schema mismatch** | Compilation fails; migration required |
| **Engine version mismatch** | Evaluation fails; pinned engine version required for reproducibility |

**Pipeline is NOT atomic.** Partial results are valid. Each node's outcome is independent unless blocked by dependency failure. The inspection record captures the complete execution trace including skipped nodes.

### 2.8 Determinism Contract

| Component | Determinism Level | Reproducibility Guarantee |
| :--- | :--- | :--- |
| Directive compilation | Deterministic (AI outputs cached) | Same Directive Graph version + same engine = same CG-IR |
| CG-IR evaluation | Fully deterministic | Same CG-IR + same target = same findings |
| Finding generation | Fully deterministic | Same evaluation results = same findings |

### 2.9 Finding Event Stream

Findings are append-only event logs. Current state is computed by replaying events.

**Events:**

| Event Type | Fields | Description |
| :--- | :--- | :--- |
| `FindingCreated` | finding_id, inspection_id, control_id, severity, description, evidence, reasoning | Initial creation |
| `DispositionChanged` | finding_id, old_disposition, new_disposition, actor, reason, timestamp | Disposition update |
| `FindingClosed` | finding_id, actor, reason, timestamp | Lifecycle closure |

**Computed State:**

| Field | Source |
|-------|--------|
| `lifecycle_status` | Computed from `FindingCreated` + `FindingClosed` events |
| `disposition` | Computed from `DispositionChanged` events |
| `severity` | Set at creation, immutable |

**Invariant:** Finding event streams are append-only. No events are modified or deleted.

**No Feedback Loops:** Findings must NEVER influence future CG-IR compilation. The Finding Event Stream is strictly an output, never an input to the Directive Graph or CG-IR.

---

## 3. Layered Namespace Model

Instead of forbidden fields, each layer has a **typed namespace** with schema validation.

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
└── provenance/     (compilation metadata)

Finding Event Stream
├── events/         (immutable event log)
└── computed/       (derived state projections)
```

### 3.2 Cross-Layer References

| From | To | Mechanism |
| :--- | :--- | :--- |
| Directive Graph → CG-IR | `compilation` | Directive ID + revision → CG-IR hash |
| CG-IR → Directive Graph | `provenance` | CG-IR node → directive_id + revision |
| CG-IR → Findings | `evaluation` | CG-IR hash + target_hash → finding events |
| Findings → CG-IR | `causal_chain` | Finding → control_id → CG-IR node |

---

## 4. Version Compatibility Matrix

### 4.1 Version Axes

| Axis | Format | Mutability |
| :--- | :--- | :--- |
| Directive Graph Version | Semantic (MAJOR.MINOR.PATCH) | Mutable (new revisions) |
| CG-IR Schema Version | Semantic (MAJOR.MINOR.PATCH) | Immutable per snapshot |
| Engine Version | Semantic (MAJOR.MINOR.PATCH) | Immutable per release |
| Model Version | String (e.g., `llm-gpt4o-2024-05-13`) | Immutable per registration |

### 4.2 Compatibility Rules

| Scenario | Requirement |
| :--- | :--- |
| Evaluate CG-IR with engine | Engine version must support CG-IR schema version |
| Compile Directive Graph | Engine version must support Directive Graph schema version |
| Reproduce historical inspection | Pin: engine version + CG-IR hash + target hash + model version |
| Migrate legacy CG-IR | Use migration tool matching source → target schema versions |

### 4.3 Model Version Coupling

| Model Type | Coupled To | Drift Handling |
| :--- | :--- | :--- |
| Compilation model (AI-assisted) | CG-IR nodes marked `cached_ai` | Model drift → new CG-IR with new nodes |
| Evaluation model (probabilistic) | Deprecated in v4.0 | All evaluation is deterministic post-compilation |

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

A policy document MUST contain the following sections:

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
| `evaluator_hint` | String | How to evaluate (regex, human_judgment, api_call) |
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
| `target_hash` | String | Content hash of the target at time of inspection |
| `ruleset_version` | String | CG-IR hash used for evaluation |
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
| **Compile-Time Purity** | All non-determinism is resolved before CG-IR publication. CG-IR is fully deterministic. |
| **CG-IR Immutability** | Once published, CG-IR is immutable. Changes produce new snapshots. |
| **Finding Event Immutability** | Finding event logs are append-only. No events are modified or deleted. |
| **Inspection Immutability** | Once completed, an inspection record is never modified. |
| **Directive ID Immutability** | A directive's identifier never changes across revisions. |
| **Ruleset Version Anchoring** | Every inspection references the exact CG-IR hash used. |
| **Causal Traceability** | Every finding traces: Finding → Control Node → Directive → Revision → Scope. |
| **Segregation of Duties** | Directive creator ≠ Finding waiver. |
| **No Feedback Loops** | Findings never influence future CG-IR compilation. |
| **DAG Acyclicity** | CG-IR dependency graph has no cycles. Enforced at compile time. |
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
3. All evaluators have valid function signatures
4. Content hash matches ruleset version
5. No orphan nodes

### 14.3 Inspection Validation

1. Target hash matches submitted target
2. CG-IR hash matches a published version
3. Engine version supports CG-IR schema version
4. Pipeline trace is complete

---

## 15. References

- `docs/Contract/policy_doctrine.yaml` — The policy contract
- `docs/Contract/rule_schema.json` — The rule schema contract
- `docs/User_Story/User_Stories.md` — User stories defining the system behavior

---

## 16. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-07-04 | Initial specification |
| 2.0.0 | 2026-07-05 | Added Control Model, Inspection Pipeline, Finding Model |
| 3.0.0 | 2026-07-05 | Added CG-IR, Determinism Contract, Model Versioning |
| 4.0.0 | 2026-07-05 | Three runtime primitives, compile-time purity boundary, DAG execution semantics, pipeline failure semantics, namespace model, version compatibility matrix, no feedback loops |
