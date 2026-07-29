# ARCHIVED — Replaced by docs/spec/contracts/

This file is preserved for reference during migration.
The normative source is now the contract tree under docs/spec/contracts/.

Migration status: PENDING
Archived on: 2026-07-29

# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform  
**Version:** 8.2.4
**Date:** 2026-07-05  
**Status:** Final  
**Normative Reference:** SPECIFICATION.md 8.2.4

> **Note:** Selma is domain-agnostic. It can serve financial compliance, environmental standards, organizational governance, software engineering, or any other regulatory domain.

---

## Executive Architectural Overview

SELMA is a domain-agnostic rule regularity platform. This document defines the behavioral contract for Selma 8.2.4 as 36 user stories across 7 epics.

### Architecture Reference
See SPECIFICATION.md §2 for the normative architecture.

### Invariant Reference
All system invariants are normatively defined in SPECIFICATION.md §8.
This document references invariants by name; see the Traceability table
for spec section mappings.

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

### Capability Matrix

| Capability | Regulatory Official | Compliance Representative | System | Segregation of Duties Constraint |
| :--- | :---: | :---: | :---: | :--- |
| `directive.create` | ✅ | ❌ | ❌ | — |
| `directive.modify` | ✅ | ❌ | ❌ | — |
| `directive.retire` | ✅ | ❌ | ❌ | — |
| `directive.fork` | ✅ | ❌ | ❌ | — |
| `directive.merge` | ✅ | ❌ | ❌ | — |
| `directive.restore` | ✅ | ❌ | ❌ | — |
| `inspection.submit` | ❌ | ✅ | ✅ | — |
| `inspection.reinspect` | ❌ | ✅ | ❌ | — |
| `finding.view` | ✅ | ✅ | ✅ | — |
| `finding.acknowledge` | ❌ | ✅ | ❌ | — |
| `finding.dismiss` | ✅ | ❌ | ❌ | — |
| `finding.waive` | ✅ | ❌ | ❌ | Actor MUST NOT be in `creator_provenance` for the finding's directive (S-29) |
| `finding.approve_remediation` | ✅ | ❌ | ❌ | Actor MUST NOT have submitted evidence for this finding (S-14a, S-33) |
| `finding.reject_remediation` | ✅ | ❌ | ❌ | — |
| `evidence.submit` | ❌ | ✅ | ❌ | — |
| `finding.supersede` | ✅ | ❌ | ❌ | — |
| `analytics.view` | ✅ | ✅ | ✅ | — |
| `conflict.resolve` | ✅ | ❌ | ❌ | — |

`creator_provenance` is inherited through fork/merge/split per SPECIFICATION.md §3.2. On merge, the union of all parent `authored_by` values applies.

### Segregation of Duties Stories

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-32** | System | I want to enforce segregation of duties automatically. | **Given** a `finding.waive` request. **When** the actor is in `creator_provenance` for the finding's directive. **Then** Selma DENIES with `403 CapabilityDenied` and records audit entry with reason "segregation of duties violation". **And** no state mutation occurs. **And** FSM state remains unchanged. | **P0** |
| **S-33** | System | I want to prevent evidence submitters from approving their own remediation. | **Given** a `finding.approve_remediation` request. **When** the actor is the same as the evidence submitter for this finding. **Then** Selma DENIES with `403 CapabilityDenied` and records audit entry with reason "segregation of duties violation". **And** no state mutation occurs. **And** FSM state remains unchanged. | **P0** |

### Capability Validation Stories

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-34** | Regulatory Official | I want to verify capability enforcement at all gates. | **Given** I attempt any action. **When** Selma processes the request. **Then** Selma checks capability at the appropriate gate (request ingress, compilation, pipeline entry, FSM transition, conflict resolution). **And** if I lack the required capability, Selma DENIES with `403 CapabilityDenied`. **And** no partial state mutation occurs. **And** all denials produce audit records. | **P1** |

---

## Key Concepts

| Concept | Reference |
| :--- | :--- |
| **Directive Graph** | Human-authored source-of-truth. Structured, versioned, diffable. |
| **CG-IR Snapshot** | SPECIFICATION.md §2.6 |
| **Semantic vs Presentation Hash** | `semantic_hash` covers evaluator/scope/priority (compilation cache). `presentation_hash` covers description/revision. `node_hash` composes both. Editorial description changes do not invalidate semantic cache. See SPECIFICATION.md §2.6. |
| **Specificity Score** | SPECIFICATION.md §2.15 |
| **Merge Identity** | SPECIFICATION.md §2.2.2 |
| **Metadata Namespacing** | Informational only. Declared namespaces: audit, vendor, author, migration. No executable hints. See SPECIFICATION.md §7.1. |
| **Anchor Reference** | `anchor_ref` MUST use `section:<id>` or JSON Pointer syntax. See SPECIFICATION.md §7.2. |
| **Array Ordering** | SPECIFICATION.md §2.16.1 |
| **Evaluator Complexity Limits** | SPECIFICATION.md §2.9 |
| **Finding Event Stream** | Append-only audit log with HLC ordering. Finding FSM enforced. |
| **Execution Artifacts** | Immutable inspection snapshots, pipeline traces, system state hashes. |
| **Hermetic Compilation** | Frozen environment ensures reproducibility. Read lock on Directive Graph. |
| **Control Node** | CG-IR node with pure evaluator, scope, severity, dependencies. |
| **Evaluator** | Pure function. Types: regex, field_check, threshold, composite. |
| **Evaluator Config** | Schema-enforced if/then binding — config MUST match evaluator_type. |
| **Evaluator Portability** | SPECIFICATION.md §2.9 |
| **Finding FSM** | SPECIFICATION.md §3.1 |
| **Hybrid Logical Clock** | SPECIFICATION.md §3.3 |
| **Capability Model** | Role → Capability → Action. Enforced at request ingress and stage gates. Deny = hard reject. |
| **Policy Runtime Prohibition** | policy_doctrine.yaml is authoring guidance only; never read during inspection/evaluation/FSM |
| **CG-IR Node Hashing** | SPECIFICATION.md §2.6 |
| **CG-IR Edge Hashing** | SPECIFICATION.md §2.6 |
| **Execution Fault Taxonomy** | Deterministic, Partial, Ambiguous, Dependency, Timeout, Resource, Schema, Corruption |
| **Conflict Resolution Mapping** | SPECIFICATION.md §2.15 |
| **Deterministic Serialization** | SPECIFICATION.md §2.16 |
| **Provenance Canonicalization** | SPECIFICATION.md §2.6 |
| **Version Resolution** | `system_state_hash` captures inspection reproducibility only; event ordering excluded. |
| **Cross-Layer Binding** | Spec is normative; schema is structural projection; policy is governance intent. |
| **Concurrency Model** | Compilation = read lock; modification = write lock (exclusive). Queue serializes requests. |
| **CG-IR Storage** | Content-addressed: snapshots → nodes → edges. Deduplication by hash. |
| **Identity Refinement** | Machine ID ↔ lineage_id bijective at root-assignment level. Fork/split allows shared lineage_id with distinct execution_ids. Rule-level key: (lineage_id, id). |

### Conflict Resolution & Hashing Deep Dive

Worked examples using normative algorithms from SPECIFICATION.md §2.8.2, §2.15, §2.6, and §2.2.2. All inputs are frozen in the CG-IR snapshot at compile time.

**Specificity Score — Rule Pair 1**

Rule A (`priority: regulatory`, level 3):
- `scope`: `{target_type: "structured", domain: "finance", jurisdiction: "EU", filters: [{field: "amount", operator: "gt", value: 1000000}]}`
- `evaluator_type: threshold`, `evaluator_config: {field: "amount", operator: "gt", threshold: 1000000}`

Rule B (`priority: regulatory`, level 3):
- `scope`: `{target_type: "any"}`
- `evaluator_type: field_check`, `evaluator_config: {field: "currency", operator: "eq", value: "EUR"}`

Resolution:
1. Explicit override: neither has `conflict_resolution` → fall through
2. Priority: both regulatory (3) → tie, fall through
3. Specificity (§2.15):
   - Rule A: `scope_specificity_score` = 1 (structured) + 1 (domain) + 1 (jurisdiction) + 1 (filter) = **4**; `count_bound_fields` = 3 (field, operator, threshold) → score = 4×100 + 3 = **403**
   - Rule B: `scope_specificity_score` = 0 (`target_type: "any"`) → **0**; `count_bound_fields` = 3 → score = 0×100 + 3 = **3**
   - **Rule A wins** (403 > 3). Deterministic.

**Specificity Score — Rule Pair 2 (identical rules → recency tie-break)**

Rules C and D share identical `priority: statutory`, identical `scope`, and identical composite evaluator structure.

Resolution:
1. Explicit override: neither → fall through
2. Priority: both statutory (2) → tie
3. Specificity: identical structure → tie
4. Recency: compare `created_at` frozen in `node_body`; later timestamp wins; identical timestamps → fall through
5. **Conflict Artifact** escalated for human review

**Merge Lineage ID + Execution ID (S-20)**

Input: Parent A (`lineage_id: PAY-800`, `execution_id: PAY-800`); Parent B (`lineage_id: AUTH-001`, `execution_id: AUTH-001-A`).

```
lineage_id := MIN("PAY-800", "AUTH-001") = "AUTH-001"
execution_id := "AUTH-001-M" + SHA-256(canonical_json({
  parents: ["AUTH-001", "PAY-800"],   // sorted per §2.16.1
  operation: "merge",
  timestamp: "<ISO 8601 UTC>"
}))[0:16]
lineage.parent_lineage_ids = ["AUTH-001", "PAY-800"]  // sorted
lineage.parent_execution_ids = ["AUTH-001-A", "PAY-800"]  // sorted (parent execution IDs at merge time)
```

Non-surviving parent `PAY-800` preserved in `lineage.parent_lineage_ids` and optional `metadata.migration.merge_provenance`.

**CG-IR Snapshot Hash Composition (S-23, S-24)**

Per node:
```
semantic_hash = SHA-256(canonical_json(semantic_body))
  semantic_body = {directive_id, lineage_id, deontic_type, evaluator, scope,
                   severity_default, depends_on, priority, conflict_resolution,
                   status, created_at}

presentation_hash = SHA-256(canonical_json(presentation_body))
  presentation_body = {description, directive_revision, control_version}

node_hash = SHA-256(canonical_json({semantic_hash, presentation_hash}))
```

Per edge: `edge_hash = SHA-256(canonical_json({source: directive_id, target: directive_id}))`

Snapshot: `cg_ir_snapshot_hash = SHA-256(canonical_json({node_hashes: sorted[], edge_hashes: sorted[], provenance}))`. `compiled_at` excluded.

**Determinism property:** Editorial `description` changes alter `presentation_hash` only; `semantic_hash` and downstream evaluator subgraphs keyed on it are preserved → incremental compilation reuse.

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
- Evidence submitter ≠ Remediation approver: holders of `evidence.submit` MUST NOT approve remediation for the same finding (S-14a, S-33)

---

## Epic 1: Directive Lifecycle

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Regulatory Official | I want to submit a new directive. | **Given** I express a need. **When** Selma processes it. **Then** Selma assigns lineage_id + execution_id, records in Directive Graph, compiles to CG-IR snapshot via hermetic boundary (read lock), performs structural review. **And** directive in "Draft" state with scope. | **P0** |
| **S-02** | Regulatory Official | I want to modify an existing directive. | **Given** I specify directive execution_id and change. **When** Selma processes it. **Then** Selma acquires write lock, creates new revision (same lineage_id), incrementally compiles to new CG-IR snapshot (reuses unchanged subgraph via content-addressed store), re-assesses consistency, records provenance. **And** lineage_id unchanged. **And** new Ruleset Version. | **P0** |
| **S-03** | Regulatory Official | I want to retire a directive. | **Given** I specify directive to retire. **When** Selma processes it. **Then** Selma transitions to `deprecated`, records reason, marks CG-IR nodes deprecated, generates new snapshot. | **P1** |
| **S-19** | Regulatory Official | I want to fork a directive into two distinct directives. | **Given** I specify a directive and describe the split. **When** Selma processes it. **Then** Selma creates two new execution_ids (inheriting lineage_id), records lineage (parent_lineage_ids, parent_execution_ids, operation=fork), compiles both to CG-IR, deprecates original nodes. **And** both new rules share the same lineage_id. **And** execution_ids are globally unique. | **P1** |
| **S-20** | Regulatory Official | I want to merge two directives into one. | **Given** I specify two directives and describe the merge. **When** Selma processes it. **Then** Selma assigns merged `lineage_id` = lexicographic min of parent lineage_ids, generates deterministic execution_id per §2.2.2, records sorted `lineage.parent_lineage_ids` and `lineage.parent_execution_ids`, compiles to CG-IR, deprecates both originals. **And** non-surviving parent lineage_id remains in audit history only. | **P1** |
| **S-26** | Regulatory Official | I want to split a directive into multiple independent directives. | **Given** I specify a directive and describe the restructuring. **When** Selma processes it. **Then** Selma creates multiple new execution_ids (inheriting parent lineage_id), records lineage (parent_lineage_ids, parent_execution_ids, operation=split), compiles to CG-IR, deprecates original. **And** each child has a unique execution_id. **And** all children share the parent lineage_id. | **P1** |

---

## Epic 2: Directive Governance

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-04** | Regulatory Official | I want to view all active requirements. | **Given** I request active requirements. **When** Selma processes it. **Then** Selma returns active directives and compiled nodes from current CG-IR snapshot. | **P0** |
| **S-05** | Regulatory Official | I want to inspect the regulatory set for conflicts. | **Given** I request consistency review. **When** Selma processes it. **Then** Selma assesses CG-IR, applies within-lineage `resolve_conflict` (explicit override → `compatible_overrides` for symmetric pairs → priority → specificity → recency), issues report with Conflict Artifacts for unresolvable within-lineage conflicts. **And** for cross-lineage pairs, Selma emits advisory Conflict Artifacts per §2.15.2 (binding_status=advisory, requires_human_action=true) without modifying finding dispositions. **And** conflict outcomes are deterministic for a given CG-IR snapshot (all inputs frozen in node_body). | **P1** |
| **S-06** | Regulatory Official | I want a comprehensive audit. | **Given** I request full audit. **When** Selma processes it. **Then** Selma generates audit report with gaps, redundancies, remedial measures. | **P2** |
| **S-07** | Regulatory Official | I want to view revision and lineage history of any directive. | **Given** I request history by lineage_id. **When** Selma processes it. **Then** Selma provides full revision log with timestamps, originator, changes, and lineage (fork/merge/split operations). Lineage_id constant across all revisions. | **P1** |
| **S-08** | Regulatory Official | I want to restore a directive to a previous revision. | **Given** I specify directive lineage_id and target revision. **When** Selma processes it. **Then** Selma creates new revision copying target, recompiles to new CG-IR snapshot, records provenance. | **P1** |
| **S-09** | Regulatory Official | I want to preview impact before finalizing. | **Given** I request change. **When** Selma generates proposal. **Then** Selma shows current vs proposed CG-IR snapshots, requires confirmation. | **P2** |
| **S-21** | Regulatory Official | I want to verify cross-runtime evaluator portability. | **Given** I request evaluator portability audit. **When** Selma processes it. **Then** Selma validates all regex patterns are RE2-compatible, confirms no prohibited regex features (backreferences, atomic groups), verifies numeric evaluators use IEEE 754 strict arithmetic, confirms timestamp evaluators use UTC-only, and reports any portability violations. | **P1** |
| **S-22** | Regulatory Official | I want to verify provenance canonicalization. | **Given** I request provenance audit. **When** Selma processes it. **Then** Selma validates all provenance fields are in canonical form before hash computation, confirms no non-deterministic ordering in provenance inclusion, and reports any canonicalization violations. | **P1** |
| **S-27** | Regulatory Official | I want to verify evaluator complexity limits. | **Given** I request complexity audit. **When** Selma processes it. **Then** Selma validates composite depth ≤ 32, total evaluator nodes ≤ 256, composite width ≤ 64, regex patterns ≤ 4096 chars, metadata ≤ 16 384 bytes, and lineage ancestry depth ≤ 64. **And** rejects rules exceeding limits at compile time via custom compile-time validator (JSON Schema Draft-07 alone cannot enforce recursive depth/node count limits — see §2.9). **And** the custom validator executes AFTER JSON Schema structural validation and BEFORE CG-IR generation. | **P1** |
| **S-28** | Regulatory Official | I want conflict resolution to be fully deterministic. | **Given** I request consistency review on a frozen CG-IR snapshot. **When** Selma applies `resolve_conflict`. **Then** Selma computes `specificity_score` per §2.15 normative algorithm, compares `priority_level` integers (not enum labels), resolves compatible override pairs (`{always_wins, never_wins}`, identical `defer_to` targets) via `compatible_overrides()`, ignores `defer_to` overrides on missing/ambiguous targets (fall through to computed resolution), detects `defer_to` cycles via DFS, and produces identical outcomes on repeated runs. | **P1** |
| **S-30** | Regulatory Official | I want architectural audit gates verified before production certification. | **Given** I request architectural audit per §9.9. **When** Selma runs the AA-01 through AA-07 gate suite. **Then** Selma reports pass/fail per gate with explicit gate-ID traceability: **AA-01** Mediated Feedback — no analytics→CG-IR write path (S-17, S-18); **AA-02** Declarative Governance — policy runtime prohibition, schema/CG-IR fields only (S-05); **AA-03** Evaluator Purity — no IO, randomness, or environment reads (S-10, S-21); **AA-04** Segregation of Duties — `finding.waive` denied when actor ∈ `creator_provenance`; `finding.approve_remediation` denied when actor submitted evidence (S-14a, S-29); **AA-05** Conflict Resolution Determinism — identical CG-IR snapshot + target → byte-identical conflict outcomes including `compatible_overrides()` pairs (S-05, S-28); **AA-06** Discriminator Completeness — invalid `evaluator_type`/`evaluator_config` pairings rejected by reference validator (S-21, S-27); **AA-07** Portable Serialization — RE2 canary vectors (§9.2.6) and UTC/NaN rejection tests pass (S-21, S-31). | **P1** |
| **S-31** | Regulatory Official | I want a canonical reference validator for portable compile-time checks. | **Given** I submit a rule dataset for validation. **When** Selma runs the reference validator. **Then** Selma enforces UTC-only timestamps (reject ±HH:MM offsets), rejects NaN/Infinity in numeric fields, whitelists regex flags to `{i,m,s}`, runs the §2.9 AST-walking discriminator validator, and executes RE2 canary test vectors. **And** invalid `evaluator_type`/`evaluator_config` pairings from the rejection corpus are rejected with `SchemaError`. | **P1** |

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
| **S-14a** | Regulatory Official | I want to approve remediation evidence. | **Given** I request pending reviews AND I hold `finding.approve_remediation` capability. **When** Selma presents evidence with Finding FSM state = Pending Verification. **Then** I approve (Pending Verification → Verified; system automatically transitions Verified → Closed). **And** human actor triggers only approve; closure is system-automatic per FSM. **And** event log append-only with event_hash and HLC total order. **And** I MUST NOT be the same actor who submitted the evidence (segregation of duties: S-33). **And** capability check occurs at Finding FSM Engine gate before state transition. | **P1** |
| **S-14b** | Regulatory Official | I want to reject remediation evidence. | **Given** I request pending reviews AND I hold `finding.reject_remediation` capability. **When** Selma presents evidence with Finding FSM state = Pending Verification. **Then** I reject (Pending Verification → Rejected). **And** event log append-only with event_hash and HLC total order. **And** capability check occurs at Finding FSM Engine gate before state transition. | **P1** |
| **S-14c** | Regulatory Official | I want to reopen a rejected finding. | **Given** I hold `finding.reject_remediation` capability and a finding is in Rejected state. **When** I reopen with comments (valid FSM transition: Rejected → Open). **Then** Selma transitions finding to Open state, records comments, records actor and timestamp. **And** event log append-only with event_hash and HLC total order. **And** capability check occurs at Finding FSM Engine gate before state transition. | **P1** |
| **S-25** | Regulatory Official | I want to dismiss an invalid finding. | **Given** I determine a finding is incorrect AND I hold `finding.dismiss` capability. **When** I dismiss (valid FSM transition: Open → Dismissed). **Then** Selma transitions finding to Dismissed state, records disposition "invalid", records actor and timestamp. **And** event log append-only with event_hash and HLC total order. **And** dismissed findings have no outgoing FSM transitions. **And** capability check occurs at Finding FSM Engine gate before state transition. **And** the finding remains in Finding Event Stream for audit purposes. | **P1** |
| **S-29** | Regulatory Official | I want to waive a finding as accepted risk. | **Given** I determine a finding is legitimate but the risk is accepted AND I hold `finding.waive` capability. **When** I waive (valid FSM transition: Open → Waived). **Then** Selma transitions finding to Waived state, records disposition "waived", records actor and timestamp. **And** system automatically transitions Waived → Closed. **And** event log append-only with event_hash and HLC total order. **And** I MUST NOT be the directive creator (segregation of duties: actor ∉ `creator_provenance` for finding.control_id). **And** capability check occurs at Finding FSM Engine gate before state transition. **And** waive action requires explicit `finding.waive` capability. | **P1** |

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
| Directive Governance | 1 | 9 | 2 | **12** |
| Inspection | 1 | 4 | 0 | **5** |
| Finding Management | 1 | 7 | 0 | **8** |
| Analytics & Mediated Feedback | 0 | 1 | 1 | **2** |
| Segregation of Duties | 2 | 0 | 0 | **2** |
| Capability Validation | 0 | 1 | 0 | **1** |
| **Total** | **7** | **26** | **3** | **36** |

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
| Pending Verification → Verified | approve | Regulatory Official | S-14a |
| Pending Verification → Rejected | reject | Regulatory Official | S-14b |
| Rejected → Open | "finding.reopen" (requires comments) | Regulatory Official | S-14c |
| Verified → Closed | Automatic after verification | System | — |
| Waived → Closed | Automatic after waive | System | — |

**Binding:** S-14a covers approve, S-14b covers reject, S-14c covers reopen. S-25 covers dismiss. S-29 covers waive. Verified → Closed and Waived → Closed are never human actions.

**Canonical PlantUML (implementation contract):** see [`../state-machine/selma_finding_lifecycle.puml`](../state-machine/selma_finding_lifecycle.puml) and the full catalog in [`../state-machine/README.md`](../state-machine/README.md).  
**Capability note (S-14c):** command is `finding.reopen`; gating capability is `finding.reject_remediation`.

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
| Finding FSM | S-11, S-12, S-13, S-14a, S-14b, S-14c, S-25, S-29 |
| HLC Event Ordering | S-14a, S-14b, S-14c |
| Capability-Based Permissions | S-14a, S-14b, S-14c, S-25, S-29, S-32, S-33, S-34 |
| Segregation of Duties | S-14a, S-29, S-32, S-33 |
| Formal Capability Model (§3.2.1) | S-32, S-33, S-34 |
| Conflict Resolution Mapping (explicit override first) | S-05, S-28 |
| Compatible Override Pairs (`compatible_overrides`) | S-05, S-28 |
| Cross-Lineage Advisory Resolution (§2.15.2) | S-05 |
| Specificity Determinism (normative algorithm) | S-05, S-28 |
| Architectural Audit Gates (§9.9) | S-30 |
| Portable Validator Requirements (§9.2.15) | S-21, S-31 |
| RE2 Canary Test Vectors (§9.2.6) | S-21, S-31 |
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
| **Normative Source** | SPECIFICATION.md 8.2.4 is the single normative source; schema and policy MUST conform |
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
| **Evaluator Type Safety** | `evaluator_config` MUST match `evaluator_type`; `oneOf` + `additionalProperties: false` is the primary structural discriminator; AST-walking validator (§2.9) is the normative compile-time gate |
| **Evaluator Portability** | RE2-compatible regex only; IEEE 754 strict numerics; UTC-only timestamps; NFC-normalized strings. Schema validation is necessary but insufficient — reference validator mandatory (S-21, S-31) |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver (`authored_by` / `creator_provenance`); Evidence submitter ≠ Approver |
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
| **Version Compatibility** | MAJOR versions match across spec/schema/policy; `policy_contract_version` cross-file consistency enforced at compile time (not by JSON Schema) |
| **Cross-Layer Binding** | Schema MUST conform to spec; policy MUST NOT contradict spec |
| **Concurrency Safety** | Compilation = read lock; modification = write lock |
| **Evaluator Complexity Bounds** | Depth ≤ 32, total nodes ≤ 256, width ≤ 64, regex ≤ 4096 chars, metadata ≤ 16 384 bytes (16 KiB) (§2.9) |
| **Lineage DAG Acyclicity** | Ancestry graph acyclic; max depth 64 (§2.2.3) |
| **Specificity Determinism** | `specificity_score` algorithm in §2.15 is normative |
| **Compatible Override Resolution** | Symmetric `{always_wins, never_wins}` and identical `defer_to` pairs resolve deterministically; incompatible dual overrides escalate to Conflict Artifact |
| **Defer_to Fall-Through** | Missing or ambiguous `defer_to` targets ignore override and fall through to computed resolution (priority → specificity → recency) |
| **Cross-Lineage Advisory Only** | Cross-lineage analysis produces advisory Conflict Artifacts; does not auto-modify findings or CG-IR |
| **Compilation Deadlock Prevention** | Read/write lock ordering with writer-preference and FIFO queue (§3.4) |
| **Architectural Audit Gates** | AA-01–AA-07 gates (§9.9) required for production-grade reference implementation certification |
| **Semantic/Presentation Hash Split** | `semantic_hash` excludes description; `node_hash` composes both (§2.6) |
| **Array Ordering Classification** | Ordered vs unordered arrays per §2.16.1 |
| **Metadata Informational Only** | Namespaced metadata; no executable content (§7.1); schema `patternProperties` rejects executable-sounding keys; engine MUST ignore metadata at evaluation runtime |
| **Merge Identity Determinism** | Merged `lineage_id` = lexicographic min of parents (§2.2.2) |

---

## Audit Remediation Summary

This document addresses findings from the Selma Formal Verification Audit (v8.2.2 corpus review, 2026-07-05). Remediation status:

| Finding ID | Severity | Remediation Applied | Location | Status |
| :--- | :--- | :--- | :--- | :--- |
| **F-001** | Major | Audit corpus section requires SPECIFICATION.md in all verification corpora | README.md, User_Stories.md, rule_schema.json `x-cross-layer-binding.audit_corpus` | ✅ Complete |
| **F-002** | Minor | Version references synchronized to 8.2.4 across all contract documents | All contract documents | ✅ Complete |
| **F-003** | Minor | Added `x-finding-fsm` informative annotation; schema description clarified | rule_schema.json | ✅ Complete |
| **F-004** | Minor | Added `x-discriminator-note` documenting `oneOf` as primary discriminator; `not:{required:[…]}` documented as weak secondary filter | rule_schema.json, README.md | ✅ Complete |
| **F-005** | Minor | Added `patternProperties` structural guard on metadata; §7.1 non-executability clause reinforced | rule_schema.json, SPECIFICATION.md §7.1 | ✅ Complete |
| **F-006** | Minor | Added `x-portability-note` and compile-time engine invariants table; S-21/S-31 reference validator gates | rule_schema.json, README.md, User_Stories.md | ✅ Complete |
| **F-007** | Informational | `utc_datetime` pattern enforces `…Z$` UTC suffix on all timestamp fields | rule_schema.json `definitions/utc_datetime` | ✅ Complete |
| **F-008** | Informational | Documented `oneOf` structural signature requirement for future evaluator types | README.md Compile-Time Engine Invariants | ✅ Documented |
| **F-009** | Informational | Lossy lexicographic merge acknowledged; `MERGE-NN` namespace deferred to v9.0.0 | User_Stories.md, policy_doctrine.yaml | ✅ Documented |
| **F-010** | Informational | `policy_contract_version` cross-file check documented as compile-time engine responsibility | rule_schema.json, README.md, User_Stories.md | ✅ Complete |
| **F-011** | Informational | Compatibility matrix completed (no truncation) | README.md | ✅ Complete |
| **F-012** | Informational | Story traceability confirmed: 32 stories with acceptance criteria traceable to schema/invariants | User_Stories.md Story Summary | ✅ Verified |
| **F-001** | Minor | `merged_at` strongly RECOMMENDED for audit compliance; optional for backward compatibility | SPECIFICATION.md §2.2.2, §7.1; rule_schema.json `merge_provenance.merged_at` | ✅ Complete |
| **F-002** | Minor | Active lineage definition for `defer_to` resolution after sequential multi-fork | SPECIFICATION.md §2.15 `defer_to_reference_resolution` | ✅ Complete |
| **F-003** | Minor | `sub_evaluators_recursion` complexity note verified accurate — no change required | rule_schema.json `x-complexity-limits` | ✅ Verified |
| **F-004** | Informational | `matches` operator cross-referenced to §2.9 RE2 portability constraints | SPECIFICATION.md §2.16.1 | ✅ Complete |
| **F-005** | Informational | S-30 acceptance criteria now explicitly reference AA-01 through AA-07 gate IDs | User_Stories.md S-30 | ✅ Complete |
| **F-006** | Informational | Cross-lineage presentation correlation guidance verified clear — no change required | SPECIFICATION.md §2.13.1 | ✅ Verified |

**Algorithm traceability:** Worked examples for specificity score (§2.15), merge identity (§2.2.2), and CG-IR hash composition (§2.6) added to Conflict Resolution & Hashing Deep Dive section, mechanically derivable from SPECIFICATION.md normative text.

**Architectural Soundness Score:** **98/100** (PASS — Production-Ready with Minor Clarifications). All v8.2.4 production-readiness audit findings (0 critical, 0 major, 2 minor clarifications, 4 informational) addressed. Remediation is non-breaking documentation only.
