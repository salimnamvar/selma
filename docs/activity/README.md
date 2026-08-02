# Selma — Activity Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** [`docs/standards/VERSION`](../standards/VERSION) · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *What procedural control flow* (decisions, fork/join, swim-lanes) realizes a ROD use case or API operation |
| **Owns 100%** | Swim-lane partitions by CA layer / C4 peer; actions named with ROD use cases + class methods; decisions for schema/capability/status guards (labels only); fork/join where contracts allow; API path/operationId on ingress; shared `common/act_*` |
| **Does not own** | Peer inventing · package trees · class catalogs · zones/TLS · FSM state charts (state owns) · sequence message order (sequence owns) · OpenAPI schemas · capability catalog tables · PlantUML notes |
| **Join key** | C4 peer IDs + ROD use-case names + `docs/api` paths/operationIds |

**No PlantUML `note` blocks.** Encode as decisions, action labels, and lane moves.  
**Colors:** CA palette via `common/act_styles.puml` only.

## Layout

```text
docs/activity/
├── common/
│   ├── act_styles.puml
│   └── act_identities.puml
└── act_NNN_*.puml
```

**Include order:** `act_styles` → `act_identities` → body.

## Catalog (coverage ↔ API ↔ use case)

| ID | File | API paths / operationIds | ROD use cases | Sequence |
| :--- | :--- | :--- | :--- | :--- |
| **ACT-001** | [act_001_directive_mutations.puml](act_001_directive_mutations.puml) | Directive standard + lifecycle custom | `CreateDirective`, `ListDirectives`, `GetDirective`, `UpdateDirective`, `LifecycleTransitions` | SEQ-001, SEQ-002 |
| **ACT-002** | [act_002_compilation.puml](act_002_compilation.puml) | `/compilations`, `/{hash}` | `CompileDirectives`, `ValidateDirectiveDocuments`, `PublishCompiledRules`, `DrainOutbox` | SEQ-003 |
| **ACT-003** | [act_003_inspection.puml](act_003_inspection.puml) | `/inspections` | `CreateInspection`, `GetInspection`, `RunInspectionPipeline`, `OpenFindings` | SEQ-004 |
| **ACT-004** | [act_004_finding_disposition.puml](act_004_finding_disposition.puml) | findings Get/List, `:transitionFinding`, `:attachEvidence`, events | `GetFinding`, `ListFindings`, `TransitionFinding`, `AttachEvidence` | SEQ-005 |
| **ACT-005** | [act_005_conflict.puml](act_005_conflict.puml) | artifacts + `:reviewConflictArtifact` | `ResolveConflict`, `ReviewConflictArtifact` | SEQ-007 |
| **ACT-006** | [act_006_guidance_aggregates.puml](act_006_guidance_aggregates.puml) | `/guidance`, `:listFindingAggregates` | `GetFindingGuidance`, `ListFindingAggregates` | SEQ-006 |
| **ACT-007** | [act_007_authorization.puml](act_007_authorization.puml) | all Bearer routes (gate) | `AuthenticateActor`, `CheckCapability`, `EnforceSegregationOfDuties`, `AppendDenial` | SEQ-008 |
| **ACT-008** | [act_008_artifacts.puml](act_008_artifacts.puml) | `GET /artifacts` | list/get Artifact; offline certification write | SEQ-009 |

## Swim-lane palette (Clean Architecture)

| Lane | MACRO | Example titles |
| :--- | :--- | :--- |
| Actors / people | Actors | (when human step is explicit) |
| `rest_interface` (C4: api) | Interface | gate authn/authz, HTTP respond |
| `*_application` | Application | ROD use cases |
| `*_domain` / ResolveConflict | Domain | domain services |
| `*_repository` | Infrastructure | port adapters |
| `*_store` | Frameworks | durable writes |
| Gate / hermetic | MICRO | DenialAuditPort, compile CPU |

## Relationship to other views

| Activity owns | Does not replace |
| :--- | :--- |
| Procedural decisions and concurrency | State machines (state inventory) |
| Swim-lane who does what | Sequence (message order and payload names) |
| Ingress API path labels | API (path/schema SSoT) |

## Render

```bash
plantuml docs/activity/act_*.puml
python scripts/check_design_alignment.py
```

## Related views

- [Sequence](../sequence/README.md) — collaborations in time  
- [State](../state/README.md) — FSM / pipeline states  
- [API](../api/README.md) — paths and wire types  
- [Use Case](../usecase/README.md) — actor goals  
- [Spec contracts](../spec/contracts/) — normative rules  
