# Universal Rule Governance Specification

**Version:** 8.2.4
**Status:** Draft Standard  
**Date:** 2026-07-05  
**Normative Source:** This document is the normative behavioral source for the Selma system.

**Version Synchronization:** All documents (SPECIFICATION.md, rule_schema.json, policy_doctrine.yaml, User_Stories.md) MUST share the same MAJOR version (8) and MUST NOT have conflicting version references. MINOR and PATCH versions MAY differ across documents within the same MAJOR family.

**Audit Corpus:** Formal verification audits MUST include all five contract documents: SPECIFICATION.md (this file), rule_schema.json, policy_doctrine.yaml, User_Stories.md, and the Contracts Directory (README.md). Projections (schema, policy, user stories) cannot substitute for the normative source when verifying algorithms in §2.6, §2.8.2, §2.15, §2.2.2, and §3.1.

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

**Policy Runtime Prohibition Enforcement (Normative):**
- Any engine implementation that loads, parses, or otherwise accesses `policy_doctrine.yaml` during runtime code paths (inspection, evaluation, FSM transitions, conflict resolution) is **non-conformant**
- Engines MUST implement configuration checks that fail if policy files are accessible from runtime modules
- Recommended: boot-time assertion that verifies policy_doctrine.yaml is absent from runtime data paths
- CI/CD pipelines MUST include static analysis that scans runtime source code for policy_doctrine.yaml references (see `scripts/validate_contracts.py`)
- Compile-time only: policy MAY be read by authors, validators, and compilation tools that generate schema/CG-IR from human prose

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
     operation: "merge",
     timestamp: lineage.timestamp
   }))[0:16].uppercase()
   // Example: TRAF-001-M3A7F2B1C4D5E6F7
   // timestamp guarantees uniqueness across re-merge attempts; 16 hex chars = 64 bits entropy

3. lineage.parent_lineage_ids := sorted unique([parent_a.lineage_id, parent_b.lineage_id])
4. lineage.parent_execution_ids := sorted unique([parent_a.id, parent_b.id])
5. Both parent rules transition to status=deprecated
```

**Invariant:** The merged `lineage_id` equals the lexicographically minimum parent `lineage_id`. The non-surviving parent `lineage_id` remains in audit history via `lineage.parent_lineage_ids` but is never reused as an active root.

**Merge Provenance Loss (Accepted Risk):** The lexicographic MIN strategy is deterministic but semantically lossy. Merging `PAY-800` with `AUTH-001` produces `AUTH-001` as the surviving root, which obscures the payment lineage provenance. Mitigations:
- The optional `metadata.migration.merge_provenance` field (§7.1, schema) explicitly maps non-surviving parent `lineage_id`s with semantic weight and context
- Downstream lineage tracing tools MUST parse `lineage.parent_lineage_ids` arrays, not rely solely on the primary identity graph
- UI/reporting layers MUST prominently surface `parent_lineage_ids` and `parent_execution_ids` for merged rules to mitigate semantic loss
- **Future (v9.0.0):** A dedicated `MERGE-NN` namespace (e.g., `MGR-18`) will replace lexicographic MIN to preserve full provenance identity in merged roots

**Merge Provenance Surfacing Requirements (Normative):**
- All reporting tools MUST display both `parent_lineage_ids` and `parent_execution_ids` when rendering merged rule lineage
- The `metadata.migration.merge_provenance.non_surviving_parents` field SHOULD be used to preserve semantic context of non-surviving parents
- `metadata.migration.merge_provenance.merged_at` is optional for backward compatibility but strongly RECOMMENDED for audit compliance; omission does not violate any invariant but may reduce audit trail completeness
- Lineage tracing APIs MUST support queries by both surviving and non-surviving parent IDs
- Audit reports MUST include complete merge provenance information for regulatory compliance

#### 2.2.3 Lineage DAG Invariants

The lineage ancestry graph MUST satisfy:

1. **Acyclicity:** No directed cycle in `(parent_lineage_ids → child lineage_id)` edges
2. **Single root per active rule:** Each active rule has exactly one `lineage_id`
3. **Parent existence:** Every ID in `parent_lineage_ids` and `parent_execution_ids` MUST reference a rule that existed at `lineage.timestamp`
4. **Operation consistency:**
   - `fork`/`split`: exactly one entry in `parent_lineage_ids` (the inherited root)
   - `merge`: exactly two entries in `parent_lineage_ids` (both parents). N-way merge is not supported in v8.2.x; only binary merge is defined.
5. **No self-reference:** A rule MUST NOT list its own `lineage_id` or `id` as a parent
6. **Depth bound:** Maximum ancestry depth = 64 operations from any leaf to root (compile-time rejection beyond limit)
7. **Temporal ordering:** `lineage.timestamp` MUST be ≥ max(parent timestamps) when parent lineage records exist

Pathological sequences (fork → merge → fork → merge chains) are permitted provided invariants 1–7 hold. Compile-time validation MUST reject cycles and depth violations.

**Lineage DAG Mechanical Validation Algorithm (Normative):**

The following algorithm MUST be executed at compile time to enforce lineage DAG invariants:

```
validate_lineage_dag(ruleset) → ValidationResult:
  // Step 1: Build ancestry graph
  graph := empty directed graph
  for each rule in ruleset:
    if rule.lineage and rule.lineage.parent_lineage_ids:
      for each parent_id in rule.lineage.parent_lineage_ids:
        add_edge(graph, parent_id → rule.lineage_id)

  // Step 2: Detect cycles using DFS
  visited := empty set
  rec_stack := empty set
  for each node in graph:
    if node not in visited:
      if has_cycle(node, graph, visited, rec_stack):
        return FAIL("Lineage DAG cycle detected")

  // Step 3: Validate parent existence
  all_lineage_ids := set(rule.lineage_id for rule in ruleset)
  for each rule in ruleset:
    if rule.lineage:
      for each parent_id in rule.lineage.parent_lineage_ids:
        if parent_id not in all_lineage_ids:
          return FAIL("Parent lineage_id does not exist: " + parent_id)
      for each parent_id in rule.lineage.parent_execution_ids:
        // Verify parent execution ID existed at lineage.timestamp
        parent_rule := find_rule_by_execution_id(parent_id, ruleset)
        if not parent_rule:
          return FAIL("Parent execution_id does not exist: " + parent_id)
        if parent_rule and parent_rule.lineage.timestamp > rule.lineage.timestamp:
          return FAIL("Parent timestamp violates temporal ordering")

  // Step 4: Validate operation consistency
  for each rule in ruleset:
    if rule.lineage:
      op := rule.lineage.operation
      parent_count := length(rule.lineage.parent_lineage_ids)
      if op == "merge" and parent_count != 2:
        return FAIL("Merge operation must have exactly 2 parent_lineage_ids")
      if (op == "fork" or op == "split") and parent_count != 1:
        return FAIL("Fork/Split operation must have exactly 1 parent_lineage_id")

  // Step 5: Validate depth bound
  for each rule in ruleset:
    depth := compute_ancestry_depth(rule.lineage_id, graph)
    if depth > 64:
      return FAIL("Lineage depth exceeded: " + depth + " > 64")

  // Step 6: Validate no self-reference
  for each rule in ruleset:
    if rule.lineage:
      if rule.lineage_id in rule.lineage.parent_lineage_ids:
        return FAIL("Rule references itself in parent_lineage_ids")
      if rule.id in rule.lineage.parent_execution_ids:
        return FAIL("Rule references itself in parent_execution_ids")

  return PASS

compute_ancestry_depth(lineage_id, graph) → integer:
  visited := empty set
  queue := [(lineage_id, 0)]
  max_depth := 0
  while queue not empty:
    (current, depth) := dequeue(queue)
    if current in visited: continue
    visited.add(current)
    max_depth := max(max_depth, depth)
    for each parent in graph.get_parents(current):
      enqueue(queue, (parent, depth + 1))
  return max_depth

has_cycle(node, graph, visited, rec_stack) → bool:
  visited.add(node)
  rec_stack.add(node)
  for each child in graph.get_children(node):
    if child not in visited:
      if has_cycle(child, graph, visited, rec_stack):
        return true
    else if child in rec_stack:
      return true
  rec_stack.remove(node)
  return false
```

**Validation Artifact:** The validation result MUST be recorded in the CG-IR snapshot provenance as `lineage_validation: {status: PASS|FAIL, timestamp, algorithm_version: "1.0"}`

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

The dual hash model separates compilation-relevant identity (`semantic_hash`) from editorial identity (`presentation_hash`), enabling incremental compilation to reuse evaluator subgraphs when only human-readable descriptions change.

| Hash | Input | Purpose |
| :--- | :--- | :--- |
| **semantic_hash** | `semantic_body` (deontic_type, evaluator, scope, depends_on, priority, conflict_resolution, status, severity_default) | Compilation cache identity; unchanged by editorial description edits |
| **presentation_hash** | `presentation_body` (description, directive_revision, control_version) | Audit/display drift detection |
| **node_hash** | SHA-256(canonical_json({semantic_hash, presentation_hash})) | Content-addressed storage key |

```
semantic_body = {
  directive_id, lineage_id,
  deontic_type,         // obligation | prohibition | permission — compiled from rule.type
  evaluator, scope, severity_default,
  depends_on,           // sorted array (§2.16)
  priority, conflict_resolution, status,
  created_at            // frozen authoring timestamp for conflict resolution recency
}

presentation_body = {
  description, directive_revision, control_version
}

node_body = union(semantic_body, presentation_body)  // 14 fields total

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

**Provenance Canonicalization Requirement:** All provenance fields MUST be canonicalized (normalized to canonical form per §2.16) before inclusion in the snapshot hash input. Specifically:
- `engine_version` and `frozen_env_hash` are normalized strings (no trailing whitespace, case-sensitive as defined)
- `directive_graph_version` follows semver normalization (no leading `v`, zero-padded numeric components)
- `compiled_at` is NOT part of the snapshot hash input. It is recorded in execution artifact metadata (inspection snapshots, pipeline traces) only. This exclusion ensures snapshot hash determinism regardless of when compilation executes
- If future extensions add provenance fields, each field MUST be declared with a canonical form before inclusion in hash computation

**Incremental Compilation Algorithm:**
1. Compute the set of changed `lineage_id` values by comparing current vs. previous directive graph
2. For each changed `lineage_id`, mark its node and all transitive dependents as dirty
3. Recompute dirty nodes
4. Reuse unchanged `node_hash` values from the previous snapshot
5. Recompute edge hashes for any dirty node's edges
6. Recompute snapshot hash

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

**Frozen Environment Schema:**

```json
{
  "engine_version": "semver",
  "toolchain": {
    "compiler": "string",
    "os_runtime_hash": "sha256"
  },
  "ai_components": [
    {
      "name": "string",
      "model_hash": "sha256",
      "prompt_hash": "sha256",
      "decoder_hash": "sha256"
    }
  ],
  "confidence_severity_cap_threshold": 0.5,
  "frozen_env_hash": "sha256"
}
```

`frozen_env_hash` = SHA-256(canonical_json(above minus `frozen_env_hash` itself))

`frozen_env_hash` is a computed digest. The hash input is the frozen environment object with the `frozen_env_hash` key excluded. Implementations MUST NOT include `frozen_env_hash` in its own computation.

### 2.8 CG-IR Node Schema

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | String | Unique node identifier |
| `directive_id` | String | Canonical directive ID |
| `lineage_id` | String | Immutable lineage root |
| `deontic_type` | Enum | `obligation`, `prohibition`, or `permission`. Compiled from rule.`type`. Drives evaluation semantics (§2.8.3). |
| `directive_revision` | String | Revision of source directive |
| `control_version` | String | Version of evaluation logic |
| `description` | String | Human-readable description |
| `evaluator` | Object | Pure evaluator specification |
| `scope` | Object | Applicability context (see §2.8.2) |
| `severity_default` | Enum | Default severity on failure |
| `depends_on` | Array | Node IDs (`directive_id` execution IDs) evaluated first — NOT `lineage_id`s |
| `priority` | Enum | Authority level for conflict resolution |
| `conflict_resolution` | Object | Optional explicit override |
| `status` | Enum | `active`, `deprecated` |
| `created_at` | Datetime (ISO 8601 UTC) | Authoring timestamp, frozen from `rule.created_at`. Used for conflict resolution recency comparison |

### 2.8.1 Rule-to-CG-IR Node Mapping

| Rule Schema Field | CG-IR Node Field | Transform | Notes |
| :--- | :--- | :--- | :--- |
| `id` | `directive_id` | Direct copy | Execution ID becomes node's canonical ID |
| `lineage_id` | `lineage_id` | Direct copy | Immutable root |
| `type` | `deontic_type` | Direct copy | Compiled into CG-IR for evaluation semantics (§2.8.3). Permissions require informational-only findings on fail. |
| `directive_revision` | `directive_revision` | Direct copy | Revision of source directive. Optional — empty string if not specified. |
| `control_version` | `control_version` | Direct copy | Version of evaluation logic. Optional — empty string if not specified. |
| `message` | `description` | Direct copy | Renamed for CG-IR convention |
| `evaluator_type` + `evaluator_config` | `evaluator` | Merge into `{"type": evaluator_type, "config": evaluator_config}` | Single evaluator object in CG-IR |
| `weight` | `severity_default` | Direct copy | Weight maps to default severity on failure |
| `target` | `scope.target_type` | Extract target_type if parseable | Compile-time only; best-effort extraction |
| `priority` | `priority` | Direct copy | Used by conflict resolution |
| `depends_on` | `depends_on` | Transform from rule.id refs to node directive_id refs | Stores **execution IDs** (`rule.id` → `node.directive_id`), NOT `lineage_id`s. Resolved at compile time. After fork/split, multiple nodes may share a `lineage_id` — `depends_on` references the specific execution ID to disambiguate. |
| `conflict_resolution` | `conflict_resolution` | Direct copy | Used by conflict resolution |
| `status` | `status` | Map: `draft`→`active`, `active`→`active`, `deprecated`→`deprecated`, `superseded`→`deprecated` | Drafts compile as active for testing |
| `created_at` | `created_at` | Direct copy | Frozen for conflict resolution recency |
| `anchor_ref` | _(not compiled)_ | Dropped | Compile-time-only field |
| `rationale` | _(not compiled)_ | Dropped | Compile-time-only field |
| `remediation` | _(not compiled)_ | Dropped | Compile-time-only field |
| `parameters` | Merged into `evaluator.config` | Shallow merge | Parameters override evaluator_config keys on conflict |
| `expires_at` | _(not compiled)_ | Dropped | Compile-time-only field; expiration is a separate scheduler concern |
| `lineage` | _(not in node_body)_ | Recorded in provenance only | Lineage metadata in snapshot provenance, not node body |
| `metadata.audit.authored_by` (per-rule) | `creator_provenance` (snapshot node provenance) | Copy as sorted unique array | Excluded from `node_body` hash; used for segregation of duties at `finding.waive` (§3.2) |
| `metadata` (per-rule, other) | _(not compiled)_ | Dropped | Other per-rule metadata is informational only (§7.1); not compiled into CG-IR |

### 2.8.2 Scope Object Schema

```json
{
  "target_type": "enum (text | structured | binary | any)",
  "domain": "string",
  "jurisdiction": "string",
  "filters": [
    {
      "field": "string (path within target metadata or content)",
      "operator": "enum (eq | neq | in | subset)",
      "value": "any"
    }
  ]
}
```

**Scope Specificity Score Function:**

```
scope_specificity_score(scope) =
  (1 if scope.target_type != "any" else 0) +
  (1 if scope.domain is non-empty else 0) +
  (1 if scope.jurisdiction is non-empty else 0) +
  length(scope.filters)
```

Rules with no scope object (or all-default scope) have `scope_specificity_score = 0`.

### 2.8.3 Deontic Type Evaluation Semantics

| Type | Evaluator Pass | Evaluator Fail | Evaluator Partial | Evaluator NeedsReview |
| :--- | :--- | :--- | :--- | :--- |
| `obligation` | No finding | Finding (severity_default) | Finding (downgraded) | Finding (informational) |
| `prohibition` | No finding | Finding (severity_default) | Finding (downgraded) | Finding (informational) |
| `permission` | No finding | Finding (informational, advisory) | No finding | No finding |

**Rationale:**
- `obligation` fail = requirement not met → violation
- `prohibition` fail = prohibited thing occurred → violation
- `permission` fail = permitted thing did not occur → advisory only (you COULD do this, you didn't — not a violation)

### 2.8.4 Compile-Time-Only Fields

The following rule schema fields are NOT compiled into CG-IR nodes. They exist in the rule schema for authoring-time tooling, documentation, and human-readable reports. The runtime engine never accesses them:

`anchor_ref`, `rationale`, `remediation`, `expires_at`, `conflicts_with` (consumed at compile time to generate candidate conflict pairs per §2.15.1; pairs recorded in snapshot metadata, not present in CG-IR nodes), `target` (best-effort extraction to `scope.target_type` only; the `target` field itself is not present in CG-IR nodes), `parameters` — values are shallow-merged into `evaluator.config` at compile time; the `parameters` field itself is not present in the CG-IR node, only the merged result within the evaluator object survives compilation.
`message` and `weight` are **compile-time-only** at the rule schema level. `message` maps to CG-IR `description`; `weight` maps to CG-IR `severity_default`. The rule-schema field names `message` and `weight` are not present in CG-IR nodes — only their renamed targets survive.

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
| Maximum `metadata` serialized size per rule | 16 384 bytes (16 KiB) | `SchemaError: metadata too large` |

**JSON Schema Draft-07 Enforcement Limitation (Normative):**

JSON Schema Draft-07 cannot natively enforce recursive depth limits or aggregate node count limits across nested evaluator trees. Schema `maxItems` validates array length at a single level but does not recursively enforce total node counts across nested `sub_evaluators`. Therefore:

1. The complexity limits above (depth ≤ 32, total nodes ≤ 256, width ≤ 64) **MUST** be enforced by custom compile-time validators — NOT by JSON Schema validation alone.
2. JSON Schema validation serves as a **first-pass structural filter** (validating individual evaluator configs, field types, and array bounds at each level). The custom validator is the **normative gate** for recursive complexity limits.
3. Reference implementations MUST ship a standalone evaluator complexity validator as part of the Control Compilation Engine. This validator MUST walk the evaluator AST and enforce all limits before CG-IR generation.
4. Engines that skip the custom validator are **non-conformant** — schema structural validation alone is insufficient to prevent stack exhaustion from deeply nested composite evaluators.

**Custom Validator Implementation Guidance (Informative):**

```
validate_evaluator_complexity(rule) → ValidationResult:
  // Walk the evaluator tree recursively
  result := count_evaluator_nodes(rule.evaluator, depth=0)
  
  if result.max_depth > 32:
    return FAIL("SchemaError: evaluator depth exceeded")
  if result.total_nodes > 256:
    return FAIL("SchemaError: evaluator count exceeded")
  if result.max_width > 64:
    return FAIL("SchemaError: evaluator width exceeded")
  
  // Regex pattern length check
  for each leaf_evaluator in walk_leaves(rule.evaluator):
    if leaf_evaluator.type == "regex":
      if length(leaf_evaluator.config.pattern) > 4096:
        return FAIL("SchemaError: pattern too long")
  
  // Metadata size check
  metadata_size := byte_length(canonical_json(rule.metadata))
  if metadata_size > 16384:
    return FAIL("SchemaError: metadata too large (exceeds 16,384 bytes / 16 KiB)")
  
  return PASS
```

**Validation Timing:** The custom complexity validator MUST execute as a mandatory pass AFTER JSON Schema structural validation and BEFORE CG-IR generation. If either validation fails, compilation MUST be rejected with no partial CG-IR output.

**Evaluator Complexity Counting Algorithm (Normative):**

The following algorithm MUST be used to compute evaluator complexity metrics:

```
count_evaluator_nodes(evaluator, depth=0) → {total_nodes, max_depth, max_width}:
  // Initialize counters
  total_nodes := 1  // Count current evaluator
  max_depth := depth
  max_width := 0
  current_width := 0

  // Handle composite evaluators
  if evaluator.type == "composite":
    current_width := length(evaluator.config.sub_evaluators)
    max_width := max(max_width, current_width)
    
    if depth >= 32:
      return ERROR("Max depth exceeded")
    
    if current_width > 64:
      return ERROR("Max width exceeded")
    
    // Recursively count sub-evaluators
    for each sub_eval in evaluator.config.sub_evaluators:
      child_result := count_evaluator_nodes(sub_eval, depth + 1)
      total_nodes += child_result.total_nodes
      max_depth := max(max_depth, child_result.max_depth)
      max_width := max(max_width, child_result.max_width)
      
      if total_nodes > 256:
        return ERROR("Max nodes exceeded")

  // Handle leaf evaluators
  elif evaluator.type == "regex":
    if length(evaluator.config.pattern) > 4096:
      return ERROR("Pattern too long")

  return {total_nodes, max_depth, max_width}
```

**Complexity Validation Timing:** All complexity checks MUST be performed at compile time. Engines MUST reject rules that exceed any complexity limit before CG-IR generation.

**Regex catastrophic backtracking mitigation:** All regex patterns MUST be RE2-compatible (§2.9 portability). Compile-time validation MUST reject patterns exceeding length limit. Runtime engines SHOULD enforce per-node evaluation timeout (§2.12).

**Discriminator Validation:** `evaluator_type` ↔ `evaluator_config` consistency is a semantic invariant. JSON Schema `if`/`then` `not:{required:[…]}` blocks are a weak first-pass filter only (they reject only when all listed forbidden fields are simultaneously present). The primary structural discriminator is `evaluator_config` `oneOf` with `additionalProperties: false` per branch. Compile-time validation MUST apply a formal AST-walking validator that implements the following algorithm:

```
validate_evaluator_pairing(rule):
  // Step 1: Type-specific required-field assertions
  match rule.evaluator_type:
    "regex":
      assert "pattern" in rule.evaluator_config           // string, 1-4096 chars
      assert "flags" in rule.evaluator_config →           // optional, pattern: ^[ims]*$
        assert rule.evaluator_config.flags matches "^[ims]*$"
      assert no unrecognized keys in rule.evaluator_config // only pattern, flags

    "field_check":
      assert "field" in rule.evaluator_config              // string, non-empty
      assert "operator" in rule.evaluator_config            // eq|neq|gt|gte|lt|lte|contains|matches
      assert "value" in rule.evaluator_config               // any JSON value
      assert no unrecognized keys in rule.evaluator_config  // only field, operator, value

    "threshold":
      assert "field" in rule.evaluator_config               // string, non-empty
      assert "operator" in rule.evaluator_config             // gt|gte|lt|lte only
      assert "threshold" in rule.evaluator_config            // number
      assert no unrecognized keys in rule.evaluator_config   // only field, operator, threshold

    "composite":
      assert "logic" in rule.evaluator_config                // and|or|not
      assert "sub_evaluators" in rule.evaluator_config       // array, 1-64 items
      for each sub in rule.evaluator_config.sub_evaluators:
        validate_evaluator_pairing(sub)                      // recursive AST walk

  // Step 2: Cross-field binding verification
  // For each oneOf variant in the evaluator_config schema, the validator MUST check
  // that the x-evaluator-type annotation matches the parent evaluator_type.
  // This catches cases where a regex config accidentally matches a field_check schema.
  assert rule.evaluator_config matches exactly_one_schema_variant(rule.evaluator_type)

  // Step 3: Reject structural mismatches
  // If evaluator_type is "regex" but evaluator_config has "field" or "threshold",
  // the validator MUST reject regardless of partial schema match.
  assert no cross-type key leakage
```

Engines MUST NOT rely on partial subschema validation for evaluator pairing. The standard JSON Schema `if`/`then` mechanism is a first-pass filter only; the formal AST walker above is the normative gate. Implementations SHOULD integrate this validator as a standalone pass before or after JSON Schema validation to ensure no invalid pairing passes through structural checks.

### 2.9.1 Outcome-to-Finding Mapping

| Evaluator Outcome | Finding Created? | Default Severity | Notes |
| :--- | :--- | :--- | :--- |
| `Pass` | No | N/A | No finding generated |
| `Fail` | Yes | `node.severity_default` | Standard failure finding |
| `Partial` | Yes | Downgraded by one level from `severity_default` | `critical`→`high`, `high`→`medium`, `medium`→`low`, `low`→`informational`, `informational`→`informational` |
| `NeedsReview` | Yes | `informational` | Always informational regardless of severity_default — cannot escalate without human review |

**Confidence threshold (optional):** If `confidence` is below the configured threshold, the finding severity is capped at `informational` regardless of outcome. This prevents low-confidence failures from appearing as critical. The confidence threshold (default: `0.5`) is configurable in the frozen environment under `confidence_severity_cap_threshold`. If not specified, `0.5` is used.

**`permission` type special case:** When a `permission` rule's evaluator returns `Fail`, the finding severity is ALWAYS `informational` regardless of `severity_default`. A permission failure means "the permitted action was not taken" — this is advisory, not a violation.

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
    "findings_by_directive_id": "object (directive_id → count)",
    "last_inspection_date": "datetime",
    "recurrence_count": "integer"
  }
}
```

**No Write-Back:** Evaluators cannot modify context.

**`finding_aggregates` Semantics:** `finding_aggregates` is pre-computed from PREVIOUS inspections' finding event streams BEFORE the current DAG execution begins. Current-inspection findings do NOT populate this field. This preserves the read-only context invariant (§2.12) — no shared mutable state during DAG execution.

**Aggregation Latency Warning:** Because `finding_aggregates` reflects only pre-inspection state, compliance dashboards and escalation systems that depend on real-time severity aggregation will experience at-least-one-inspection-cycle delay. For example, if a critical violation occurs during the current inspection, `finding_aggregates` will not reflect it until the next inspection of the same target. Implementations SHOULD:
- Document this latency in compliance dashboards (e.g., "Aggregates reflect prior inspection state")
- Consider multi-pass inspection within a single pipeline if real-time escalation is required
- Rely on individual finding events (via the Finding Event Stream) for immediate alerting; use `finding_aggregates` for trend analysis and dashboard views only

### 2.12 DAG Execution Semantics

| Aspect | Rule |
| :--- | :--- |
| **Evaluation Order** | Topological sort respecting `depends_on` |
| **Cycle Detection** | Enforced at compile time |
| **Parallel Execution** | Independent nodes execute in parallel |
| **State Propagation** | Read-only context; no shared mutable state |
| **Timeout** | Per-node configurable (default: 30s) |
| **Retry** | Deterministic evaluation failures: no retries (permanent state). Infrastructure timeouts: configurable retry (default: 0, max: 3) per §3.3. Failed nodes → `NeedsReview`. |
| **Skipped Nodes** | Dependency-failed nodes produce NO finding. They generate a `Skipped` pipeline trace entry only. The parent inspection snapshot records them in `skipped_nodes`. This prevents cascading false positives from dependency failures |

### 2.13 Inspection Consistency Model

An inspection produces a **point-in-time snapshot**:

| Aspect | Rule |
| :--- | :--- |
| **Snapshot** | Complete evaluation state at completion |
| **Partial execution** | Skipped nodes recorded; report marks partial results |
| **Report** | Consistent point-in-time view including partial results |
| **Reproducibility** | Same CG-IR + same target + same frozen_env = same snapshot |
| **Immutability** | Once completed, never modified |

### 2.13.1 Reinspection Semantics

Reinspection creates a completely new inspection with a new `inspection_id` and new findings. Findings from previous inspections of the same target are NOT automatically affected.

**Correlation model:** Findings are correlated by `target_id` + `lineage_id`. A dashboard view MAY group findings across inspections by these fields, but this is a presentation concern — the Finding Event Stream remains append-only with no cross-inspection mutation.

**Cross-lineage presentation correlation:** When a target is reinspected after merge, split, or fork operations that change `lineage_id` associations, correlation by `target_id + lineage_id` alone will not group historical findings across lineage boundaries. Dashboards and reporting layers that require cross-inspection historical grouping MUST implement application-layer correlation logic (e.g., by `target_id` alone, by Machine ID root ancestry via `lineage.parent_lineage_ids`, or by explicit supersession links). The Finding Event Stream and inspection snapshots remain immutable; cross-lineage grouping is never a runtime engine responsibility.

**Supersession (manual only):** A Regulatory Official MAY close a previous finding with disposition `superseded` via a manual FSM transition (if implemented) or by adding `superseded` as an additional disposition value with its own capability (`finding.supersede`). This is NOT automatic on reinspection.

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

**Event Payload Structures:**

| `event_type` | Required `payload` fields |
| :--- | :--- |
| `FindingCreated` | `finding_id`, `lineage_id`, `control_id` (directive_id), `inspection_id`, `fsm_state` (`Created`), `severity`, `outcome`, `confidence`, `evidence`, `reasoning` |
| `DispositionChanged` | `previous_disposition`, `new_disposition`, `previous_fsm_state`, `new_fsm_state`, `reason` (optional) |
| `FindingClosed` | `final_disposition`, `final_fsm_state`, `closure_reason` (optional) |

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

**Event Hash Composition:** `event_hash` = SHA-256(canonical_json(event minus `event_hash` field)). The event (excluding `event_hash` itself) is serialized in canonical JSON form per §2.16 before hashing. This ensures `event_hash` covers all event fields including `logical_clock` and `payload`.

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

### 2.15.1 Conflict Detection

Conflicts are identified through two mechanisms:

**Mechanism 1: Declared Conflicts (compile-time)**
The `conflicts_with` schema field declares explicit conflict pairs. At compilation, the engine generates candidate conflict pairs from all active rules' `conflicts_with` arrays. These pairs are recorded in the CG-IR snapshot metadata and fed to `resolve_conflict` at evaluation time if both rules in a pair produce findings for the same target.

**Mechanism 2: Outcome Contradiction (evaluation-time)**
When two active rules sharing a `lineage_id` both produce `Fail` findings for the same target, and their `type` fields are contradictory (one `obligation` and one `prohibition` about the same target aspect), the engine flags this as a conflict and applies `resolve_conflict`.

**Non-Conflicting Outcomes:**
- Both Pass: no conflict
- One Pass, one Fail: no conflict (only failing rules enter conflict resolution)
- Both Fail with same type: no conflict (both findings stand independently)
- One Fail, one NeedsReview: no conflict (NeedsReview does not contradict)

**Operational guidance (NeedsReview + Fail overlap):** When one rule produces `Fail` and another produces `NeedsReview` for the same target within the same lineage, automatic conflict detection does not fire (by design). Operational review workflows SHOULD treat co-occurring `Fail` and `NeedsReview` findings for the same target as a related set requiring joint human review, as ambiguity findings may contextualize or qualify violation findings.

**Cross-Lineage:** Mechanism 2 does not apply across lineage boundaries. Cross-lineage findings never trigger automatic conflict resolution — they are always reported as independent findings. Humans may request cross-lineage analysis via S-05, which produces advisory Conflict Artifacts (not automatic resolution).

**Temporal Binding Guarantee:** The `created_at` field used in conflict resolution is the directive's authoring timestamp, frozen into `node_body` at compilation time. It is a static property of the CG-IR node — NOT evaluation time, NOT wall clock time. For a given CG-IR snapshot, conflict resolution outcomes are fully deterministic because all inputs (`priority`, `conflict_resolution`, `created_at`, `scope` for specificity) are frozen in the immutable snapshot. Two evaluations of the same CG-IR snapshot against the same target always produce identical conflict outcomes, regardless of when evaluation occurs.

| Intent (Policy — authoring only) | Schema Field | Operator (CG-IR — runtime) | Implementation |
| :--- | :--- | :--- | :--- |
| "Higher priority wins" | `priority` | `max(priority_level)` | Constitutional(1) > Statutory(2) > Regulatory(3) > Operational(4) > Advisory(5) |
| "More specific wins" | scope constraints, evaluator bindings | `specificity_score(rule) > specificity_score(other)` | Formal algorithm below |
| "Newer wins" | `created_at` | `max(created_at)` | ISO 8601 timestamp comparison |
| N/A (schema-only) | `conflict_resolution` | `has_field(conflict_resolution)` | Checked first, before all computed factors |

**Cross-Layer Precedence Chain:**

| Layer | Role | Runtime Influence |
| :--- | :--- | :--- |
| **Policy** | Declares governance intent for human authors. Documents what priority levels mean. | **None.** Not read at inspection, evaluation, or conflict resolution runtime. |
| **Schema** | Encodes `priority`, `created_at`, `conflict_resolution` as structural fields. | **Data carrier only.** Fields are read by the engine; schema itself is not an algorithm. |
| **Spec (this document)** | Normative `resolve_conflict` algorithm. | **Sole executable source.** All runtime conflict decisions flow through this function. |

**`node_id` Mapping:** The CG-IR `node_id` is a unique node identifier generated at compilation time. It is derived from `directive_id` (the execution ID) to ensure global uniqueness within a snapshot. The mapping is: `rule.id` → `directive_id` → `node_id` (uniquely derived). Unlike `directive_id` and `lineage_id`, `node_id` is a compilation artifact and has no corresponding field in the rule schema — it is assigned during CG-IR generation.

**Compile-Time Translation (not runtime):** When compiling policy prose to schema, authors set `priority` and optional `conflict_resolution` fields. A compile-time validator MAY check that priority assignments are consistent with policy intent — but this validation produces errors/warnings at compile time only; it does not create a second runtime decision path.

**Specificity Score Algorithm (normative):**

```
specificity_score(node) → non-negative integer

score = 0

// 1. Scope constraint specificity (§2.8.2 scope_specificity_score)
//    Includes target_type discrimination (text | structured | binary | any)
score += scope_specificity_score(scope) * 100

// 2. Evaluator field binding (more constrained = more specific)
score += count_bound_fields(node.evaluator)   // regex pattern=1, field_check=3, threshold=3, composite=sum(children)

// 3. Explicit priority within same level does NOT affect specificity (handled by priority step)

Tie on equal score → proceed to recency step
```

`count_bound_fields` recursively counts required evaluator config fields. Composite evaluators sum child scores. Evaluator complexity contributes to specificity because a rule with more evaluation constraints is more narrowly targeted. Two engines implementing this algorithm MUST produce identical scores for identical CG-IR node bodies. The algorithm operates exclusively on CG-IR node fields — compile-time-only rule schema fields (e.g., `rule.target`) are NOT accessed at runtime.

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

// Step 1: Explicit override takes precedence (single-sided)
1. if rule_a.conflict_resolution and not rule_b.conflict_resolution:
     result := apply_strategy(rule_a.conflict_resolution, rule_a, rule_b)
     if result is WinningRule: return result
     // null → fall through to Step 2
2. if rule_b.conflict_resolution and not rule_a.conflict_resolution:
     result := apply_strategy(rule_b.conflict_resolution, rule_b, rule_a)
     if result is WinningRule: return result
     // null → fall through to Step 2

// Step 1b: Dual explicit overrides — compatible pairs resolve deterministically
3. if both have conflict_resolution:
     if compatible_overrides(rule_a.conflict_resolution, rule_b.conflict_resolution):
       return apply_compatible_overrides(rule_a, rule_b)
     else:
       return Conflict Artifact (escalate — incompatible override pairing)

// Step 2: Computed resolution (when no explicit override applies)
4. if rule_a.priority != rule_b.priority:
     return rule with lower priority_level number
5. if specificity(rule_a) != specificity(rule_b):
     return rule with higher specificity score
6. if rule_a.created_at != rule_b.created_at:
     return rule with newer timestamp

// Step 3: Unresolvable
7. return Conflict Artifact (escalate to human)

compatible_overrides(strategy_a, strategy_b) → bool:
  // Complementary symmetric pairs — deterministic, not ambiguous
  if (strategy_a.strategy == "always_wins" and strategy_b.strategy == "never_wins") or
     (strategy_a.strategy == "never_wins" and strategy_b.strategy == "always_wins"):
    return true
  // Identical defer_to target — both defer to the same execution ID
  if strategy_a.strategy == "defer_to" and strategy_b.strategy == "defer_to":
    return strategy_a.defer_to == strategy_b.defer_to
  return false

apply_compatible_overrides(rule_a, rule_b) → winning_rule | Conflict Artifact:
  sa := rule_a.conflict_resolution
  sb := rule_b.conflict_resolution
  if sa.strategy == "always_wins" and sb.strategy == "never_wins":
    return rule_a
  if sa.strategy == "never_wins" and sb.strategy == "always_wins":
    return rule_b
  if sa.strategy == "defer_to" and sb.strategy == "defer_to":
    target := resolve_defer_to_target(sa, rule_a, rule_b)
    if target is ActiveRule: return target
    return null  // fall through to Step 2 computed resolution
  return Conflict Artifact

apply_strategy(strategy, rule, other_rule) → winning_rule | null:
  - "always_wins": return rule
  - "never_wins": return other_rule
  - "defer_to":
      target := resolve_defer_to_target(strategy, rule, other_rule)
      if target is ActiveRule: return target
      return null  // target not found or ambiguous — fall through to computed resolution (Step 2)

resolve_defer_to_target(strategy, rule, other_rule) → ActiveRule | null:
  // Delegates to defer_to_reference_resolution algorithm below.
  // Returns null (not Conflict Artifact) when target is missing, deprecated-with-no-successor,
  // or post-fork ambiguous — caller falls through to computed resolution.
  // Returns Conflict Artifact ONLY when called from apply_compatible_overrides with
  // post-fork ambiguity on a dual-defer_to pair (both rules defer to same target that
  // itself cannot be resolved — escalate).

defer_to_cycle_detection(defer_graph) → bool:
  // defer_graph: map of rule_id → defer_to target_execution_id (only rules with strategy=defer_to)
  // Returns true if any directed cycle exists (cycle found → all defer_to overrides ignored)
  visited := empty set
  for each node in defer_graph:
    if dfs_has_cycle(node, defer_graph, visited, path=empty set):
      return true
  return false

dfs_has_cycle(node, graph, visited, path) → bool:
  if node in path: return true          // back-edge → cycle
  if node in visited: return false      // already explored acyclic subtree
  path.add(node)
  if node in graph:
    next := graph[node]
    if dfs_has_cycle(next, graph, visited, path): return true
  path.remove(node)
  visited.add(node)
  return false

// Before applying any defer_to override in a conflict pair, engines MUST run
// defer_to_cycle_detection on the {rule_a, rule_b} defer_to subgraph.
// If a cycle is detected, both defer_to overrides are ignored → fall through to Step 2.

defer_to_reference_resolution:
  - defer_to contains a rule id (execution ID), not a lineage_id
  - Resolution occurs at compile time: the engine resolves the referenced execution ID to a CG-IR node in the current ruleset snapshot
  - Resolution algorithm (normative):
    1. Let target_execution_id = strategy.defer_to
    2. If target_execution_id == rule.id (self-reference): ignore override; fall through to computed resolution
    3. If target_execution_id exists as an active rule id in the current ruleset: resolve to that rule
    4. Else if target_execution_id exists as a deprecated or superseded rule id:
       a. Let lineage_L = the lineage_id of the referenced rule
       b. Find all active rules with lineage_id == lineage_L (status = active or draft)
       c. If exactly one active rule exists: resolve to that rule (lineage chain successor)
       d. If zero active rules exist: ignore override; fall through to computed resolution
       e. If multiple active rules exist (post-fork ambiguity): return Conflict Artifact — human resolution required; do NOT apply defer_to override
    5. Else (target not found in ruleset at all): ignore override; fall through to computed resolution
  - Active rule definition: status is `active` or `draft` (draft compiles as active per §2.8.1)
  - **Active lineage definition:** A lineage is active if it contains at least one rule with status `active` or `draft`. When resolving a deprecated `defer_to` target via lineage chain successor lookup (step 4): if exactly one active rule exists in that lineage, resolve to it; if zero active rules exist, ignore the override and fall through to computed resolution; if more than one active rule exists (post-fork ambiguity after sequential forks), escalate to Conflict Artifact — do NOT apply the `defer_to` override
  - The resolved target MUST be compiled into the same CG-IR snapshot as the deferring rule
  - defer_to MUST NOT reference the rule's own id (self-deference is ignored)

scope_boundary:
  Conflict resolution applies within same lineage_id.
  Cross-lineage conflicts are flagged as Conflict Artifacts for human review.
```

#### 2.15.2 Cross-Lineage Advisory Resolution

Cross-lineage conflicts do not invoke `resolve_conflict` automatically (§2.15.1 Mechanism 2). When a human requests cross-lineage analysis (S-05), the engine produces **advisory Conflict Artifacts** — informational records that do not alter finding dispositions or CG-IR state.

**Advisory Resolution Algorithm (normative):**

```
cross_lineage_advisory(rule_a, rule_b) → AdvisoryConflictArtifact

preconditions:
  - rule_a.lineage_id != rule_b.lineage_id
  - both rules are active in the current CG-IR snapshot
  - human actor holds conflict.resolve capability (or consistency review is requested)

steps:
  1. Compute pairwise specificity_score for both rules (§2.15 algorithm)
  2. Compute priority_level integers for both rules
  3. Record created_at timestamps for both rules
  4. Apply the same precedence chain as resolve_conflict Steps 2–3:
     priority → specificity → recency
  5. Emit AdvisoryConflictArtifact with:
     - recommended_winner: rule selected by precedence chain (or null if tied on all factors)
     - resolution_basis: {priority, specificity, recency} scores used
     - binding_status: "advisory" (MUST NOT auto-dismiss or auto-merge findings)
     - requires_human_action: true

constraints:
  - Advisory outcomes MUST NOT modify finding FSM state
  - Advisory outcomes MUST NOT be replayed as automatic resolution on subsequent inspections
  - Identical CG-IR snapshot + identical rule pair → identical advisory output (deterministic)
  - If both rules produce only Pass findings for the target, no advisory artifact is emitted
```

**Distinction from within-lineage resolution:** Within-lineage conflicts bind finding dispositions via `resolve_conflict`. Cross-lineage advisories inform governance review only; the Regulatory Official MUST explicitly act (e.g., directive merge via S-20, retire via S-03) to resolve structural conflicts.

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
| **Hash algorithm version** | `1` — flat `node_body` hash (deprecated 8.2.0); `2` — dual-hash model (`semantic_hash` + `presentation_hash`, current) |

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
| `field_check` | `field`, `operator`, `value` | `{"field":"...","operator":"...","value":...}`. Operator `matches` performs regex matching against the field value. The `matches` operator is RE2-compatible per §2.9 portability constraints (regex dialect, prohibited PCRE-only features, flags limited to `{i,m,s}`). |
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

| From | To | Trigger | Allowed Actor | Story |
| :--- | :--- | :--- | :--- | :--- |
| Created | Open | System (automatic) | System | — |
| Open | Acknowledged | acknowledge | Compliance Representative | S-12 |
| Open | Dismissed | dismiss (invalid) | Regulatory Official | S-25 |
| Open | Waived | waive (accepted risk) | Regulatory Official | S-29 |
| Acknowledged | Evidence Submitted | submit evidence | Compliance Representative | S-13 |
| Evidence Submitted | Pending Verification | System (automatic) | System | — |
| Pending Verification | Verified | approve | Regulatory Official | S-14a |
| Pending Verification | Rejected | reject | Regulatory Official | S-14b |
| Rejected | Open | "finding.reopen" (requires comments) | Regulatory Official | S-14c |
| Verified | Closed | System (automatic) | System | — |
| Waived | Closed | System (automatic) | System | — |

**Disposition Values:**

| Disposition | Meaning |
| :--- | :--- |
| `valid` | Finding is legitimate; requires remediation |
| `invalid` | Finding is incorrect; no action needed |
| `waived` | Finding is legitimate but accepted as risk |
| `superseded` | Finding replaced by a newer finding (manual transition via `finding.supersede` capability) |

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

`updated_at` is set to the timestamp of the most recent FSM transition event for this finding. On creation, `updated_at = created_at`.

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
| `finding.supersede` | ✅ | ❌ | ❌ |
| `analytics.view` | ✅ | ✅ | ✅ |
| `conflict.resolve` | ✅ | ❌ | ❌ |

**Segregation of Duties:**
- Directive creator ≠ Finding waiver (same person cannot both create a rule and waive findings from it; enforced on `finding.waive` — see S-29)
- Evidence submitter ≠ Remediation approver (same person cannot both submit evidence and approve it; enforced on `finding.approve_remediation` — see S-14a, S-33)

**Creator Provenance (`authored_by`):**

Segregation of duties requires tracking directive authorship across identity lifecycle operations. The canonical creator identity is stored at `metadata.audit.authored_by` (actor ID) on each rule. At compile time, the engine copies this into per-node snapshot provenance as `creator_provenance` (sorted array of unique actor IDs, excluded from `node_body` hash per §7.1).

**Inheritance rules (normative):**
- On `directive.create`: `metadata.audit.authored_by` MUST be set to the authenticated actor performing the create operation
- On `directive.modify`: `authored_by` is preserved from the parent revision unless explicitly reassigned by an authorized governance process (out of scope for automatic inheritance)
- On `fork`: each child rule inherits `authored_by` from the parent directive being forked
- On `split`: each child rule inherits `authored_by` from the parent directive being split
- On `merge`: the merged rule's `creator_provenance` is the sorted-set union of all parent `authored_by` values (deduplicated). Segregation enforcement applies if the requesting actor appears in ANY parent's authorship set

**Enforcement gates:**
- `finding.waive`: DENY (`403 CapabilityDenied`) if `actor` is present in `creator_provenance` for the directive identified by `finding.control_id` in the active CG-IR snapshot
- `finding.approve_remediation`: DENY if `actor` submitted the evidence for this finding (tracked via Finding Event Stream `DispositionChanged` events with `evidence.submit` actor, not via `authored_by`)

Compile-time validation MUST verify that every active rule has a non-empty `metadata.audit.authored_by` before CG-IR compilation.

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

**Delegation Model:** Not supported in v8.2.2. Capabilities bind directly to authenticated actor identity. AI agents use the same capability matrix with `actor` set to agent ID.

### 3.2.1 Formal Capability Model

The Selma capability model enforces strict segregation of duties and role-based access control:

**Role Definitions:**
| Role | Purpose | Actor Type |
| :--- | :--- | :--- |
| **Regulatory Official** | Rule author and governance owner | Human or AI Agent |
| **Compliance Representative** | Compliance seeker and remediation owner | Human or System |
| **System** | Automated processes and services | Service Account |

**Capability Matrix (Normative):**
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
| `finding.supersede` | ✅ | ❌ | ❌ |
| `analytics.view` | ✅ | ✅ | ✅ |
| `conflict.resolve` | ✅ | ❌ | ❌ |

**Segregation of Duties Constraints (Normative):**
1. **Creator ≠ Waiver:** Actors with `finding.waive` capability MUST NOT waive findings raised by directives they authored
2. **Evidence Submitter ≠ Remediation Approver:** Actors who submitted evidence via `evidence.submit` MUST NOT approve remediation for the same finding via `finding.approve_remediation`

**Creator Provenance Tracking (Normative):**
- `metadata.audit.authored_by` MUST be set to the authenticated actor ID on `directive.create`
- `authored_by` is inherited through fork/merge/split operations
- On merge: `creator_provenance` = sorted-set union of all parent `authored_by` values
- Segregation enforcement uses `creator_provenance` snapshot field (excluded from `node_body` hash)

**Capability Enforcement Algorithm (Normative):**
```
enforce_capability(actor, action, target) → Allow | Deny:
  // Step 1: Check basic capability matrix
  capability := get_capability_for_action(action)
  role := get_role_for_actor(actor)
  
  if capability_matrix[role][capability] == ❌:
    return Deny("Capability not granted to role")
  
  // Step 2: Check segregation of duties
  if action == "finding.waive":
    directive_id := target.finding.control_id
    creator_provenance := get_creator_provenance(directive_id)
    if actor in creator_provenance:
      return Deny("Segregation of duties: creator cannot waive own findings")
  
  if action == "finding.approve_remediation":
    finding_id := target.finding_id
    evidence_submitter := get_evidence_submitter(finding_id)
    if actor == evidence_submitter:
      return Deny("Segregation of duties: evidence submitter cannot approve own remediation")
  
  // Step 3: Allow
  return Allow
```

**Enforcement Points:** Capability checks MUST occur at:
1. Request ingress (API Gateway / Command Handler)
2. Directive mutations (Compilation Engine)
3. Inspection submit (Pipeline entry)
4. Finding FSM transitions (Finding FSM Engine)
5. Conflict resolution (Conflict Resolution Engine)

### 3.3 Execution Fault Taxonomy

| Fault Class | Type | Behavior | Retry |
| :--- | :--- | :--- | :--- |
| **Deterministic Evaluation** | Rule logic fails | Node → `Fail` finding | No |
| **Deterministic Partial** | Partial compliance | Node → `Partial` finding | No |
| **Ambiguous Evaluation** | Cannot determine | Node → `NeedsReview` finding | No |
| **Dependency Failure** | Upstream node failed | Node skipped → `Skipped` trace entry only (no finding) | No |
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
- Two compilations of identical directive graph content, engine version, and frozen environment produce the same snapshot hash (content-addressed determinism)
- If two compilations produce identical CG-IR, the second is a no-op (deduplication)

**Compilation Queue:**
- Multiple compilation requests are serialized through a queue
- Each request includes a request_id for tracking
- Duplicate requests (same Directive Graph version + same frozen_env) are deduplicated

**Deadlock Prevention:**
- Compilation holds **read locks only**; directive modification holds **write locks only** — no lock type inversion (read-then-write on the same request path is prohibited)
- Write lock acquisition uses FIFO queue ordering; a pending write request blocks new read lock grants (writer-preference) to prevent write starvation
- Read locks never wait on other read locks; only write lock acquisition may block
- No circular wait: the dependency graph is strictly `read_lock → (optional) write_lock`, never `write_lock → read_lock` within a single transaction
- Engines MUST NOT hold a write lock while awaiting compilation completion; compilation and modification are separate transactions
- Queue position and lock holder identity MUST be observable for operator diagnostics

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

**Pipeline Stage Descriptions:**

| Stage | Description |
| :--- | :--- |
| `normalize` | Validate target schema, compute `target_hash` |
| `classify` | Determine `target_type`, select evaluation strategy |
| `select_controls` | Filter CG-IR nodes by scope applicability |
| `evaluate` | DAG execution with topological ordering |
| `aggregate` | Collect findings, compute severities per §2.9.1 |
| `report` | Generate inspection snapshot. **All prior stages operate on pre-inspection aggregates; escalation logic fed by this pipeline is inherently delayed by at least one inspection cycle (see §2.11 Aggregation Latency Warning).** |

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

**Metadata Non-Executability Clause (Normative):**
- `metadata` fields and all `x-*` keys MUST NOT influence evaluation outcomes or conflict resolution
- Engines MUST treat all metadata as informational and ignore it during runtime execution
- `metadata` does NOT participate in `semantic_hash` computation and MUST NOT affect CG-IR node hashing
- Validation engines MAY read metadata at compile time for structural validation, but MUST NOT use it for runtime decisions
- This clause extends to all custom namespaces and vendor-specific metadata fields

**Structural Guard (Schema):** `rule_schema.json` applies `patternProperties` to reject keys matching `^(x-exec|x-eval|x-hint|evaluator_|evaluator\\.).*`. This is a compile-time structural filter — semantic non-executability remains an engine invariant regardless of keys present.

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
      "migration_notes": "string (optional)",
      "merge_provenance": {
        "non_surviving_parents": [
          {
            "lineage_id": "string (non-surviving parent lineage_id)",
            "semantic_weight": "primary | secondary | informational (optional)",
            "context": "string (human-readable contribution description, optional)"
          }
        ],
        "merged_at": "datetime (ISO 8601 UTC, optional — strongly RECOMMENDED for audit compliance)",
        "merge_notes": "string (optional)"
      }
    }
  }
}
```

**`merge_provenance` (optional, merge operations):** When a merge assigns `lineage_id := MIN(parent_a, parent_b)`, the non-surviving parent's semantic identity is lost from the primary lineage graph. Authors SHOULD populate `metadata.migration.merge_provenance` on the merged rule to preserve audit context. The `merged_at` timestamp is optional for backward compatibility but strongly RECOMMENDED for audit trail completeness; its omission does not violate any invariant. This field is informational only — it does NOT participate in `semantic_hash` and MUST NOT be read at evaluation runtime. Downstream lineage tracing tools SHOULD consult both `lineage.parent_lineage_ids` and `merge_provenance.non_surviving_parents`.

- Declared namespaces (`audit`, `vendor`, `author`, `migration`, `domain`, `jurisdiction`, `project`) are preferred for all metadata
- Custom top-level keys are permitted for backward compatibility and vendor extensions; validators MAY warn on undeclared keys but MUST NOT reject datasets solely for custom metadata keys within the same MAJOR version
- Unknown keys within a declared namespace MAY be rejected with warning at compile time
- Metadata does NOT participate in `semantic_hash` unless explicitly declared in a future spec version

### 7.2 Anchor Reference Syntax

`anchor_ref` MUST conform to:

```
anchor_ref ::= section_ref | json_pointer

section_ref ::= "section:" section_id ["/" subsection_id]

section_id ::= [a-z][a-z_]*   // any lowercase section identifier (e.g. preamble, domain_appendix)
subsection_id ::= [a-z_]+

json_pointer ::= "/" path_segment ("/" path_segment)*
```

**Examples:**
- `section:directives/specific_directives`
- `section:definitions`
- `/directives/TRAF-001`

Compile-time validation MUST verify `section:` references against policy document structure. Invalid references produce warnings; missing policy sections produce errors.

### 7.3 Parameters Field Behavior

The `parameters` field provides runtime configuration values that are merged into `evaluator_config` at compilation time. This allows the same evaluator logic to be reused with different thresholds, patterns, or field paths without duplicating evaluator definitions.

**Merge algorithm:**
1. Start with a copy of `evaluator_config`
2. For each key in `parameters`, if the key exists in the copy, overwrite it
3. If the key does not exist in the copy, add it
4. The merged result becomes the CG-IR node's `evaluator.config`

**Constraint:** `parameters` MUST NOT contain keys that would change the structural type of the evaluator (e.g., a `parameters.logic` key that conflicts with `evaluator_config.logic`). Compile-time validation rejects such conflicts.

**Example:**
```json
{
  "evaluator_type": "threshold",
  "evaluator_config": {"field": "coverage", "operator": "gte", "threshold": 80},
  "parameters": {"threshold": 95}
}
```
Result after merge: `{"field": "coverage", "operator": "gte", "threshold": 95}`

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
| **Finding Event Immutability** | Append-only; event_hash + HLC ordering ensure integrity |
| **Finding FSM** | Findings follow strict state transitions (see Section 3.1) |
| **Inspection Immutability** | Completed snapshots never modified |
| **Evaluator Purity** | Pure functions: no IO, no randomness |
| **Evaluator Type Safety** | evaluator_config MUST match evaluator_type (schema-enforced if/then) |
| **Evaluator Portability** | RE2-compatible regex only; IEEE 754 strict numerics; UTC-only timestamps; NFC-normalized strings |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver; Evidence submitter ≠ Approver; `authored_by` inherited through lineage ops; enforced at `finding.waive` and `finding.approve_remediation` (§3.2) |
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
| **Evaluator Complexity Bounds** | Depth ≤ 32, total nodes ≤ 256, width ≤ 64, regex ≤ 4096 chars, metadata ≤ 16 384 bytes (16 KiB) (§2.9) |
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
10. Composite recursion depth ≤ 32 (custom compile-time validator required; JSON Schema Draft-07 cannot enforce)
11. Total evaluator nodes per rule ≤ 256 (custom compile-time validator required)
12. Composite width (`sub_evaluators` count) ≤ 64 at any level
13. Regex pattern length ≤ 4096 characters
14. Cross-field discriminator: `evaluator_type` ↔ `evaluator_config` verified by compile-time AST-walking validator (not partial subschema validation alone). The validator MUST implement the algorithm specified in §2.9 Discriminator Validation.
15. **Custom complexity validator:** A standalone compile-time validator MUST walk the evaluator AST to enforce depth, node count, width, and pattern length limits. JSON Schema structural validation alone is insufficient (see §2.9 JSON Schema Draft-07 Enforcement Limitation). Engines that skip this validator are non-conformant.

#### 9.2.6 RE2 Compatibility Validation

Compile-time validation MUST verify all regex patterns against RE2 syntax constraints (§2.9 portability). Validation MUST reject:

| Prohibited Feature | Example Pattern | Rejection Reason |
| :--- | :--- | :--- |
| Backreferences | `(a)\1` | PCRE-only; RE2 incompatible |
| Atomic groups | `(?>a+)` | PCRE-only |
| Lookbehind beyond fixed-width | `(?<=a*)b` | Variable-width lookbehind |
| Possessive quantifiers | `a++` | PCRE-only |

**Canary Test Vectors (normative):** Reference validators MUST pass all vectors below. Failing any vector is a portability violation.

| Vector ID | Pattern | Flags | Input | Expected Match | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RE2-C01 | `^[a-z]+$` | `""` | `"hello"` | `true` | Basic anchor |
| RE2-C02 | `(?i)hello` | `""` | `"HELLO"` | `true` | Inline case flag (RE2) |
| RE2-C03 | `^line$` | `m` | `"a\nline\nb"` | `true` on `"line"` | Multiline `^`/`$` |
| RE2-C04 | `a.b` | `s` | `"a\nb"` | `true` | Dot-all |
| RE2-C05 | `(a\|b)+` | `""` | `"abab"` | `true` | Alternation, linear time |
| RE2-C06 | `(a)\1` | `""` | `"aa"` | **REJECT at compile** | Backreference prohibited |
| RE2-C07 | `(?>a+)` | `""` | `"aaa"` | **REJECT at compile** | Atomic group prohibited |

Implementations SHOULD ship the canary corpus as a standalone test suite runnable against any regex engine binding.

#### 9.2.15 Portable Validator Requirements

JSON Schema structural validation alone is insufficient for cross-runtime determinism. Compile-time validators MUST implement the following portable checks beyond Draft-07 schema validation:

| Check | Requirement | Failure Signal |
| :--- | :--- | :--- |
| **UTC-only timestamps** | All `format: "date-time"` fields MUST match `^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$`. Offsets (`±HH:MM`) MUST be rejected. | `SchemaError: non-UTC timestamp` |
| **Finite numerics** | All `type: "number"` fields MUST be finite (not NaN, not ±Infinity). Validators MUST reject non-finite values at parse time before schema validation. | `SchemaError: non-finite number` |
| **Regex flags whitelist** | `evaluator_config.flags` MUST match `^[ims]*$` (subset of `{i,m,s}` only). | `SchemaError: invalid regex flags` |
| **NFC string normalization** | All string values participating in evaluator comparison SHOULD be NFC-normalized at validation time. | `SchemaError: non-NFC string` (warning) |
| **AST discriminator walk** | `evaluator_type` ↔ `evaluator_config` pairing verified by §2.9 algorithm, not `if`/`then` alone. | `SchemaError: evaluator pairing mismatch` |

Reference implementations SHOULD use strict JSON parsing (reject duplicate keys, reject trailing content) and explicit NaN/Infinity guards before delegating to JSON Schema engines. Ajv `strict: true` mode or equivalent is RECOMMENDED but not sufficient alone — the finite-numeric and UTC checks MUST be implemented as explicit pre-validation passes.

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
5. Runtime engines do not read policy_doctrine.yaml — enforced by: (a) architecture discipline (runtime modules MUST NOT import or load policy_doctrine.yaml); (b) CI static analysis scanning runtime source paths for references to policy_doctrine.yaml (see `scripts/validate_contracts.py`); (c) boot-time assertion (recommended): runtime startup MAY verify policy_doctrine.yaml is absent from configured data paths
6. Conflict resolution at runtime uses spec algorithm over schema/CG-IR fields only
7. `anchor_ref` conforms to §7.2 syntax
8. `metadata` uses declared namespaces only; no executable hints
9. Lineage DAG satisfies §2.2.3 invariants (acyclicity, depth ≤ 64)
10. Merge operations produce lineage_id per §2.2.2 deterministic algorithm

### 9.8 Schema Annotation Status

All `x-*` keys in `rule_schema.json` are **informative and non-normative**. They document cross-layer bindings for human maintainers. On conflict between an `x-*` annotation and this specification, **this specification wins**.

### 9.9 Architectural Audit Validation

Certain §8 invariants require architectural review beyond mechanical JSON/schema validation. The following gates MUST be satisfied before a reference implementation is certified against this specification:

| Gate ID | Invariant | Validation Method | Stories |
| :--- | :--- | :--- | :--- |
| AA-01 | **Mediated Feedback** | Verify analytics engine has no write path to CG-IR or Finding FSM; integration test proving finding events cannot trigger compilation | S-17, S-18 |
| AA-02 | **Declarative Governance** | Static analysis confirming runtime modules load only schema/CG-IR fields; policy_doctrine.yaml absent from runtime data paths | S-05, all |
| AA-03 | **Evaluator Purity** | AST analysis or sandboxed execution proving evaluators perform no IO, no randomness, no environment reads | S-10, S-21 |
| AA-04 | **Segregation of Duties** | Integration test: `finding.waive` denied when actor ∈ `creator_provenance`; `finding.approve_remediation` denied when actor submitted evidence | S-14a, S-29 |
| AA-05 | **Conflict Resolution Determinism** | Replay test: identical CG-IR snapshot + identical target → byte-identical conflict outcomes including compatible_overrides pairs | S-05, S-28 |
| AA-06 | **Discriminator Completeness** | Corpus of invalid `evaluator_type`/`evaluator_config` pairings MUST be rejected by reference validator (§2.9, §9.2.15) | S-21, S-27 |
| AA-07 | **Portable Serialization** | RE2 canary vectors (§9.2.6) + UTC/NaN rejection tests pass on reference validator | S-21 |

Architectural audit gates are non-blocking for spec conformance of the document suite itself but MUST be satisfied for production-grade reference implementation certification.

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
| 8.2.2 | 2026-07-05 | Deep audit corrections: created_at in node_body (13 fields), conflict detection (§2.15.1), scope schema (§2.8.2), rule-to-CG-IR mapping (§2.8.1), compile-time-only fields (§2.8.4), deontic semantics (§2.8.3), outcome-to-finding mapping (§2.9.1), defer_to resolution, skipped nodes, finding_aggregates pre-computation, reinspection semantics, frozen env schema, incremental compilation, pipeline stages, FSM story binding (S-25, S-29), flexible standards encoding; P0/P1/P2 fixes: hash_algorithm_version 2, metadata backward compatibility, CG-IR-only specificity (removed rule.target), merge ID timestamp + 16 hex chars, conflicts_with/parameters clarified, findings_by_directive_id naming, frozen_env_hash self-reference, confidence threshold in frozen env, anchor_ref relaxed, FindingCreated event payload, evaluator complexity specificity rationale; cross-document audit: HLC in Finding Event Immutability (§8), delegation model v8.2.2 alignment, explicit S-29/S-14 segregation binding in §3.2 |
| 8.2.2-auditfix | 2026-07-05 | Audit report fixes: schema Draft-07 compliance (dependentRequired→dependencies, $defs→definitions), deontic_type added to CG-IR node and semantic_body, scope object added to rule schema, per-rule metadata and directive_revision/control_version fields added, regex flags pattern restriction, composite evaluator width/not constraints, lineage parent cardinality enforcement, retry policy clarified (deterministic vs timeout), User_Stories S-03 Retired→deprecated, event_hash composition defined, finding.supersede capability added, superseded disposition added, snapshot hash determinism clarified, matches operator semantics defined, README deduplicated |
| 8.2.3 | 2026-07-05 | Formal verification audit findings: normative `defer_to` active-lineage resolution algorithm with post-fork Conflict Artifact escalation (§2.15), `authored_by` creator provenance inheritance through fork/merge/split with `creator_provenance` snapshot field (§3.2, §2.8.1), cross-lineage presentation correlation guidance (§2.13.1), NeedsReview+Fail operational guidance (§2.15.1), Policy Runtime Prohibition CI enforcement mechanism (§9.7), User_Stories capability matrix segregation column |
| 8.2.3-b | 2026-07-05 | Formal verification audit deltas: normative AST-walking discriminator validation algorithm superseding JSON Schema if/then (§2.9), optional `metadata.migration.merge_provenance` for merge lineage preservation (§7.1), aggregation latency warning in §2.11 and §3.7, MERGE-NN namespace documented as v9.0.0 candidate (§2.2.2) |
| 8.2.3-c | 2026-07-05 | Formal verification audit remediation: `compatible_overrides()` for symmetric override pairs (§2.15 D-01/F-02), `defer_to` missing-target fall-through reconciliation (§2.15 D-02/F-03), DFS `defer_to` cycle detection (§2.15 D-07/F-08), cross-lineage advisory resolution algorithm (§2.15.2 D-10/F-07), compilation deadlock prevention (§3.4 D-12/F-15), RE2 canary test vectors (§9.2.6 D-13/F-12), portable validator requirements for UTC/NaN/flags (§9.2.15 D-11/F-04–F-06), architectural audit validation gates (§9.9 D-09/F-16), `merge_provenance` normative documentation (§7.1 D-05) |
| 8.2.4 | 2026-07-05 | Formal verification audit (v2) delta items: JSON Schema Draft-07 enforcement limitation documented with custom compile-time validator requirement (§2.9 F-001/Δ-001–Δ-002), `depends_on` execution ID semantics clarified (§2.8, §2.8.1 F-002/Δ-003), metadata size standardized to 16 384 bytes (§2.9, §8 F-005/Δ-005), merge provenance loss risk documented (§2.2.2 F-004/Δ-004), §8 System Invariants completeness verified (F-003/Δ-007) |
| 8.2.4-d | 2026-07-05 | Formal verification audit (v8.2.2 corpus) remediation: audit corpus requirement (F-001), `x-finding-fsm` annotation (F-003), `x-discriminator-note` for evaluator_type safety (F-004), metadata `patternProperties` structural guard (F-005), `x-portability-note` compile-time engine invariants (F-006), `policy_contract_version` cross-file check documentation (F-010), worked algorithm examples in User_Stories.md, version sync to 8.2.4 |
| 8.2.4-e | 2026-07-05 | Formal verification audit (v8.2.4 production-readiness) clarifications: active lineage definition for `defer_to` resolution after multi-fork (§2.15 D-01/F-002), `matches` operator RE2 cross-reference to §2.9 portability (§2.16.1 D-02/F-004), `merged_at` strongly RECOMMENDED guidance (§2.2.2, §7.1 D-04/F-001), S-30 explicit AA-01–AA-07 gate-ID traceability (User_Stories.md D-03/F-005) |
