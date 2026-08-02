# Selma API

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **ROD:** [AIP-121](https://google.aip.dev/121) · [AIP-136](https://google.aip.dev/136)  
> **design_contract_version:** [`docs/standards/VERSION`](../standards/VERSION) · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

OpenAPI wire surface for driving adapter **`rest_interface`** (C4 peer **`api`**).  
This is **not** a parallel product design: it is the HTTP encoding of the same
resources, use cases, domain types, and store projections already defined in
use case / class / package / ERD / C4 / contracts.

**Entry point:** [`openapi.yaml`](openapi.yaml)

## View concern (this directory owns)

Full exclusive-ownership matrix: [`../standards/view_concerns.md`](../standards/view_concerns.md).

| | |
| :--- | :--- |
| **Answers** | *What HTTP resources, methods, and wire schemas* the product exposes |
| **Owns 100%** | Path inventory (AIP-121/136); HTTP methods; `operationId`s; request/response **wire** schemas; shared parameters/headers as wire names; error response components / envelope shape; OpenAPI security **scheme declaration**; multi-file OpenAPI + Redocly; `api_resources` path list identity |
| **Does not own** | Peer inventing (C4) · package trees/ports · domain method catalogs · actor graphs · zones/TLS/RPO · FSM tables/guards · capability catalog / SoD · store mutability / locks / HLC · dual-document principles · certification gate criteria · ERD physical keys · REST **behavior** norms (idempotency rules live in `rest_api.yaml` — this view only **encodes** headers/status) |
| **Join key** | C4 peer IDs + ROD PascalCase use-case names + domain resource type names + `api_resources` |

**Absorption rule:** API is the HTTP encoding of use case + class + ERD + C4 owners — not a parallel product design. Every path/operation must map to an existing ROD use case (or pure Get/List on an existing resource).

## AIP-121 / AIP-136 (mandatory)

| Principle | How Selma applies it |
| :--- | :--- |
| Resources are **nouns** | `Directive`, `Compilation`, `Inspection`, `Finding`, `Artifact` |
| Prefer **standard methods** | Create / Get / List / Update / Delete on collections and items |
| **Get + List** required | Every collection supports both (soft-deleted Directives remain Get-able) |
| **Uniform resource schema** | Create/Get/Update/List items share `Directive`, `Inspection`, `Finding`, … |
| **Custom methods** only when standard verbs do not fit | AIP-136 `:` + camelCase (`:fork`, `:transitionFinding`, …) |
| **Stateless** | Each request independent; server owns durable state |
| **Acyclic resource graph** | Parent/child via path only; cross-store refs are hashes/IDs |

## Resources (identical to registry + class routers)

| # | Resource (domain type) | Paths | Standard | Custom | C4 owner |
|---|---|---|---|---|---|
| R1 | `Directive` | `/directives`, `/{lineage_id}`, `/revisions/{revision}` | C L G U D(soft) | `:fork` `:merge` `:split` `:restore` | `directives_application` |
| R2 | `Compilation` / `CgIrSnapshot` | `/compilations`, `/{hash}` | C L G | — | `compilation_application` |
| R3 | `Inspection` | `/inspections`, `/{inspection_id}` | C L G | — | `inspections_application` |
| R4 | `Finding` | `/findings`, `/{finding_id}`, `/events`, `/guidance` | L G | `:transitionFinding` `:attachEvidence` `:listFindingAggregates` | `findings_application` |
| R5 | `Artifact` | `/artifacts`, `/{artifact_id}` | L G | `:reviewConflictArtifact` | `artifacts_repository` |

Registry SSoT: `docs/standards/c4_registry.yaml` → `api_resources`.

## ROD use case ↔ operationId ↔ HTTP (identical strings)

| Use case (UC / package / class) | Method | Path | operationId |
| :--- | :--- | :--- | :--- |
| `CreateDirective` | POST | `/directives` | `createDirective` |
| `ListDirectives` | GET | `/directives` | `listDirectives` |
| `GetDirective` | GET | `/directives/{lineage_id}` | `getDirective` |
| `UpdateDirective` | PATCH | `/directives/{lineage_id}` | `updateDirective` |
| `LifecycleTransitions.Retire` | DELETE | `/directives/{lineage_id}` | `retireDirective` |
| `LifecycleTransitions.Fork` | POST | `/directives/{lineage_id}:fork` | `forkDirective` |
| `LifecycleTransitions.Merge` | POST | `/directives/{lineage_id}:merge` | `mergeDirective` |
| `LifecycleTransitions.Split` | POST | `/directives/{lineage_id}:split` | `splitDirective` |
| `LifecycleTransitions.Restore` | POST | `/directives/{lineage_id}:restore` | `restoreDirective` |
| `CompileDirectives` | POST | `/compilations` | `compileDirectives` |
| (Get Compilation) | GET | `/compilations/{hash}` | `getCompilation` |
| (List Compilations) | GET | `/compilations` | `listCompilations` |
| `CreateInspection` | POST | `/inspections` | `createInspection` |
| `GetInspection` | GET | `/inspections/{inspection_id}` | `getInspection` |
| (List Inspections) | GET | `/inspections` | `listInspections` |
| `ListFindings` | GET | `/findings` | `listFindings` |
| `GetFinding` | GET | `/findings/{finding_id}` | `getFinding` |
| `TransitionFinding` | POST | `/findings/{finding_id}:transitionFinding` | `transitionFinding` |
| `AttachEvidence` | POST | `/findings/{finding_id}:attachEvidence` | `attachEvidence` |
| `ListFindingAggregates` | GET | `/findings:listFindingAggregates` | `listFindingAggregates` |
| `GetFindingGuidance` | GET | `/findings/{finding_id}/guidance` | `getFindingGuidance` |
| `ReviewConflictArtifact` | POST | `/artifacts/{artifact_id}:reviewConflictArtifact` | `reviewConflictArtifact` |

**Not client HTTP routes:** `OpenFindings`, `RunInspectionPipeline`, `PublishCompiledRules`, `DrainOutbox`, `ValidateDirectiveDocuments`, domain `ResolveConflict`, offline `RunArchitecturalCertification`.

## Wire schema ↔ domain / ERD

| Wire schema | Domain / class | Store / ERD |
| :--- | :--- | :--- |
| `Directive` | `Directive` aggregate | `directives` + `directive_revisions` |
| `Compilation` | `CgIrSnapshot` | `snapshots` (content-addressed) |
| `Inspection` | `Inspection` aggregate | `inspection_snapshots` |
| `Finding` | `Finding` / `FindingProjection` | `finding_projections` + events fold |
| `FindingEvent` | event stream | `events` |
| `Guidance` | `GuidanceView` | doctrine via `paired_policy_ref` |
| `Artifact` / `ConflictArtifact` | write-once blobs | `artifacts_store` tables |
| `AggregateReport` | `AggregateReport` | projections over events |
| `FindingState` storage_id | domain `FindingState` | ERD `$ENUM_FINDING_STATE` |

## Layout

```text
docs/api/
├── openapi.yaml
├── redocly.yaml
├── paths/          # one file per resource family
├── components/     # parameters, responses, schemas, security
└── schemas/        # JSON Schema primary resource views
```

## Lint & checks

```bash
cd docs/api && npx @redocly/cli lint openapi.yaml
python scripts/check_design_alignment.py
```

## Normative references

| Topic | Authority |
| :--- | :--- |
| REST behavior / idempotency / errors | `docs/spec/contracts/interfaces/rest_api.yaml` |
| Capabilities / SoD | `docs/spec/contracts/authorization/` |
| Finding FSM | `docs/spec/contracts/finding_lifecycle/` |
| Peers + `api_resources` | `docs/standards/c4_registry.yaml` |
| Actor goals | `docs/usecase/` |
| Types / routers / DTOs | `docs/class/` |
| Packages | `docs/package/` |
| Tables | `docs/erd/` |
