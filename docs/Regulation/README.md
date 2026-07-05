# Contracts Directory

Three-layer architecture for universal rule governance. Spec is normative; schema and policy conform.

## Audit Corpus

Formal verification audits MUST include the complete five-document corpus below. Omitting `SPECIFICATION.md` renders approximately 60% of normative algorithm claims (specificity_score, merge formula, CG-IR hash composition, HLC ordering, Finding FSM) unverifiable from projections alone.

| Document | Role | Version (current) |
| :--- | :--- | :--- |
| [SPECIFICATION.md](SPECIFICATION.md) | Normative behavioral source | 8.2.4 |
| [rule_schema.json](rule_schema.json) | Structural JSON Schema projection | 8.2.4 |
| [policy_doctrine.yaml](policy_doctrine.yaml) | Governance intent (authoring only) | 8.2.4 |
| [User_Stories.md](../User-Story/User_Stories.md) | Behavioral contract | 8.2.4 |
| README.md (this file) | Cross-layer binding and compatibility matrix | — |

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

### Architectural Risks & Mitigations

Four known edge cases require monitoring during implementation. See `docs/User-Story/User_Stories.md` (Executive Architectural Overview → Architectural Risks & Mitigations) for detailed risk analysis.

| Risk | Summary | Mitigation |
| :--- | :--- | :--- |
| **Lossy Lexicographic Merges** | `lineage_id := MIN(parent_a, parent_b)` is deterministic but may obscure provenance | Metadata parsing for lineage tracing; future `MERGE-NN` namespace (e.g. `MGR-18`) in v9.0.0 |
| **Time Realism in `finding_aggregates`** | Pre-computed aggregates exclude current-inspection findings | Multi-pass inspection or delayed escalation until reinspection |
| **Discriminator Under-Validation** | `evaluator_type` ↔ `evaluator_config` consistency requires custom compile-time checks beyond standard JSON Schema subschema engines | Enforce formal AST-walking discriminator validation (§2.9) at compile time; ship canonical reference validator + invalid-pairing test corpus (§9.2.15, S-30, S-31) |
| **Cascade Invisibility via Skipped Nodes** | Dependency failures bypass downstream checks without findings | Surface `skipped_nodes` in pipeline trace and dashboards |

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

**Mechanical enforcement:** CI runs `scripts/validate_contracts.py` to scan runtime source paths (`src/`) for references to `policy_doctrine.yaml`. Runtime startup MAY additionally assert the doctrine file is absent from configured data paths (SPECIFICATION.md §9.7 item 5).

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

**Precedence Chain:** Explicit override (schema `conflict_resolution` field) → `compatible_overrides()` for symmetric pairs (`{always_wins, never_wins}`, identical `defer_to` targets) → priority → specificity → recency → Conflict Artifact. Missing or ambiguous `defer_to` targets fall through to computed resolution (not Conflict Artifact). Cross-lineage pairs produce advisory Conflict Artifacts only (§2.15.2). All inputs are frozen in the CG-IR snapshot, making outcomes deterministic per snapshot.

**Precedence Clarifier:** Policy prose describes governance *intent* for human authors. Schema `conflict_resolution` is structural override *data*. SPECIFICATION.md §2.15 is the sole *algorithm*. On any conflict between the three layers, spec wins; policy is never read at runtime.

| Schema `priority` enum | `priority_level` integer |
| :--- | :--- |
| `constitutional` | 1 |
| `statutory` | 2 |
| `regulatory` | 3 |
| `operational` | 4 |
| `advisory` | 5 |

Enum values are presentation; all comparisons use `priority_level` integers.

See SPECIFICATION.md §2.15 for the normative `specificity_score` algorithm and `resolve_conflict` function (including `compatible_overrides()`, DFS `defer_to` cycle detection, and §2.15.2 cross-lineage advisory resolution).

## Reference Validator

Production-grade implementations SHOULD ship a canonical reference validator satisfying §9.2.15 portable checks (UTC-only timestamps, finite numerics, regex flags whitelist, AST discriminator walk) and §9.2.6 RE2 canary test vectors. User stories S-30 (architectural audit gates) and S-31 (reference validator) define the behavioral contract.

## Compile-Time Engine Invariants

JSON Schema Draft-07 structural validation is **necessary but insufficient** for full contract conformance. The following semantic invariants MUST be enforced by the compilation engine (reference validator) at compile time — they cannot be expressed structurally in JSON Schema alone:

| Invariant | Schema Coverage | Engine Responsibility |
| :--- | :--- | :--- |
| **Evaluator portability** | Regex flags whitelist (`^[ims]*$`) | RE2 linter pass; reject PCRE features (backreferences, lookaheads). NFC string normalization. IEEE 754 finite numerics (reject NaN/±Infinity). |
| **UTC timestamps** | `utc_datetime` pattern (`…Z$`) | Normalize all timestamps to UTC before hashing; reject `±HH:MM` offsets. |
| **Evaluator type safety** | `oneOf` + `additionalProperties: false` (primary); `allOf` `not:{required:[…]}` (weak secondary) | AST-walking discriminator validator per §2.9 — mandatory normative gate. |
| **Evaluator complexity** | Per-level `maxItems` only | Recursive AST walk: depth ≤ 32, total nodes ≤ 256, width ≤ 64. |
| **Metadata non-executability** | `patternProperties` rejects `x-exec*`, `x-eval*`, `x-hint*`, `evaluator_*` keys | Engine MUST ignore metadata at evaluation runtime regardless of content. |
| **Policy version consistency** | `policy_contract_version` field required | Engine MUST verify `major(policy_contract_version) == major(policy.version)`. |
| **Finding FSM** | `x-finding-fsm` informative annotation only | Finding FSM Engine enforces transitions per SPECIFICATION.md §3.1 at runtime. |



## Migration Rules

Cross-version migration follows the invariants defined in SPECIFICATION.md §2.2.4 and §5. Key points: `lineage_id` is preserved across MAJOR versions by default; field removals require a migration descriptor (`metadata.migration`).

## Composite Evaluator Recursion

The schema supports recursive composite evaluators. See SPECIFICATION.md §2.9 for compile-time complexity limits (depth ≤ 32, nodes ≤ 256, width ≤ 64, pattern length ≤ 4096, metadata ≤ 16 384 bytes). **Critical:** JSON Schema Draft-07 cannot natively enforce recursive depth or aggregate node count limits. Custom compile-time validators MUST walk the evaluator AST to enforce these limits (§2.9 JSON Schema Draft-07 Enforcement Limitation).

## Deterministic Serialization & Hashing

See SPECIFICATION.md §2.6, §2.16 for the normative hash formulas and §2.16.1 for the array ordering classification table.

Key points:
- **Dual hash model:** `semantic_hash` (evaluator/scope/priority/status/depends_on/created_at/deontic_type) + `presentation_hash` (description, directive_revision, control_version) compose `node_hash`
- **Edge hash:** Directional `{source: directive_id, target: directive_id}` — independent of node content
- **Snapshot hash:** SHA-256 of sorted `node_hashes[]` + sorted `edge_hashes[]` + provenance (compiled_at excluded)
- **Ordered arrays:** `sub_evaluators`, `pipeline_trace`, `skipped_nodes`
- **Unordered arrays (sorted before hash):** `depends_on`, `conflicts_with`, `parent_lineage_ids`, `parent_execution_ids`

## Evaluation Portability & Complexity Guardrails

The evaluation layer enforces pure, mathematical isolation. See SPECIFICATION.md §2.9 for the full evaluator contract and portability constraints.

### System Complexity Limits (Quick Reference)

| Complexity Metric | Limit | Failure Signal |
| :--- | :--- | :--- |
| Max composite recursion depth | 32 levels | `SchemaError: evaluator depth exceeded` |
| Max evaluator nodes per rule | 256 nodes | `SchemaError: evaluator count exceeded` |
| Max composite width | 64 nodes | `SchemaError: evaluator width exceeded` |
| Max regex pattern length | 4,096 chars | `SchemaError: pattern too long` |
| Max ancestry depth | 64 steps | Compile-time lineage rejection |
| Max metadata per rule | 16 384 bytes (16 KiB) | `SchemaError: metadata too large` |

## Compilation Pipeline

The end-to-end lifecycle from policy authoring to runtime execution. See SPECIFICATION.md §2.4 for the canonical pipeline. Key stages:
`normalize` → `classify` → `select_controls` → `evaluate` → `aggregate` → `report`

Each stage performs a specific class of validation. The engine is the sole executor; policy is never interpreted at any stage after Policy Validation.

See [SPECIFICATION.md](SPECIFICATION.md) for the full universal rule governance specification.
