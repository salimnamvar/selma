# Universal Rule Governance Specification

**Version:** 6.0.0  
**Status:** Draft Standard  
**Date:** 2026-07-05

---

## 1. Introduction

### 1.1 Purpose

This specification defines a universal framework for creating, maintaining, and enforcing rules across any domain. The system is built on **three runtime primitives**:

1. **Directive Graph** — The human-authored source-of-truth specification
2. **Compiled Control DAG (CG-IR)** — The immutable executable intermediate representation
3. **Finding Event Stream** — The append-only audit log with read-only analytics

### 1.2 Scope

This standard applies to:
- Policy documents (prose rules, governance documents, standards)
- Machine-executable rules (automated enforcement, validation, compliance)
- Control derivation (translating directives into testable conditions)
- Inspection execution (evaluating targets against controls)
- Finding lifecycle (detection, disposition, remediation, closure)

---

## 2. Architecture

### 2.1 Three Runtime Primitives

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
└─────────────────────────────┘
```

### 2.2 Canonical Identity Resolution

A single directive has ONE identifier across all three layers:

| Layer | Field Name | Example |
| :--- | :--- | :--- |
| Policy Doctrine | `Machine ID` (in directive tables) | `TRAF-001` |
| Rule Schema | `rule.id` | `TRAF-001` |
| CG-IR | `node.directive_id` | `TRAF-001` |
| Finding | `finding.control_id` → `node.directive_id` | `TRAF-001` |

**Invariant:** `policy.Machine ID` = `rule.id` = `node.directive_id`. This is the single identity across all layers. No other identifier serves this function.

### 2.3 Canonical Transformation Pipeline

The transformation from policy to executable graph follows a formal pipeline:

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
    ▼
Rule Schema (machine-readable)
    │
    │ Step 3: Compile to CG-IR
    │ For each rule:
    │   - Generate control node
    │   - Attach pure evaluator (regex/field_check/threshold/composite)
    │   - Resolve dependencies (depends_on → node edges)
    │   - Apply priority hierarchy (declarative intent → executable logic)
    │   - Pin frozen environment hash
    ▼
CG-IR (immutable DAG)
    │
    │ Step 4: Evaluate targets
    │ Topological DAG execution with pure functions
    ▼
Finding Event Stream (append-only)
```

**Transformation Rules:**

| Input (Policy) | Output (CG-IR) | Transformation |
| :--- | :--- | :--- |
| `Machine ID` | `node.directive_id` | Direct copy (identity resolution) |
| `Type` (Obligation/Prohibition/Permission) | `node.evaluator` | Maps to evaluator_type and config |
| `Context / Conditions` | `node.scope` | Parsed into applicability context |
| Priority hierarchy (declarative) | `node.severity_default` + conflict logic | Compiled into executable resolution |
| `depends_on` | `node.edges` | Compiled into DAG edges |

### 2.4 The Directive Graph

| Aspect | Description |
| :--- | :--- |
| **Format** | Structured document (YAML/JSON with prose sections) |
| **Versioning** | Semantic versioning (MAJOR.MINOR.PATCH) |
| **Mutability** | Mutable (new revisions created on change) |
| **Content** | Directives, scope, priority, prose sections, metadata |

### 2.5 The Compiled Control DAG (CG-IR)

| Aspect | Description |
| :--- | :--- |
| **Format** | Directed Acyclic Graph of control nodes |
| **Versioning** | Content-addressed (SHA-256 hash) |
| **Mutability** | Immutable once published |
| **Content** | Control nodes, edges (dependencies), evaluation logic |

**Incremental Compilation:**

| Change Type | Strategy |
| :--- | :--- |
| Add new directive | Append new nodes; reuse unchanged subgraph |
| Modify directive | Recompile only affected nodes and dependents |
| Remove directive | Mark nodes deprecated; reuse rest |
| Change evaluator | Recompile only affected node |

**Node-Level Version Inheritance:** Unchanged nodes inherit their previous version. CG-IR snapshots share common subgraphs.

### 2.6 The Hermetic Compilation Boundary

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
   │  Output: CG-IR + provenance metadata│
   └─────────────────────────────────────┘
```

**Hermeticity Rules:**
1. Compilation is reproducible only when the entire environment is frozen
2. The frozen environment is recorded in CG-IR provenance
3. To reproduce: pin engine version + model version + prompt hash + toolchain version
4. AI outputs are cached and serialized into CG-IR before publication
5. Once published, CG-IR is immutable

### 2.7 CG-IR Node Schema

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | String | Unique node identifier (e.g., `CTRL-TRAF-001-01`) |
| `directive_id` | String | Canonical directive ID (Machine ID = rule.id) |
| `directive_revision` | String | Revision of source directive |
| `control_version` | String | Version of this node's evaluation logic |
| `description` | String | Human-readable description |
| `evaluator` | Object | Pure evaluator specification (see 2.8) |
| `scope` | Object | Applicability context |
| `severity_default` | Enum | Default severity on failure |
| `depends_on` | Array | Node IDs that must be evaluated first |
| `status` | Enum | `active`, `deprecated` |

### 2.8 Formal Evaluator Contract

Evaluators are **pure functions**:

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
| **Prohibited operations** | HTTP calls, database queries, file reads, environment variables |
| **Context** | Read-only. Contains target metadata, domain constants, finding aggregates |
| **Serialization** | JSON-serializable with deterministic key ordering |

**Evaluator Types (pure only):**

| Type | Description |
| :--- | :--- |
| `regex` | Pattern matching against target content |
| `field_check` | Validates specific fields in structured targets |
| `threshold` | Numeric comparison against configured limits |
| `composite` | Boolean combination of sub-evaluators |

**Removed:** `api_call`, `human_judgment`, `cached_ai` — these violate the purity contract. AI-assisted compilation produces frozen evaluator logic, not runtime AI calls.

### 2.9 Context Object

Read-only input to evaluators:

| Field | Type | Description |
|-------|------|-------------|
| `target_metadata` | Object | Hash, type, submission time |
| `domain_constants` | Object | Jurisdiction, domain, scope filters |
| `finding_aggregates` | Object | Pre-computed from Finding Event Stream |

**Finding Aggregates:**

| Field | Type | Description |
|-------|------|-------------|
| `total_open_findings` | Integer | Open findings for this target |
| `findings_by_severity` | Map | `{ severity: count }` |
| `findings_by_control` | Map | `{ control_id: count }` |
| `last_inspection_date` | DateTime | Last inspection time |
| `recurrence_count` | Integer | Times this control failed for this target |

**No Write-Back:** Evaluators cannot modify context.

### 2.10 DAG Execution Semantics

| Aspect | Rule |
| :--- | :--- |
| **Evaluation Order** | Topological sort respecting `depends_on` |
| **Cycle Detection** | Enforced at compile time |
| **Parallel Execution** | Independent nodes execute in parallel |
| **State Propagation** | Read-only context; no shared mutable state |
| **Timeout** | Per-node configurable (default: 30s) |
| **Retry** | No retries; failed nodes → `NeedsReview` |

### 2.11 Inspection Consistency Model

An inspection produces a **point-in-time snapshot** of the DAG evaluation:

| Aspect | Rule |
| :--- | :--- |
| **Snapshot** | The inspection record captures the complete evaluation state at completion |
| **Partial execution** | Nodes may be skipped (dependency failures); skipped nodes are recorded |
| **Report** | The report reflects the snapshot, including partial results |
| **Reproducibility** | Same CG-IR + same target + same frozen_env = same snapshot |
| **Immutability** | Once completed, the inspection snapshot is never modified |

**Consistency Guarantee:** The report is a consistent point-in-time view. Partial results are valid and explicitly marked. Consumers can detect partial execution via `skipped_nodes`.

### 2.12 Finding Event Stream

**Events:**

| Event Type | Description |
| :--- | :--- |
| `FindingCreated` | Initial creation |
| `DispositionChanged` | Disposition update |
| `FindingClosed` | Lifecycle closure |

**Read-Only Analytics:**

| Analytics | Description |
| :--- | :--- |
| `finding_aggregates` | Pre-computed aggregates for context object |
| `trend_analysis` | Finding rates over time (read-only) |
| `compliance_dashboard` | Real-time posture view |

**Mediated Feedback:**

```
Finding Event Stream → Read-only analytics → Human review → Directive Graph change → Recompile
```

**Rules:**
1. Analytics are read-only; never directly modify CG-IR
2. All changes go through standard Directive Graph → CG-IR path
3. Human decision recorded as provenance on directive revision
4. Feedback loops are auditable

### 2.13 Version Resolution Function

The complete system state for any finding is determined by:

```
system_state_hash = hash(
  directive_graph_version,
  cg_ir_hash,
  frozen_env_hash,
  engine_version,
  target_hash
)
```

To reproduce any historical inspection, pin all five dimensions.

---

## 3. Layered Namespace Model

```
Directive Graph
├── prose/          (human-readable sections)
├── directives/     (structured rule definitions)
├── metadata/       (version, jurisdiction, domain)
└── traceability/   (Machine IDs, anchor refs)

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

---

## 4. Version Compatibility Matrix

| Axis | Format | Mutability |
| :--- | :--- | :--- |
| Directive Graph Version | Semantic (MAJOR.MINOR.PATCH) | Mutable |
| CG-IR Schema Version | Semantic | Immutable per snapshot |
| Engine Version | Semantic | Immutable per release |
| Frozen Environment | Content hash | Immutable per compilation |

---

## 5. Policy Doctrine Contract

### 5.1 Structure

| Section | Required | Content Type | Purpose |
|---------|----------|--------------|---------|
| Preamble | Yes | Prose | Existential need |
| Governance & Amendment | Yes | Prose | Change process |
| Definitions | Yes | Table | Term definitions |
| Foundational Principles | Yes | Prose/Table | Axioms |
| Directives | Yes | Mixed | Rules and standards |
| Sanctions & Remedies | Yes | Table | Consequences |
| References & Annexes | No | Prose/Table | External sources |

### 5.2 Contamination Guard

**Prohibited fields:** parameters, conditions, evaluator_hint, evaluator_type, weight, depends_on, conflicts_with, status, created_at, expires_at, remediation, target

**Allowed:** Machine ID columns (cross-reference labels only)

**Note:** Priority hierarchy and conflict resolution are DECLARATIVE DESCRIPTIONS of governance intent, not executable algorithms. The compilation engine translates intent into CG-IR logic.

---

## 6. Rule Schema Contract

See `rule_schema.json` for the formal JSON Schema.

Key fields: `id` (canonical identity), `type`, `message`, `evaluator_type` (pure only), `evaluator_config`, `depends_on`, `priority`.

---

## 7. System Invariants

| Invariant | Description |
| :--- | :--- |
| **Canonical Identity** | One ID across all layers: Machine ID = rule.id = directive_id |
| **Hermetic Compilation** | CG-IR reproducibility requires pinned frozen_env |
| **CG-IR Immutability** | Once published, immutable |
| **Finding Event Immutability** | Append-only |
| **Inspection Immutability** | Completed inspections never modified |
| **Evaluator Purity** | Pure functions: no IO, no randomness |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver |
| **Mediated Feedback** | Analytics inform humans; no direct finding → CG-IR |
| **Declarative Governance** | Policy describes intent; engine implements logic |

---

## 8. Validation

### 8.1 Identity Validation

1. Every Machine ID in policy exists as rule.id in schema
2. Every rule.id has a Machine ID in policy
3. Every CG-IR node.directive_id matches a rule.id
4. No orphan IDs in any layer

### 8.2 Evaluator Validation

1. All evaluators are pure functions (no IO detected)
2. evaluator_type is one of: regex, field_check, threshold, composite
3. No `api_call`, `human_judgment`, or `cached_ai` types
4. All inputs/outputs JSON-serializable

### 8.3 CG-IR Validation

1. All nodes reference valid directive_ids
2. DAG is acyclic
3. Content hash matches ruleset version
4. Frozen environment metadata complete

### 8.4 Inspection Validation

1. Target hash matches submitted target
2. CG-IR hash matches published version
3. Frozen environment hash matches CG-IR provenance
4. Pipeline trace complete

---

## 9. References

- `docs/Regulation/policy_doctrine.yaml` — Policy contract (declarative governance)
- `docs/Regulation/rule_schema.json` — Rule schema (machine structure)
- `docs/User_Story/User_Stories.md` — User stories (behavioral contract)

---

## 10. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-07-04 | Initial specification |
| 2.0.0 | 2026-07-05 | Added Control Model, Inspection Pipeline |
| 3.0.0 | 2026-07-05 | Added CG-IR, Determinism Contract |
| 4.0.0 | 2026-07-05 | Three runtime primitives, hermetic boundary |
| 5.0.0 | 2026-07-05 | Incremental compilation, evaluator contract, context object |
| 6.0.0 | 2026-07-05 | Canonical identity resolution, transformation pipeline, inspection consistency model, version resolution function, declarative governance separation, pure evaluator types only |
