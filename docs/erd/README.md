# Selma — Entity-Relationship Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.3.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)  
> **View ownership:** [`../standards/view_concerns.md`](../standards/view_concerns.md) (ERD row)

## Answers

*What durable tables and relationships does each C4 `*_store` hold?*

ERD owns **storage structure** only: entities, columns, keys, enum domains, and
mutability stereotypes. Normative locking, retention prose, FSM transition
tables, and capability catalogs live under [`../spec/contracts/`](../spec/contracts/)
and are **not** restated as diagram notes.

## Catalog

| File | Diagram ID | C4 store ID | Owner repository | Storage model |
| :--- | :--- | :--- | :--- | :--- |
| `erd_001_directives_store.puml` | ERD-001 | `directives_store` | `directives_repository` | PostgreSQL · mutable dual documents · compile outbox |
| `erd_002_compiled_rules_store.puml` | ERD-002 | `compiled_rules_store` | `compiled_rules_repository` | Content-addressed · immutable snapshots · lineage head index |
| `erd_003_finding_events_store.puml` | ERD-003 | `finding_events_store` | `finding_events_repository` | Append-only log · hybrid logical clock · projections |
| `erd_004_artifacts_store.puml` | ERD-004 | `artifacts_store` | `artifacts_repository` | Object store · write-once + conflict versioning |

Contract filenames under `spec/contracts/data_stores/` match C4 store IDs
(`directives_store.yaml`, `compiled_rules_store.yaml`, `finding_events_store.yaml`,
`artifacts_store.yaml`).

## Shared maintenance layer

| File | Role |
| :--- | :--- |
| `common/erd_styles.puml` | CA palette include + entity/package skinparams + `$ERD_*` color aliases |
| `common/erd_identities.puml` | Diagram titles/IDs, C4 store peers, table name macros, product terms, stereotypes |

**Include order:** `erd_styles.puml` → `erd_identities.puml` → body.

**Headers (required):** `Title`, `Source`, `C4`, `Package`, `Contract` (= `docs/standards/VERSION`).

**Join key:** C4 store peer IDs from the registry — identical strings to package
`ST_*`, deployment data-zone nodes, and class infrastructure store targets.

**Cross-store links:** content hashes and opaque IDs only (no foreign keys drawn
across failure domains). Pointers such as `head_snapshot_hash` and
`paired_policy_ref` are documented as columns, not multi-store relationships.

**No PlantUML `note` blocks.** Encode mutability with stereotypes
(`<<mutable>>`, `<<append_only>>`, `<<immutable>>`, `<<write_once>>`,
`<<projection>>`, `<<outbox>>`, `<<secondary_index>>`, `<<content_addressed>>`,
`<<system_of_record>>`). Constraints appear as `<<PK>>` / `<<FK>>` /
`<<unique>>` attribute markers and enum entities.

## Alignment map (ERD ↔ other views)

| ERD concern | Aligns with | Does not own |
| :--- | :--- | :--- |
| Table/column shape | Domain aggregates & value objects ([`../class/`](../class/README.md)); store contracts | Class method signatures |
| Outbox columns (`worker_id`, `lease_expires_at`, status enum) | Compilation / directive store contracts; state machine 003 pipeline drain | Locking algorithm narrative |
| `fsm_state` / disposition on projections | Finding lifecycle contracts; class `Finding` / `FindingProjection` | Transition guards (state view) |
| Hybrid logical clock columns + `RetiredNodes` | Finding events store + state machine 009 | Deployment PVC sizing |
| Lineage head index | Compiled rules store `lineage_head_index`; directives `head_snapshot_hash` | CAS publish linearization prose |
| Artifact types | Ports: Inspection / Finding / Certification artifact ports (package + class) | Pipeline stage inventory as process (activity/state) |
| Enum domains | Domain enums in class; lifecycle contracts | Actor goal catalogs (use case) |

## Rendering

```bash
# Single file
plantuml docs/erd/erd_001_directives_store.puml

# All ERDs
plantuml docs/erd/erd_00*.puml
```

## Check

```bash
python scripts/check_design_alignment.py
```
