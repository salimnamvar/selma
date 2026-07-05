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

| Layer | Role | Runtime Influence |
| :--- | :--- | :--- |
| **SPECIFICATION.md** | Normative — defines system behavior, invariants, algorithms | Sole executable source at runtime |
| **rule_schema.json** | Structural projection of spec invariants | Data carrier — fields read by engine; schema itself is not an algorithm |
| **policy_doctrine.yaml** | Governance intent — describes how humans write rules | **None.** Never read at inspection, evaluation, or conflict resolution runtime |

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

**Anchor Reference Syntax (§7.2):** `section:<id>[/<subsection>]` or JSON Pointer (`/path/to/section`).

## Contamination Guards

Each contract explicitly lists what it MUST NOT contain:

### Policy Contract Forbidden Fields
`parameters`, `conditions`, `evaluator_hint`, `evaluator_type`, `evaluator_config`, `weight`, `depends_on`, `conflicts_with`, `status`, `created_at`, `expires_at`, `remediation`, `target`, `lineage`, `technical_hints`

### Rule Contract Forbidden Root Fields
`preamble`, `governance`, `definitions`, `principles`, `sanctions`, `references`, `writing_principles`, `sections`, `guidance`, `columns`

## Version Synchronization

Both contracts reference each other's version:
- `policy_doctrine.yaml` → `doctrine.rule_contract_version` + `doctrine.rule_contract_id`
- `rule_schema.json` → `policy_contract_version` + `policy_contract_id`

Update both when either contract changes.

## Priority Hierarchy

Rules exist at different authority levels. When two rules conflict, the higher-priority rule wins:

1. **Constitutional** - Core principles that cannot be overridden
2. **Statutory** - Rules enacted by authorized governing bodies
3. **Regulatory** - Rules created by agencies to implement statutory requirements
4. **Operational** - Day-to-day procedures implementing higher-level rules
5. **Advisory** - Recommendations that are not mandatory

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

## Metadata Namespacing

Root `metadata` is informational only. Declared namespaces: `audit`, `vendor`, `author`, `migration`. No executable hints permitted (§7.1).

## Merge Semantics

Merged `lineage_id` = lexicographic minimum of parent lineage_ids. New execution_id generated deterministically per §2.2.2.

## Specification

See [SPECIFICATION.md](SPECIFICATION.md) for the full universal rule governance specification.
