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

See SPECIFICATION.md §1.2 for the normative three-layer hierarchy.

**Summary:** Spec > Schema > Policy. Policy has zero runtime authority.

### The Policy Runtime Prohibition

See SPECIFICATION.md §1.2 (normative) and `policy_doctrine.yaml` `cross_layer_binding.runtime_prohibition`.

**Mechanical enforcement:** CI runs `scripts/validate_contracts.py` to scan runtime source paths (`src/`) for references to `policy_doctrine.yaml`. Runtime startup MAY additionally assert the doctrine file is absent from configured data paths (SPECIFICATION.md §9.7 item 5).

### Version Synchronization Invariant

See SPECIFICATION.md §5 for the normative version compatibility matrix and formal compatibility rule.

**Summary:** MAJOR MUST match; MINOR/PATCH MAY differ. Formal rule: `dataset(S) accepts policy(P) ⟺ ⌊S⌋ == ⌊P⌋`.

### Architectural Risks & Mitigations

See SPECIFICATION.md §2.2.2 (merge provenance loss), §2.11 (finding_aggregates latency), §2.9 (discriminator under-validation), and §2.12 (skipped nodes cascade) for the normative risk analysis and mitigations.

### Binding Rules

See SPECIFICATION.md §1.2 for the normative binding rules. All `x-*` keys in rule_schema.json are informative and non-normative (see `x-normative-status` annotation).

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

## Contamination Guards

See `policy_doctrine.yaml` `contamination_guard.prohibited_fields` for the normative list of forbidden fields. See SPECIFICATION.md §1.2 binding rules for cross-layer contamination principles.

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

**Normative source: SPECIFICATION.md §2.15.** This section serves as a quick-reference index.

**Precedence Chain:** Explicit override (schema `conflict_resolution` field) → `compatible_overrides()` for symmetric pairs (`{always_wins, never_wins}`, identical `defer_to` targets) → priority → specificity → recency → Conflict Artifact. Missing or ambiguous `defer_to` targets fall through to computed resolution (not Conflict Artifact). Cross-lineage pairs produce advisory Conflict Artifacts only (§2.15.2). All inputs are frozen in the CG-IR snapshot, making outcomes deterministic per snapshot.

**Precedence Clarifier:** Policy prose describes governance *intent* for human authors. Schema `conflict_resolution` is structural override *data*. SPECIFICATION.md §2.15 is the sole *algorithm*. On any conflict between the three layers, spec wins; policy is never read at runtime.

See `rule_schema.json` `x-conflict-resolution-binding.priority_level_mapping` for the enum-to-integer mapping. See SPECIFICATION.md §2.15 for the normative `specificity_score` algorithm and `resolve_conflict` function (including `compatible_overrides()`, DFS `defer_to` cycle detection, and §2.15.2 cross-lineage advisory resolution).

## Reference Validator

Production-grade implementations SHOULD ship a canonical reference validator satisfying §9.2.15 portable checks (UTC-only timestamps, finite numerics, regex flags whitelist, AST discriminator walk) and §9.2.6 RE2 canary test vectors. User stories S-30 (architectural audit gates) and S-31 (reference validator) define the behavioral contract.

## Compile-Time Engine Invariants

See SPECIFICATION.md §2.9 for the normative compile-time engine invariants. JSON Schema Draft-07 structural validation is necessary but insufficient — custom compile-time validators are mandatory for evaluator complexity limits, discriminator validation, and portability constraints.

## Migration Rules

See SPECIFICATION.md §2.2.4 and §5 for normative migration and versioning invariants.

## Composite Evaluator Recursion

See SPECIFICATION.md §2.9 for compile-time complexity limits (depth ≤ 32, nodes ≤ 256, width ≤ 64, pattern length ≤ 4096, metadata ≤ 16 384 bytes). JSON Schema Draft-07 cannot natively enforce recursive depth or aggregate node count limits — custom compile-time validators MUST walk the evaluator AST (§2.9).

## Deterministic Serialization & Hashing

See SPECIFICATION.md §2.6 for the normative hash formulas and §2.16 for the serialization rules and array ordering classification table.

## Evaluation Portability & Complexity Guardrails

See SPECIFICATION.md §2.9 for the full evaluator contract, portability constraints, and complexity limits.

## Compilation Pipeline

The end-to-end lifecycle from policy authoring to runtime execution. See SPECIFICATION.md §2.4 for the canonical pipeline. Key stages:
`normalize` → `classify` → `select_controls` → `evaluate` → `aggregate` → `report`

Each stage performs a specific class of validation. The engine is the sole executor; policy is never interpreted at any stage after Policy Validation.

See [SPECIFICATION.md](SPECIFICATION.md) for the full universal rule governance specification.
