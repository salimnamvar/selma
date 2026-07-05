# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform  
**Version:** 8.2.2
**Date:** 2026-07-05  
**Status:** Final  
**Normative Reference:** SPECIFICATION.md 8.2.2

> **Note:** Selma is domain-agnostic. It can serve financial compliance, environmental standards, organizational governance, software engineering, or any other regulatory domain.

---

## Executive Architectural Overview

SELMA is designed as a highly disciplined, domain-agnostic compliance and rule-regularity engine. Its core architecture relies on an elegant separation between human governance intent, strict machine-executable structural invariants, and a purely functional runtime execution model.

The architecture is built upon **three runtime primitives** (plus an execution artifact layer):

1. **Directive Graph:** The human-authored, structured source of truth.
2. **Compiled Control DAG (CG-IR):** The content-addressed, immutable executable intermediate representation.
3. **Finding Event Stream:** An append-only, chronologically consistent event log driven by Hybrid Logical Clocks (HLC).
4. **Execution Artifacts:** The reproducible inspection snapshots and pipeline traces.

### Layered Dominance & Cross-Layer Binding

The foundation of SELMA rests on a strict three-layer dominance hierarchy designed to eliminate runtime interpretation ambiguity:

| Layer | Document | Role | Runtime Authority |
| :--- | :--- | :--- | :--- |
| **Normative** | `SPECIFICATION.md` | Defines absolute system behaviors, algorithms, and invariants | **Highest.** The sole source of runtime semantics |
| **Structural** | `rule_schema.json` | Structural JSON Schema projection of spec invariants | **Data Carrier.** Read by the engine; contains no executable logic |
| **Governance** | `policy_doctrine.yaml` | Human-facing governance intent and formatting guide | **None.** Completely prohibited at inspection and evaluation runtime |

### The Policy Runtime Prohibition

A key architectural strength is the **Policy Runtime Prohibition**. The compilation and execution engines never interpret prose fields from the governance layer. Instead, the policy layer dictates human authoring constraints (enforced via compile-time schema validation), ensuring that runtime execution evaluates *only* highly structured schema fields.

### Version Synchronization Invariant

Cross-layer compatibility enforces strict semantic version consistency across all layers via a major-version math boundary:

```
dataset(S) accepts policy(P) ⟺ ⌊S⌋ == ⌊P⌋
```

Minor and patch versions are allowed to evolve independently within the same major family, but a major version mismatch results in an absolute compile-time rejection.

---

## Cross-Layer Binding

| Layer | Document | Role |
| :--- | :--- | :--- |
| **Normative** | SPECIFICATION.md 8.2.2 | Defines system behavior, invariants, contracts |
| **Structural** | rule_schema.json 8.2.2 | JSON Schema encoding of spec invariants |
| **Governance** | policy_doctrine.yaml 8.2.2 | Declarative governance intent (authoring only) |
| **Behavioral** | User_Stories.md 8.2.2 | This document — behavioral contract |

**Rule:** Spec is normative; schema and policy MUST conform. MAJOR versions MUST match across all documents; MINOR and PATCH MAY differ (compatibility matrix, not strict equality). Policy is never read at runtime — only schema fields compiled per spec.

**Schema Annotations:** All `x-*` keys in `rule_schema.json` are informative and non-normative. On conflict, SPECIFICATION.md wins.

**Cross-Field Constraints (semantic, not structural):**
- `evaluator_type` ↔ `evaluator_config` consistency requires compile-time dependent-schema validation beyond partial subschema checks (§2.9)
- `priority` ordering vs `depends_on` consistency is a semantic invariant, not a structural one
- `lineage.operation` constraints beyond required fields are semantic invariants

**Conflict Resolution:** Declared in three places (schema `conflict_resolution` field, cross-layer binding, policy intent section). All three MUST remain synchronized. SPECIFICATION.md §2.15 is normative; policy describes governance intent only.

---

## Core Architecture

```
┌─────────────────────────────┐
│   1. Directive Graph        │
│   (source-of-truth spec)    │
└──────────────┬──────────────┘
               │ compile (hermetic boundary, read lock)
               ▼
┌─────────────────────────────┐
│   2. Compiled Control DAG   │
│   (= CG-IR snapshot)        │
│   Content-addressed store   │
└──────────────┬──────────────┘
               │ evaluate (pure functions)
               ▼
┌─────────────────────────────┐
│   3. Finding Event Stream   │
│   - Append-only events      │
│   - HLC-ordered             │
│   - Finding FSM             │
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
└─────────────────────────────┘
```

### Architectural Strengths

| Strength | Description |
| :--- | :--- |
| **Content-Addressed Storage** | CG-IR nodes are deduplicated by hash; identical rule content across snapshots shares storage |
| **Incremental Compilation** | Unchanged subgraphs are reused via semantic_hash; only dirty nodes are recompiled |
| **Pure Evaluation** | Evaluators are side-effect-free functions; same inputs always produce same outputs |
| **HLC Event Ordering** | Hybrid Logical Clocks ensure total ordering without wall-clock dependency |
| **Hermetic Reproducibility** | Frozen environment pins all non-deterministic factors; identical inputs → identical CG-IR |

### Architectural Risks & Mitigations

| Risk | Description | Mitigation |
| :--- | :--- | :--- |
| **Lossy Metadata in Lexicographic Merges** | Merging `PAY-800` and `AUTH-001` permanently forces `AUTH-001` as lineage root; structural provenance of payment chain survives only in metadata array | Downstream metadata parsing for lineage tracing; consider `MERGE-NN` namespace (e.g. `MGR-18`) in future versions |
| **Time Realism in `finding_aggregates`** | Aggregates are pre-computed from past inspections; current-inspection findings not included in real-time | Multi-pass inspection loop or delayed escalation alerts until reinspection |
| **Discriminator Under-Validation** | `evaluator_type` ↔ `evaluator_config` consistency requires custom compile-time checks beyond standard JSON Schema subschema engines | Enforce dependent-schema validation at compile time; never rely solely on `if`/`then` |
| **Cascade Invisibility via Skipped Nodes** | Dependency failures silently bypass downstream checks; compliance review may miss unverified infrastructure | Pipeline trace entries record skipped nodes; dashboard views should surface `skipped_nodes` alongside findings |

---

## Dual Identity Model

SELMA avoids identity collision and preserves historical provenance during lifecycle shifts through a decoupled identity model:

| ID Type | Purpose | Mutability | Format |
| :--- | :--- | :--- | :--- |
| **Lineage ID** | Immutable root for audit trail | Never changes | `^[A-Z][A-Z0-9]+-[0-9]+$` |
| **Execution ID** | Active node identity for compilation | Changes on fork/merge/split | `^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$` |

| Layer | Lineage ID Field | Execution ID Field |
| :--- | :--- | :--- |
| Policy Doctrine | `Machine ID` → lineage_id | Not represented (assigned at schema compile time) |
| Rule Schema | `rule.lineage_id` | `rule.id` |
| CG-IR | `node.lineage_id` | `node.directive_id` |

**Invariant:** `rule.lineage_id` is immutable. `rule.id` changes only on fork/merge/split. Policy `Machine ID` maps to lineage_id only — never to execution ID.

**Machine ID semantics:** Stable external lineage identifier assigned at authoring time. At compile: `rule.lineage_id = Machine ID` (bijective at root-assignment level). On first creation: `rule.id = rule.lineage_id`. After fork/split, multiple active rules may share the same `lineage_id` with distinct execution_ids. Engine never reads policy tables at runtime.

### Deterministic Merge Semantics

When multiple rules converge, SELMA resolves identity mathematically to prevent semantic collision:

1. The new rule's `lineage_id` defaults strictly to the **lexicographic minimum** of the parent IDs.
2. The non-surviving parent root is permanently deprecated and preserved only within the `lineage.parent_lineage_ids` array metadata for downstream traceability.
3. The new execution `id` is derived deterministically by appending a short SHA-256 slice of the sorted parent IDs and the string token `"merge"`.

```
merge(parent_a, parent_b)
   ├── lineage_id := MIN(parent_a.lineage_id, parent_b.lineage_id)
   └── execution_id := lineage_id + "-M" + SHA-256(canonical_json({parents, operation: "merge", timestamp}))[0:16]
```

---

## Capability Enforcement

All mutating actions are gated before dispatch. Denial is a hard reject — no partial state mutation.

| Stage | Gate | Example Capabilities |
| :--- | :--- | :--- |
| Request ingress | API Gateway / Command Handler | All mutating capabilities |
| Directive mutations | Compilation Engine | `directive.create`, `directive.modify`, … |
| Inspection | Pipeline entry | `inspection.submit`, `inspection.reinspect` |
| Finding transitions | Finding FSM Engine | `finding.acknowledge`, `finding.approve_remediation`, … |

**Segregation of duties** is checked at the same gates. No capability delegation in v8.2.2.

---

## Key Concepts

| Concept | Definition |
| :--- | :--- |
| **Directive Graph** | Human-authored source-of-truth. Structured, versioned, diffable. |
| **CG-IR Snapshot** | Immutable, content-addressed DAG instance. Snapshot hash = SHA-256(sorted node_hashes + sorted edge_hashes + provenance). Determinism: identical inputs → identical hash. compiled_at excluded from hash (execution artifact metadata only). |
| **Semantic vs Presentation Hash** | `semantic_hash` covers evaluator/scope/priority (compilation cache). `presentation_hash` covers description/revision. `node_hash` composes both (§2.6). Editorial description changes do not invalidate semantic cache. |
| **Specificity Score** | Normative integer algorithm (§2.15): scope constraints via `scope_specificity_score` (×100) + evaluator field bindings. Two engines MUST agree on scores for identical node bodies. |
| **Merge Identity** | Merged `lineage_id` = lexicographic min of parent lineage_ids; new execution_id per §2.2.2 deterministic formula. |
| **Metadata Namespacing** | Informational only. Declared namespaces: audit, vendor, author, migration. No executable hints (§7.1). |
| **Anchor Reference** | `anchor_ref` MUST use `section:<id>` or JSON Pointer syntax (§7.2). |
| **Array Ordering** | Ordered: `sub_evaluators`, `pipeline_trace`. Unordered (sorted before hash): `depends_on`, `conflicts_with`, `parent_*_ids` (§2.16.1). |
| **Evaluator Complexity Limits** | Max depth 32, max nodes 256, max width 64, max regex 4096 chars, max metadata 16 KiB (§2.9). |
| **Finding Event Stream** | Append-only audit log with HLC ordering. Finding FSM enforced. |
| **Execution Artifacts** | Immutable inspection snapshots, pipeline traces, system state hashes. |
| **Hermetic Compilation** | Frozen environment ensures reproducibility. Read lock on Directive Graph. |
| **Control Node** | CG-IR node with pure evaluator, scope, severity, dependencies. |
| **Evaluator** | Pure function. Types: regex, field_check, threshold, composite. |
| **Evaluator Config** | Schema-enforced if/then binding — config MUST match evaluator_type. |
| **Evaluator Portability** | Cross-runtime determinism: RE2-compatible regex, IEEE 754 numerics, UTC timestamps, NFC strings. |
| **Finding FSM** | Strict state machine: Created → Open → Acknowledged → Evidence Submitted → Pending Verification → Verified → Closed (system) / Rejected → Open |
| **Hybrid Logical Clock** | Total order: physical_time → logical_counter → node_id → event_id; per-node tuple strictly non-decreasing; absorbs wall clock regression |
| **Capability Model** | Role → Capability → Action. Enforced at request ingress and stage gates. Deny = hard reject. |
| **Policy Runtime Prohibition** | policy_doctrine.yaml is authoring guidance only; never read during inspection/evaluation/FSM |
| **CG-IR Node Hashing** | Local content identity: node_hash from node_body only; graph context in edges + snapshot manifest |
| **CG-IR Edge Hashing** | edge_hash = SHA-256(canonical_json({source: directive_id, target: directive_id})). Directional. Independent of node content. |
| **Execution Fault Taxonomy** | Deterministic, Partial, Ambiguous, Dependency, Timeout, Resource, Schema, Corruption |
| **Conflict Resolution Mapping** | Precedence chain: explicit override (schema) → priority → specificity → recency → Conflict Artifact. Cycles detected and resolved. All inputs frozen in CG-IR snapshot — deterministic per snapshot. |
| **Deterministic Serialization** | Canonical JSON with sorted keys, ISO 8601 UTC, SHA-256, NaN/Infinity prohibited. `additionalProperties: true` objects normalized by sorting keys before hashing. Schema `$ref` resolved at validation time only, excluded from canonical form. |
| **Provenance Canonicalization** | All provenance fields canonicalized before hash inclusion; no non-deterministic ordering. |
| **Version Resolution** | `system_state_hash = f(directive_version, cg_ir_snapshot_hash, frozen_env, engine, target_hash)`. Captures inspection reproducibility only; event ordering excluded. |
| **Cross-Layer Binding** | Spec is normative; schema is structural projection; policy is governance intent. |
| **Concurrency Model** | Compilation = read lock; modification = write lock (exclusive). Queue serializes requests. |
| **CG-IR Storage** | Content-addressed: snapshots → nodes → edges. Deduplication by hash. |
| **Identity Refinement** | Machine ID ↔ lineage_id bijective at root-assignment level. Fork/split allows shared lineage_id with distinct execution_ids. Rule-level key: (lineage_id, id). |

### Evaluation Portability & Complexity Guardrails

The evaluation layer enforces pure, mathematical isolation. Evaluators operate with zero side effects, zero I/O, and zero runtime randomness.

#### Cross-Runtime Portability Rules

To prevent execution drift when evaluating rules across disparate CPU architectures or runtimes, the system mandates strict computational portability:

| Constraint | Rule | Rationale |
| :--- | :--- | :--- |
| **Regex Dialect** | Restricted entirely to **RE2-compatible syntax**. Advanced PCRE components (backreferences, lookaheads) are banned. | Mitigates catastrophic backtracking risks; ensures linear-time matching across implementations |
| **Strict Numerics** | Numeric evaluations must strictly use **IEEE 754 double-precision floats**. Special float states like `NaN` and `Infinity` are proactively blocked at the schema level. | Prevents silent divergence across CPU architectures and language runtimes |
| **Time & Strings** | Timestamps are strictly normalized to **ISO 8601 UTC** before comparison. String matches require **Unicode normalization form (NFC)**. | Eliminates DST/timezone ambiguity; prevents locale-sensitive ordering divergence |

#### System Complexity Limits

The compiler prevents execution engine stack exhaustion by tracking structural bounds:

| Complexity Metric | Absolute Limit | Compilation Failure Signal |
| :--- | :--- | :--- |
| **Max Composite Recursion Depth** | 32 levels | `SchemaError: evaluator depth exceeded` |
| **Max Total Evaluator Nodes / Rule** | 256 nodes | `SchemaError: evaluator count exceeded` |
| **Max Composite Width (`sub_evaluators`)** | 64 nodes | `SchemaError: evaluator width exceeded` |
| **Max Regex Pattern Length** | 4,096 chars | `SchemaError: pattern too long` |
| **Max Ancestry Lineage DAG Depth** | 64 steps | Compile-time lineage cycle/depth rejection |

### Conflict Resolution & Hashing Deep Dive

#### The Deterministic Precedence Chain

Runtime conflicts follow an unyielding, short-circuiting logical hierarchy executed via the normative algorithm in the specification:

```
Explicit Override (Schema conflict_resolution field)
        │
        ▼ [If no explicit override]
Priority Level (Internal integer evaluation: 1 to 5)
        │
        ▼ [If priority levels match]
Specificity Score (Normative score calculation)
        │
        ▼ [If specificity scores match]
Recency (Comparison of frozen created_at authoring timestamps)
        │
        ▼ [If all conditions tie]
Escalate to human review as a Conflict Artifact
```

The `specificity_score` is computed explicitly:

```
Score = (Scope Specificity × 100) + Bound Evaluator Fields
// Scope includes target_type, domain, jurisdiction, and filter count (§2.8.2)
```

Because all variables (including `created_at`) are embedded directly inside the `node_body` at compile time, conflict resolution outcomes are completely snapshot-bound and immutable, leaving zero vulnerability to evaluation-time environmental variance.

#### Split-Decomposition Hashing

SELMA partitions node evaluation states using a highly optimized dual-hash configuration to streamline caching and validation:

```
┌────────────────────────────────────────────────────────┐
│                      NODE_BODY                         │
├───────────────────────────┬────────────────────────────┤
│       SEMANTIC_BODY       │     PRESENTATION_BODY      │
│  - directive_id           │  - description             │
│  - lineage_id             │  - directive_revision      │
│  - evaluator              │  - control_version         │
│  - scope                  │                            │
│  - priority & status      │                            │
│  - depends_on & created_at│                            │
└─────────────┬─────────────┘             .──────────────┘
              │                           │
              ▼                           ▼
        SEMANTIC_HASH             PRESENTATION_HASH
              │                           │
              └─────────────┬─────────────┘
                            │
                            ▼
                        NODE_HASH (SHA-256)
```

By isolating the `semantic_hash` from editorial prose changes (like typos or description enhancements), the engine can execute incremental compilations and reuse downstream evaluator subgraphs without forcing unnecessary execution rebuilds.

Graph topology is decoupled entirely from node content. The global `cg_ir_snapshot_hash` is computed as a master SHA-256 function of the sorted array of independent `node_hashes`, directional `edge_hashes` ($source \to target$), and canonicalized provenance metadata.

---

## Actors & Capabilities

### Regulatory Official (Human or AI Agent)

| Attribute | Description |
| :--- | :--- |
| **Acts On Behalf Of** | The Regulatory Authority |
| **Role** | Rule Author & Governance Owner |
| **Capabilities** | `directive.*`, `finding.view`, `finding.dismiss`, `finding.waive`, `finding.approve_remediation`, `finding.reject_remediation`, `analytics.view`, `conflict.resolve` |
| **AI Agent Constraint** | Same capabilities as humans. All actions audit-logged with actor identity. |

### Compliance Representative (Human or System)

| Attribute | Description |
| :--- | :--- |
| **Acts On Behalf Of** | The Regulated Entity |
| **Role** | Compliance Seeker & Remediation Owner |
| **Capabilities** | `inspection.submit`, `inspection.reinspect`, `finding.view`, `finding.acknowledge`, `evidence.submit`, `analytics.view` |
| **Non-Capabilities** | Cannot create/modify/retire directives. Cannot waive findings. |

**Segregation of Duties:**
- Directive creator ≠ Finding waiver: holders of `finding.waive` MUST NOT waive findings raised by directives they authored (S-29)
- Evidence submitter ≠ Remediation approver: holders of `evidence.submit` MUST NOT approve remediation for the same finding (S-14)

---

## Epic 1: Directive Lifecycle

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Regulatory Official | I want to submit a new directive. | **Given** I express a need. **When** Selma processes it. **Then** Selma assigns lineage_id + execution_id, records in Directive Graph, compiles to CG-IR snapshot via hermetic boundary (read lock), performs structural review. **And** directive in "Draft" state with scope. | **P0** |
| **S-02** | Regulatory Official | I want to modify an existing directive. | **Given** I specify directive execution_id and change. **When** Selma processes it. **Then** Selma acquires write lock, creates new revision (same lineage_id), incrementally compiles to new CG-IR snapshot (reuses unchanged subgraph via content-addressed store), re-assesses consistency, records provenance. **And** lineage_id unchanged. **And** new Ruleset Version. | **P0** |
| **S-03** | Regulatory Official | I want to retire a directive. | **Given** I specify directive to retire. **When** Selma processes it. **Then** Selma transitions to "Retired", records reason, marks CG-IR nodes deprecated, generates new snapshot. | **P1** |
| **S-19** | Regulatory Official | I want to fork a directive into two distinct directives. | **Given** I specify a directive and describe the split. **When** Selma processes it. **Then** Selma creates two new execution_ids (inheriting lineage_id), records lineage (parent_lineage_ids, parent_execution_ids, operation=fork), compiles both to CG-IR, deprecates original nodes. **And** both new rules share the same lineage_id. **And** execution_ids are globally unique. | **P1** |
| **S-20** | Regulatory Official | I want to merge two directives into one. | **Given** I specify two directives and describe the merge. **When** Selma processes it. **Then** Selma assigns merged `lineage_id` = lexicographic min of parent lineage_ids, generates deterministic execution_id per §2.2.2, records sorted `lineage.parent_lineage_ids` and `lineage.parent_execution_ids`, compiles to CG-IR, deprecates both originals. **And** non-surviving parent lineage_id remains in audit history only. | **P1** |
| **S-26** | Regulatory Official | I want to split a directive into multiple independent directives. | **Given** I specify a directive and describe the restructuring. **When** Selma processes it. **Then** Selma creates multiple new execution_ids (inheriting parent lineage_id), records lineage (parent_lineage_ids, parent_execution_ids, operation=split), compiles to CG-IR, deprecates original. **And** each child has a unique execution_id. **And** all children share the parent lineage_id. | **P1** |

---

## Epic 2: Directive Governance

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-04** | Regulatory Official | I want to view all active requirements. | **Given** I request active requirements. **When** Selma processes it. **Then** Selma returns active directives and compiled nodes from current CG-IR snapshot. | **P0** |
| **S-05** | Regulatory Official | I want to inspect the regulatory set for conflicts. | **Given** I request consistency review. **When** Selma processes it. **Then** Selma assesses CG-IR, applies Conflict Resolution Mapping (explicit override first, then priority → specificity → recency), issues report with Conflict Artifacts. **And** conflict outcomes are deterministic for a given CG-IR snapshot (all inputs frozen in node_body). | **P1** |
| **S-06** | Regulatory Official | I want a comprehensive audit. | **Given** I request full audit. **When** Selma processes it. **Then** Selma generates audit report with gaps, redundancies, remedial measures. | **P2** |
| **S-07** | Regulatory Official | I want to view revision and lineage history of any directive. | **Given** I request history by lineage_id. **When** Selma processes it. **Then** Selma provides full revision log with timestamps, originator, changes, and lineage (fork/merge/split operations). Lineage_id constant across all revisions. | **P1** |
| **S-08** | Regulatory Official | I want to restore a directive to a previous revision. | **Given** I specify directive lineage_id and target revision. **When** Selma processes it. **Then** Selma creates new revision copying target, recompiles to new CG-IR snapshot, records provenance. | **P1** |
| **S-09** | Regulatory Official | I want to preview impact before finalizing. | **Given** I request change. **When** Selma generates proposal. **Then** Selma shows current vs proposed CG-IR snapshots, requires confirmation. | **P2** |
| **S-21** | Regulatory Official | I want to verify cross-runtime evaluator portability. | **Given** I request evaluator portability audit. **When** Selma processes it. **Then** Selma validates all regex patterns are RE2-compatible, confirms no prohibited regex features (backreferences, atomic groups), verifies numeric evaluators use IEEE 754 strict arithmetic, confirms timestamp evaluators use UTC-only, and reports any portability violations. | **P1** |
| **S-22** | Regulatory Official | I want to verify provenance canonicalization. | **Given** I request provenance audit. **When** Selma processes it. **Then** Selma validates all provenance fields are in canonical form before hash computation, confirms no non-deterministic ordering in provenance inclusion, and reports any canonicalization violations. | **P1** |
| **S-27** | Regulatory Official | I want to verify evaluator complexity limits. | **Given** I request complexity audit. **When** Selma processes it. **Then** Selma validates composite depth ≤ 32, total evaluator nodes ≤ 256, composite width ≤ 64, regex patterns ≤ 4096 chars, and lineage ancestry depth ≤ 64. **And** rejects rules exceeding limits at compile time. | **P1** |
| **S-28** | Regulatory Official | I want conflict resolution to be fully deterministic. | **Given** I request consistency review on a frozen CG-IR snapshot. **When** Selma applies `resolve_conflict`. **Then** Selma computes `specificity_score` per §2.15 normative algorithm, compares `priority_level` integers (not enum labels), and produces identical outcomes on repeated runs. | **P1** |

---

## Epic 3: Inspection

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-10** | Compliance Representative | I want to submit a target for inspection. | **Given** I provide a target (conforming to target schema). **When** Selma processes it. **Then** Selma validates target schema, populates context (conforming to context schema), validates evaluator_config matches evaluator_type, executes DAG pipeline, produces findings. **And** records inspection snapshot with: target_hash, ruleset_version, frozen_env_hash, engine_version, pipeline_trace (with fault taxonomy), skipped_nodes, system_state_hash. **And** failed nodes produce findings per fault taxonomy. **And** report is consistent point-in-time snapshot. | **P0** |
| **S-15** | Compliance Representative | I want to reinspect against latest directives. | **Given** I specify previously inspected target. **When** Selma processes it. **Then** Selma reads target (new hash), creates new inspection snapshot against current CG-IR, produces new Report. **And** original immutable. | **P1** |
| **S-16** | Compliance Representative | I want Selma to explain why a finding was raised. | **Given** I request explanation. **When** Selma processes it. **Then** Selma traverses causal chain (Finding → Control Node → Directive → Revision → Scope), highlights target portions, explains reasoning. | **P1** |
| **S-23** | Compliance Representative | I want to verify CG-IR snapshot determinism. | **Given** I request determinism verification. **When** Selma processes it. **Then** Selma compiles the same directive graph twice with identical frozen_env, confirms both produce identical cg_ir_snapshot_hash, confirms compiled_at is excluded from hash, and reports verification result. | **P1** |
| **S-24** | Compliance Representative | I want to verify edge hash correctness. | **Given** I request edge hash audit. **When** Selma processes it. **Then** Selma validates all edges follow edge_hash = SHA-256(canonical_json({source: directive_id, target: directive_id})), confirms edges are directional, confirms edge hashes are independent of node content, and reports any violations. | **P1** |

---

## Epic 4: Finding Management

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-11** | Compliance Representative | I want to view all findings. | **Given** I request findings. **When** Selma processes it. **Then** Selma returns findings with FSM state, computed disposition, severity, inspection reference, control node. | **P0** |
| **S-12** | Compliance Representative | I want to acknowledge a finding. | **Given** I specify finding. **When** I acknowledge (valid FSM transition: Open → Acknowledged). **Then** Selma creates Remediation record, status "In Progress", records timestamp and actor. **And** event log unchanged. | **P1** |
| **S-13** | Compliance Representative | I want to submit remediation evidence. | **Given** I specify finding and evidence. **When** I submit evidence (valid FSM transition: Acknowledged → Evidence Submitted). **Then** Selma attaches evidence, records submission. **And** system automatically transitions Evidence Submitted → Pending Verification. **And** event log unchanged. | **P1** |
| **S-14** | Regulatory Official | I want to review remediation evidence. | **Given** I request pending reviews. **When** Selma presents evidence. **Then** I approve (Pending Verification → Verified; system automatically transitions Verified → Closed) or reject (Pending Verification → Rejected). **And** reopening a rejected finding requires a separate explicit action (Rejected → Open with comments). **And** human actor triggers only approve/reject; closure is system-automatic per FSM. **And** event log append-only with event_hash and HLC total order (physical_time → logical_counter → node_id → event_id). | **P1** |
| **S-25** | Regulatory Official | I want to dismiss an invalid finding. | **Given** I determine a finding is incorrect. **When** I dismiss (valid FSM transition: Open → Dismissed). **Then** Selma transitions finding to Dismissed state, records disposition "invalid", records actor and timestamp. **And** event log append-only with event_hash and HLC total order. **And** dismissed findings have no outgoing FSM transitions. | **P1** |
| **S-29** | Regulatory Official | I want to waive a finding as accepted risk. | **Given** I determine a finding is legitimate but the risk is accepted. **When** I waive (valid FSM transition: Open → Waived). **Then** Selma transitions finding to Waived state, records disposition "waived", records actor and timestamp. **And** system automatically transitions Waived → Closed. **And** event log append-only with event_hash and HLC total order. **And** I cannot waive findings from directives I created (segregation of duties). | **P1** |

---

## Epic 5: Analytics & Mediated Feedback

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-17** | Regulatory Official | I want to view analytics on finding patterns. | **Given** I request analytics. **When** Selma processes it. **Then** Selma returns read-only aggregates: rates, severity distributions, recurrence, trends. **And** analytics never modify CG-IR. | **P1** |
| **S-18** | Regulatory Official | I want to propose a directive change based on analytics. | **Given** I review analytics and decide to change. **When** I submit via S-02. **Then** Selma records analytics provenance on directive revision. **And** follows standard path. | **P2** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Directive Lifecycle | 2 | 4 | 0 | **6** |
| Directive Governance | 1 | 7 | 1 | **9** |
| Inspection | 1 | 4 | 0 | **5** |
| Finding Management | 1 | 5 | 0 | **6** |
| Analytics & Mediated Feedback | 0 | 1 | 1 | **2** |
| **Total** | **5** | **21** | **2** | **28** |

---

## Finding FSM — Human vs System Transitions

| Transition | Trigger | Actor | Story |
| :--- | :--- | :--- | :--- |
| Created → Open | Automatic on finding creation | System | — |
| Open → Acknowledged | acknowledge | Compliance Representative | S-12 |
| Open → Dismissed | dismiss (invalid) | Regulatory Official | S-25 |
| Open → Waived | waive (accepted risk) | Regulatory Official | S-29 |
| Acknowledged → Evidence Submitted | submit evidence | Compliance Representative | S-13 |
| Evidence Submitted → Pending Verification | Automatic on evidence receipt | System | — |
| Pending Verification → Verified | approve | Regulatory Official | S-14 |
| Pending Verification → Rejected | reject | Regulatory Official | S-14 |
| Rejected → Open | reopen with comments | Regulatory Official | S-14 |
| Verified → Closed | Automatic after verification | System | — |
| Waived → Closed | Automatic after waive | System | — |

**Binding:** S-14 covers human approve/reject only. S-25 covers dismiss. S-29 covers waive. Verified → Closed and Waived → Closed are never human actions.

---

## Traceability

| Principle | Stories |
| :--- | :--- |
| Dual Identity (lineage + execution) | S-01, S-02, S-03, S-19, S-20, S-26 |
| Incremental Compilation (content-addressed) | S-02, S-03, S-19, S-20, S-26 |
| Hermetic Reproducibility | S-10, S-23 |
| Inspection Consistency (point-in-time) | S-10 |
| Evaluator Type Safety | S-10 |
| Evaluator Portability (cross-runtime determinism) | S-10, S-21 |
| Finding FSM | S-11, S-12, S-13, S-14, S-25, S-29 |
| HLC Event Ordering | S-14 |
| Capability-Based Permissions | S-14, S-25, S-29 |
| Segregation of Duties | S-14, S-29 |
| Conflict Resolution Mapping (explicit override first) | S-05, S-28 |
| Specificity Determinism (normative algorithm) | S-05, S-28 |
| Evaluator Complexity Limits | S-27 |
| Merge Identity Determinism | S-20 |
| Semantic/Presentation Hash Split | S-23 |
| Metadata Namespacing | S-01 |
| Anchor Reference Syntax | S-01 |
| Lineage DAG Invariants | S-19, S-20, S-26 |
| Conflict Resolution Temporal Binding | S-05 |
| Mediated Feedback | S-17, S-18 |
| DAG Execution with Fault Taxonomy | S-10 |
| Concurrency Safety (read/write locks) | S-01, S-02 |
| Cross-Layer Binding | All |
| CG-IR Edge Hashing (directional, node-independent) | S-24 |
| Provenance Canonicalization | S-22 |
| Snapshot Hash Determinism (compiled_at excluded) | S-23 |
| Identity Refinement (bijection at root level) | S-01, S-19, S-20, S-26 |

---

## System Invariants

Behavioral projection of SPECIFICATION.md §8. On conflict, the spec is normative.

| Invariant | Description |
| :--- | :--- |
| **Normative Source** | SPECIFICATION.md 8.2.2 is the single normative source; schema and policy MUST conform |
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
| **Finding Event Immutability** | Append-only; event_hash + HLC ordering ensure integrity |
| **Finding FSM** | Findings follow strict state transitions (see SPECIFICATION.md §3.1) |
| **Inspection Immutability** | Completed snapshots never modified |
| **Evaluator Purity** | Pure functions: no IO, no randomness |
| **Evaluator Type Safety** | evaluator_config MUST match evaluator_type (schema-enforced if/then) |
| **Evaluator Portability** | RE2-compatible regex only; IEEE 754 strict numerics; UTC-only timestamps; NFC-normalized strings |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver; Evidence submitter ≠ Approver |
| **Capability Enforcement** | All actions checked at ingress and stage gates; deny = 403, no partial mutation, audit logged |
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
| **Evaluator Complexity Bounds** | Depth ≤ 32, total nodes ≤ 256, width ≤ 64, regex ≤ 4096 chars, metadata ≤ 16 KiB (§2.9) |
| **Lineage DAG Acyclicity** | Ancestry graph acyclic; max depth 64 (§2.2.3) |
| **Specificity Determinism** | `specificity_score` algorithm in §2.15 is normative |
| **Semantic/Presentation Hash Split** | `semantic_hash` excludes description; `node_hash` composes both (§2.6) |
| **Array Ordering Classification** | Ordered vs unordered arrays per §2.16.1 |
| **Metadata Informational Only** | Namespaced metadata; no executable content (§7.1) |
| **Merge Identity Determinism** | Merged `lineage_id` = lexicographic min of parents (§2.2.2) |

---

## Internal View

| Engine | What It Does |
| :--- | :--- |
| **Directive Drafting Engine** | Natural language → Directive Graph entries |
| **Structural Compliance Reviewer** | Validates against schema, spec invariants, and contamination rules |
| **Control Compilation Engine** | Directive Graph → CG-IR snapshot. Hermetic. Incremental. Content-addressed. |
| **DAG Evaluation Engine** | Topological sort, parallel execution, strict context, fault taxonomy handling |
| **Conflict Resolution Engine** | Applies Conflict Resolution Mapping (explicit override first), creates Conflict Artifacts |
| **Finding FSM Engine** | Enforces state transitions, validates capability permissions |
| **Provenance Manager** | Tracks lineage IDs, execution IDs, revisions, frozen_env hashes, causal traceability |
| **Analytics Engine** | Read-only aggregates from Finding Event Stream. Feeds context. Never modifies CG-IR. |
