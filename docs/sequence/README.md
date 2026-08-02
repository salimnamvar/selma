# Selma — Sequence Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** [`docs/standards/VERSION`](../standards/VERSION) · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *In what order* peers and packages collaborate for a ROD use case or API operation |
| **Owns 100%** | Time-ordered message collaborations; participants (C4/package labels); messages using ROD use-case names, class methods, and **exact API paths/operationIds**; alt/opt/loop/group for gate and contract branches; shared `common/seq_*` |
| **Does not own** | Peer inventing · package trees · class member catalogs · zones/TLS · FSM charts · use-case oval catalogs · ERD · OpenAPI schema definitions · capability catalog prose · PlantUML notes |
| **Join key** | C4 peer IDs + ROD use-case names + `docs/api` paths/operationIds |

**No PlantUML `note` blocks.** Encode branches as `alt` / `opt` / groups.  
**Colors:** [`../standards/common/ca_palette.puml`](../standards/common/ca_palette.puml) via `common/seq_styles.puml` only.

## Layout

```text
docs/sequence/
├── common/
│   ├── seq_styles.puml      # CA palette skinparams
│   └── seq_identities.puml  # titles, participants, API path macros
└── seq_NNN_*.puml           # orchestrators
```

**Include order:** `seq_styles` → `seq_identities` → participants (actors → interface → application → domain → infrastructure → frameworks).

## Catalog (coverage ↔ API ↔ use case)

| ID | File | API paths / operationIds | ROD use cases | State / activity |
| :--- | :--- | :--- | :--- | :--- |
| **SEQ-001** | [seq_001_directive_standard.puml](seq_001_directive_standard.puml) | `POST\|GET /directives`, `GET\|PATCH\|DELETE /directives/{lineage_id}`, revisions | `CreateDirective`, `ListDirectives`, `GetDirective`, `UpdateDirective`, `LifecycleTransitions.Retire` | [ACT-001](../activity/act_001_directive_mutations.puml) · SM-002 |
| **SEQ-002** | [seq_002_directive_lifecycle.puml](seq_002_directive_lifecycle.puml) | `:fork` `:merge` `:split` `:restore` | `LifecycleTransitions` Fork/Merge/Split/Restore | ACT-001 · SM-002 |
| **SEQ-003** | [seq_003_compilation.puml](seq_003_compilation.puml) | `POST\|GET /compilations`, `GET /compilations/{hash}` | `CompileDirectives`, `PublishCompiledRules`, `DrainOutbox`, `ValidateDirectiveDocuments` | [ACT-002](../activity/act_002_compilation.puml) · SM-003 |
| **SEQ-004** | [seq_004_inspection.puml](seq_004_inspection.puml) | `POST\|GET /inspections`, `GET /inspections/{inspection_id}` | `CreateInspection`, `GetInspection`, `RunInspectionPipeline`, `OpenFindings` | [ACT-003](../activity/act_003_inspection.puml) · SM-004 |
| **SEQ-005** | [seq_005_finding_lifecycle.puml](seq_005_finding_lifecycle.puml) | `GET /findings`, `GET /findings/{id}`, `:transitionFinding`, `:attachEvidence`, `/events` | `GetFinding`, `ListFindings`, `TransitionFinding`, `AttachEvidence` | [ACT-004](../activity/act_004_finding_disposition.puml) · SM-001 |
| **SEQ-006** | [seq_006_guidance_aggregates.puml](seq_006_guidance_aggregates.puml) | `/guidance`, `:listFindingAggregates` | `GetFindingGuidance`, `ListFindingAggregates` | [ACT-006](../activity/act_006_guidance_aggregates.puml) |
| **SEQ-007** | [seq_007_conflict.puml](seq_007_conflict.puml) | Artifact GET, `:reviewConflictArtifact` | `ResolveConflict`, `ReviewConflictArtifact` | [ACT-005](../activity/act_005_conflict.puml) · SM-005 |
| **SEQ-008** | [seq_008_authorization.puml](seq_008_authorization.puml) | all Bearer routes (gate) | `AuthenticateActor`, `CheckCapability`, `EnforceSegregationOfDuties`, `AppendDenial` | [ACT-007](../activity/act_007_authorization.puml) · SM-007 |
| **SEQ-009** | [seq_009_artifacts.puml](seq_009_artifacts.puml) | `GET /artifacts`, `GET /artifacts/{id}` | list/get Artifact; offline `RunArchitecturalCertification` | [ACT-008](../activity/act_008_artifacts.puml) · SM-008 |

Every client-facing API path family and ROD use case above is covered. Gate SEQ-008 is included by all mutating sequences via shared authn/authz steps.

## Clean Architecture participant order

| Box | C4 / package examples | CA MACRO color |
| :--- | :--- | :--- |
| Actors | Regulatory Official, Compliance Representative, System | Actors |
| Interface | `clients`, `rest_interface` (C4: `api`) | Interface |
| Application | `*_application` use cases | Application |
| Domain | `ResolveConflict` (not peer) | Domain |
| Infrastructure | `*_repository`, gateways | Infrastructure |
| Frameworks | `*_store` | Frameworks |

## Conventions

- Headers: `Title`, `Source`, `C4`, `Package`, `API`, `UseCase`, `Contract: docs/standards/VERSION`
- Message labels: class method or use-case name + API path when at the gate
- Errors: `Error` envelope codes from API / `rest_api.yaml` (`CapabilityDenied`, `FSMError`, …)
- Non-peers labeled `(domain · not peer)` / `(offline · not peer)`

## Render

```bash
plantuml docs/sequence/seq_*.puml
python scripts/check_design_alignment.py
```

## Related views

| View | Relationship |
| :--- | :--- |
| [API](../api/README.md) | Path / operationId SSoT |
| [Use Case](../usecase/README.md) | ROD oval names |
| [Class](../class/README.md) | Method shapes on messages |
| [Activity](../activity/README.md) | Procedural swim-lanes (not message order) |
| [State](../state/README.md) | FSM / pipeline states |
| [Spec](../spec/contracts/) | Normative behavior |
