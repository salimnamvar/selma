# Contracts Directory

Three-layer architecture for universal rule governance. Spec is normative; schema and policy conform.

## Architecture

```
+-------------------------------+         +-------------------------------+         +-------------------------------+
|    policy_doctrine.yaml       |         |     rule_schema.json          |         |     SPECIFICATION.md          |
|  (Governance Intent)          |         |  (Structural Projection)      |         |  (Normative Source)           |
|                               |         |                               |         |                               |
|  - Writing Principles         |         |  - Data Structure             |         |  - System Behavior            |
|  - Document Sections          |         |  - Lifecycle States           |         |  - Invariants                 |
|  - Governance & Amendment     |<------->|  - Dependencies               |<------->|  - Contracts                  |
|  - Sanctions & Remedies       |  Label  |  - Evaluator Routing          |  Derive  |  - Algorithms                 |
|  - Directive Tables           |  Only   |  - Parameters & Conditions    |  From    |  - Execution Semantics        |
|  - Priority Hierarchy (intent)|         |  - Complexity Limits          |         |  - Conflict Resolution (norm) |
|                               |         |  - Priority Reference         |         |  - DAG Execution              |
|  FORBIDDEN: parameters,       |         |  FORBIDDEN: preamble,         |         |  FORBIDDEN: prose governance  |
|  conditions, evaluator_hint,  |         |  governance, definitions,     |         |  (behavioral only)            |
|  weight, depends_on, etc.     |         |  principles, sanctions, etc.  |         |                               |
+-------------------------------+         +-------------------------------+         +-------------------------------+
```

## The Layered Authority Model

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

### Architectural Risks & System Deficiencies

While the system design exhibits strong mathematical rigor, a deep audit highlights several subtle edge cases, semantic vulnerabilities, and structural risks that require careful monitoring:

#### 1. The Lossy Metadata Nature of Lexicographic Merges

The merge protocol dictating that `lineage_id := MIN(parent_a, parent_b)` provides strict mathematical determinism, but introduces **semantic provenance loss**.

**The Risk:** Merging `PAY-800` (Payments Regulation) and `AUTH-001` (Identity Verification) permanently forces `AUTH-001` as the active lineage root. Over multiple system iterations, the structural provenance of the payment rule chain vanishes from direct lineage tracking, surviving only within the metadata array. If a future major shift splits the rule again, tracing its lineage back to payments requires heavy manual traversal of ancestral metadata strings.

**Mitigation:** Downstream metadata parsing for lineage tracing; consider introducing a dedicated `MGR-NN` merge namespace to explicitly track unified rule heritage.

#### 2. Time Realism Shift in `finding_aggregates`

The pre-computation constraint on `finding_aggregates` ensures that the `Context` object remains perfectly read-only, avoiding shared mutable state race conditions during topological DAG execution.

**The Risk:** Because aggregates are compiled strictly from *past* historical finding event streams before the active evaluation begins, they do not incorporate findings generated during the current inspection cycle. If a series of interdependent rules within the same execution path count cumulative failures to escalate a severity level, the pipeline cannot track them in real-time. This structural isolation forces a multi-pass inspection loop or delays escalation alerts until a subsequent reinspection occurs.

**Mitigation:** Multi-pass inspection loop or delayed escalation alerts until reinspection.

#### 3. Discriminator Under-Validation Risk

The specification highlights that `evaluator_type` ↔ `evaluator_config` consistency is a core semantic invariant, warning that standard JSON Schema subschema engines often fail to validate these strict pairings comprehensively.

**The Risk:** If a development team relies solely on automated schema validators at ingress points without implementing custom compile-time conditional checks, malformed pairings (e.g., an `evaluator_type` set to `regex` passing an object containing a threshold structure) could bypass edge filtering and cause runtime exceptions inside the pure evaluation functions.

**Mitigation:** Enforce dependent-schema validation at compile time; never rely solely on `if`/`then`.

#### 4. Cascade Invisibility via Skipped Dependency Semantics

To eliminate false-positive storms, nodes whose upstream dependencies fail are silently bypassed, appending a `Skipped` status marker to the pipeline trace instead of generating a separate validation finding.

**The Risk:** While this keeps error logs clean, it can obscure systemic non-compliance. If a foundational control node fails, dozens of fine-grained downstream checks will quietly deactivate without recording explicit findings. A compliance representative reviewing *only* open findings could easily overlook massive swathes of unverified infrastructure because the system treats them as invisible pipeline trace entries rather than actionable validation gaps.

**Mitigation:** Pipeline trace entries record skipped nodes; dashboard views should surface `skipped_nodes` alongside findings.

**Binding Rules:**
1. SPECIFICATION.md is the single normative source for all system behavior
2. rule_schema.json MUST be derivable from spec invariants — no schema element may contradict spec
3. policy_doctrine.yaml describes governance intent only — no executable fields
4. When spec and schema conflict, spec wins
5. Version synchronization is a compatibility matrix: MAJOR MUST match; MINOR/PATCH MAY differ
6. All `x-*` keys in rule_schema.json are informative and non-normative
7. The engine validates schema against spec invariants at compile time
8. **Policy runtime prohibition:** policy_doctrine.yaml MUST NOT be read during inspection, evaluation, finding FSM transitions, or conflict resolution at runtime

## The Separation Principle

**SPECIFICATION.md** defines *how the system behaves*:
- Algorithms, invariants, execution semantics, conflict resolution
- The normative source — all other layers conform to it

**Policy Contract** defines *why and how humans write rules*:
- Prose structure, editorial standards, governance processes, social consequences
- A diplomat can edit this without knowing what a "regex" is
- **Never read at runtime** — influences execution only indirectly through human authoring

**Rule Contract** defines *what the machine executes*:
- Data structure, lifecycle, dependencies, evaluator routing hints
- A kernel developer can extend this without caring about the "Governance" section
- Derived from spec invariants — structural projection, not standalone algorithm

## The Traceability Bond

The contracts connect in exactly **one** way:

- **Policy → Rule**: Directive tables contain a `Machine ID` column (cross-reference label)
- **Rule → Policy**: Each rule has an `anchor_ref` field (link back to policy document section)

This forms a strict bidirectional pointer:
- Policy says: *"This paragraph is about Rule `R-001`."*
- Rule says: *"Rule `R-001` points back to `section:directives/specific_directives`."*

**Anchor Reference Syntax (§7.2):** `section:<id>[/<subsection>]` or JSON Pointer per [RFC 6901](https://tools.ietf.org/html/rfc6901) (`/path/to/section`).

## Policy Runtime Prohibition

**Policy MUST NOT be read at runtime.** This prohibition is stated in each document for self-contained clarity:

- **policy_doctrine.yaml**: `cross_layer_binding.runtime_prohibition` and `contamination_guard.note`
- **rule_schema.json**: `x-cross-layer-binding.policy_runtime_prohibition`
- **SPECIFICATION.md**: §2.15 conflict resolution, §2.2 identity resolution, and cross-layer binding sections

The compilation engine implements all runtime behavior over schema/CG-IR fields only. Policy prose is authoritative for human authoring but never interpreted by the engine.

## Contamination Guards

Each contract explicitly lists what it MUST NOT contain:

### Policy Contract Forbidden Fields
`parameters`, `conditions`, `evaluator_hint`, `evaluator_type`, `evaluator_config`, `weight`, `depends_on`, `conflicts_with`, `status`, `created_at`, `expires_at`, `remediation`, `target`, `lineage`

### Rule Contract Forbidden Root Fields
`preamble`, `governance`, `definitions`, `principles`, `sanctions`, `references`, `writing_principles`, `sections`, `guidance`, `columns`

## Version Synchronization

Both contracts reference each other's version:
- `policy_doctrine.yaml` → `doctrine.rule_contract_version` + `doctrine.rule_contract_id`
- `rule_schema.json` → `policy_contract_version` + `policy_contract_id`

Update both when either contract changes.

## Compatibility Matrix

All three documents share the same MAJOR version. MINOR and PATCH may differ independently:

| Policy (MAJOR.minor.patch) | Schema (MAJOR.minor.patch) | Spec (MAJOR.minor.patch) | Compatible? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| 8.x.x | 8.x.x | 8.x.x | ✅ | Same MAJOR family — all combinations valid |
| 8.2.2 | 8.4.2 | 8.3.0 | ✅ | MINOR/PATCH may differ within MAJOR |
| 8.x.x | 9.x.x | 8.x.x | ❌ | MAJOR mismatch — incompatible |
| 9.0.0 | 8.x.x | 8.x.x | ❌ | MAJOR mismatch — incompatible |

**Formal rule:** `dataset(schema_version=S) accepts policy(policy_version=P) ⟺ ⌊S⌋ == ⌊P⌋`

## Conflict Resolution Mapping

### Priority Hierarchy

Rules exist at different authority levels. When two rules conflict, the higher-priority rule wins:

1. **Constitutional** - Core principles that cannot be overridden
2. **Statutory** - Rules enacted by authorized governing bodies
3. **Regulatory** - Rules created by agencies to implement statutory requirements
4. **Operational** - Day-to-day procedures implementing higher-level rules
5. **Advisory** - Recommendations that are not mandatory

### The Deterministic Precedence Chain

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

### Specificity Score Algorithm (Normative)

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

`count_bound_fields` recursively counts required evaluator config fields. Composite evaluators sum child scores. Evaluator complexity contributes to specificity because a rule with more evaluation constraints is more narrowly targeted. Two engines implementing this algorithm MUST produce identical scores for identical CG-IR node bodies. The algorithm operates exclusively on CG-IR node fields.

### Priority Level Mapping (Internal Integer)

| Schema `priority` enum | `priority_level` integer |
| :--- | :--- |
| `constitutional` | 1 |
| `statutory` | 2 |
| `regulatory` | 3 |
| `operational` | 4 |
| `advisory` | 5 |

Enum values are presentation; all comparisons use `priority_level` integers.

### Temporal Binding Guarantee

The `created_at` field used in conflict resolution is the directive's authoring timestamp, frozen into `node_body` at compilation time. It is a static property of the CG-IR node — NOT evaluation time, NOT wall clock time. For a given CG-IR snapshot, conflict resolution outcomes are fully deterministic because all inputs (`priority`, `conflict_resolution`, `created_at`, `scope` for specificity) are frozen in the immutable snapshot.

**Conflict Resolution Precedence Chain:** Explicit override (schema `conflict_resolution` field) → priority → specificity → recency → Conflict Artifact. Described in three places (schema, cross-layer binding, policy intent). All MUST remain synchronized. SPECIFICATION.md §2.15 is normative.

**Identity Pattern Relationship:**
- Lineage ID: `^[A-Z][A-Z0-9]+-[0-9]+$` (e.g., `TRAF-001`)
- Execution ID: `^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$` (e.g., `TRAF-001-A`)
- Execution ID extends lineage_id by appending `-SUFFIX` segments. On first creation, execution_id equals lineage_id (zero suffixes). After fork/merge/split, suffixes are appended.

## Versioning Strategy

Both contracts follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR** - Breaking changes requiring migration
- **MINOR** - New backward-compatible features
- **PATCH** - Bug fixes and clarifications

## Migration Rules

Cross-version migration follows these invariants:

1. **Lineage preservation:** `lineage_id` is preserved across MAJOR versions by default (`identity_preserved`). Machine IDs retain their audit trail.
2. **Additive changes:** New schema fields in a MAJOR version MUST have defaults so existing datasets remain valid without modification.
3. **Breaking changes:** Field removals or renames require a migration descriptor in `metadata.migration` documenting the transformation, with `migration_required: true`.
4. **Cross-version validation:** The compilation engine MUST validate that all `lineage_id` references resolve within the migrated dataset.
5. **Audit replay:** Old `hash_algorithm_version` values remain valid for audit replay of historical compilations.

**Migration descriptor fields:** `upgrade_from`, `upgrade_to`, `migration_required`, `lineage_preservation` (identity_preserved | identity_reassigned | requires_remap).

## Composite Evaluator Recursion

The schema supports recursive composite evaluators (`sub_evaluators` → `evaluator_config_entry` → `composite` → `sub_evaluators`). Compile-time limits (§2.9):

| Limit | Value |
| :--- | :--- |
| Max recursion depth | 32 |
| Max total evaluator nodes | 256 |
| Max composite width | 64 |
| Max regex pattern length | 4096 chars |

Evaluators MUST use iterative (not naive recursive) evaluation to avoid stack exhaustion.

## Deterministic Serialization

Canonical form for hashing:
- JSON keys sorted lexicographically
- **Ordered arrays** (preserve insertion order): `sub_evaluators`, `pipeline_trace`, `skipped_nodes`
- **Unordered arrays** (sorted lexicographically before hash): `depends_on`, `conflicts_with`, `parent_lineage_ids`, `parent_execution_ids`
- Schema `$ref` resolved at validation time only; excluded from canonical form
- Default values NOT injected — only explicit values participate in hashing
- NaN/Infinity prohibited
- Dual hash model: `semantic_hash` (evaluator/scope) + `presentation_hash` (description) compose `node_hash`

### Split-Decomposition Hashing

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

### Array Ordering Classification

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

## Metadata Namespacing

Root `metadata` is informational only. Declared namespaces: `audit`, `vendor`, `author`, `migration`, `domain`, `jurisdiction`, `project`. Custom top-level keys permitted for backward compatibility; validators MAY warn on undeclared keys. No executable hints permitted (§7.1).

## Merge Semantics

Merged `lineage_id` = lexicographic minimum of parent lineage_ids. New execution_id generated deterministically per §2.2.2.

```
merge(parent_a, parent_b) → merged_rule:
1. lineage_id := MIN(parent_a.lineage_id, parent_b.lineage_id) lexicographically
2. id := lineage_id + "-M" + SHA-256(canonical_json({sorted(parent_lineage_ids), sorted(parent_execution_ids), operation: "merge", timestamp}))[0:16].uppercase()
3. lineage.parent_lineage_ids := sorted unique([parent_a.lineage_id, parent_b.lineage_id])
4. lineage.parent_execution_ids := sorted unique([parent_a.id, parent_b.id])
5. Both parent rules transition to status=deprecated
```

**Invariant:** The merged `lineage_id` equals the lexicographically minimum parent `lineage_id`. The non-surviving parent `lineage_id` remains in audit history via `lineage.parent_lineage_ids` but is never reused as an active root.

## Evaluation Portability & Complexity Guardrails

The evaluation layer enforces pure, mathematical isolation. Evaluators operate with zero side effects, zero I/O, and zero runtime randomness.

### Cross-Runtime Portability Rules

To prevent execution drift when evaluating rules across disparate CPU architectures or runtimes, the system mandates strict computational portability:

| Constraint | Rule | Rationale |
| :--- | :--- | :--- |
| **Regex Dialect** | Restricted entirely to **RE2-compatible syntax**. Advanced PCRE components (backreferences, lookaheads beyond lookahead/lookbehind, atomic groups) are PROHIBITED. Flags limited to: `i` (case-insensitive), `m` (multiline), `s` (dot-all). | RE2 guarantees linear-time matching and consistent behavior across implementations (Go, C++, Java, Python via `google-re2`). PCRE features create cross-runtime divergence. |
| **Strict Numerics** | All numeric comparisons use **IEEE 754 double-precision arithmetic**. NaN and Infinity are NOT permitted in evaluator configs or target values (schema rejects). Float comparison uses exact IEEE 754 bitwise equality — no epsilon tolerance unless explicitly configured. | Prevents silent divergence across CPU architectures and language runtimes. |
| **Time & Strings** | All timestamp comparisons in evaluators use **UTC (ISO 8601)**. Timezone-aware conversions are NOT permitted within evaluator logic. Target `submitted_at` and context `last_inspection_date` are always UTC-normalized before evaluator invocation. String equality and ordering use Unicode codepoint comparison (NFC-normalized). No locale-dependent collation. | Eliminates DST/timezone ambiguity; prevents locale-sensitive ordering divergence. |

### System Complexity Limits

The compiler prevents execution engine stack exhaustion by tracking structural bounds:

| Complexity Metric | Absolute Limit | Compilation Failure Signal |
| :--- | :--- | :--- |
| **Max Composite Recursion Depth** | 32 levels | `SchemaError: evaluator depth exceeded` |
| **Max Total Evaluator Nodes / Rule** | 256 nodes | `SchemaError: evaluator count exceeded` |
| **Max Composite Width (`sub_evaluators`)** | 64 nodes | `SchemaError: evaluator width exceeded` |
| **Max Regex Pattern Length** | 4,096 chars | `SchemaError: pattern too long` |
| **Max Ancestry Lineage DAG Depth** | 64 steps | Compile-time lineage cycle/depth rejection |
| **Max Metadata Serialized Size** | 16 KiB per rule | `SchemaError: metadata too large` |

### Evaluator Portability Constraints

| Constraint | Rule |
| :--- | :--- |
| **Purity** | No side effects. No network calls. No file I/O. No randomness. |
| **Determinism** | Same inputs → same outputs, always. |
| **Allowed operations** | String matching, regex, arithmetic, field extraction, comparison |
| **Prohibited operations** | HTTP calls, DB queries, file reads, environment variables |
| **Type Safety** | `evaluator_config` MUST match `evaluator_type` (schema if/then). Cross-field consistency is a semantic invariant. |

## Compilation Pipeline

The end-to-end lifecycle from policy authoring to runtime execution:

```
Policy Authoring (human writes policy_doctrine.yaml)
        │
        ▼
Policy Validation (compile-time: contamination guard, no executable fields)
        │
        ▼
Schema Validation (JSON Schema Draft-07: structure, types, constraints)
        │
        ▼
Cross-Layer Validation (schema derivable from spec; cross-field evaluator_type ↔ evaluator_config)
        │
        ▼
Identity Validation (lineage_id uniqueness, pattern compliance, DAG integrity)
        │
        ▼
Conflict Graph Construction (override → priority → specificity → recency)
        │
        ▼
CG-IR Generation (directives → nodes with dual identity)
        │
        ▼
Semantic Hash Generation (node_hash, edge_hash, snapshot_hash per §2.6)
        │
        ▼
Snapshot Manifest (deterministic serialization, sorted keys, UTF-8)
        │
        ▼
Runtime Bundle (engine reads schema/CG-IR fields only)
```

Each stage performs a specific class of validation. The engine is the sole executor; policy is never interpreted at any stage after Policy Validation.

### Pipeline Stage Descriptions

| Stage | Description |
| :--- | :--- |
| `normalize` | Validate target schema, compute `target_hash` |
| `classify` | Determine `target_type`, select evaluation strategy |
| `select_controls` | Filter CG-IR nodes by scope applicability |
| `evaluate` | DAG execution with topological ordering |
| `aggregate` | Collect findings, compute severities per §2.9.1 |
| `report` | Generate inspection snapshot |

### Incremental Compilation Algorithm

1. Compute the set of changed `lineage_id` values by comparing current vs. previous directive graph
2. For each changed `lineage_id`, mark its node and all transitive dependents as dirty
3. Recompute dirty nodes
4. Reuse unchanged `node_hash` values from the previous snapshot
5. Recompute edge hashes for any dirty node's edges
6. Recompute snapshot hash

**Incremental Reuse Guarantee:** If `node_body` is byte-identical across compilations, `node_hash` is identical regardless of which snapshot references it. Conflict resolution metadata (`priority`, `conflict_resolution`) is part of `node_body` — not lost by local hashing. Graph context (which nodes depend on which) is captured in edge hashes and the snapshot manifest only.

## Hash Algorithm Versioning

Hash algorithms may change over time (e.g. SHA-256 → BLAKE3). The `hash_algorithm_version` field in `x-deterministic-serialization` tracks the current algorithm version:

- **Version 1**: Flat `node_body` hash (deprecated 8.2.0)
- **Version 2**: Dual-hash model (`semantic_hash` + `presentation_hash`, current)
- All `node_hash`, `edge_hash`, and `snapshot_hash` values are tagged with the algorithm version
- Old versions remain valid for audit replay; new compilations MUST use the current version
- Algorithm migration requires a MAJOR version bump

## CG-IR Snapshot Hash Composition

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

### Frozen Environment Schema (§2.7)

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

`frozen_env_hash` = SHA-256(canonical_json(above minus `frozen_env_hash` itself)). The `frozen_env_hash` key is excluded from its own computation.

## Edge Hash Formula

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

## Version Resolution Function

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

See [SPECIFICATION.md](SPECIFICATION.md) for the full universal rule governance specification.
