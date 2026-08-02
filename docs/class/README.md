# Selma Class Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `1.1.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *What types and methods* realize each Clean Architecture package? |
| **Owns 100%** | Aggregate/entity/VO/event members; domain service signatures; ISP **port method shapes**; ROD use-case classes; DTO fields; adapter method implements; interface router/command/screen types; composition-root types |
| **Does not own** | Package module trees / dependency edges (package/) · peer inventing / Component Rel (c4-model/) · zones / TLS / RPO (deployment/) · FSM transition tables as normative text (state/ + spec/) · store mutability / capability catalog (spec/) |
| **Join key** | C4 peer IDs in headers; package module names on package boxes |

PlantUML class diagrams are an **implementation type view**. They must **not** restate package layout as the product graph, deployment topology, or contract prose. **No PlantUML `note` blocks** — unfinished design smell; encode as stereotypes, fields, methods, or invariants on types.

## Prerequisites

- [PlantUML](https://plantuml.com/) (v1.2022.1+)
- Java Runtime (for PlantUML rendering)

## Usage

```bash
plantuml docs/class/*.puml
plantuml -tsvg docs/class/*.puml
python scripts/check_design_alignment.py
```

## Diagram index

| ID | File | Clean Architecture layer | Responsibility |
|----|------|--------------------------|----------------|
| CLS-001 | [cd_001_domain_model.puml](cd_001_domain_model.puml) | Domain | Aggregates, entities, VOs, domain services, domain events — by `*_domain` package |
| CLS-002 | [cd_002_application_services.puml](cd_002_application_services.puml) | Application | ISP ports (full methods), ROD use cases, DTOs — by `*_application` package |
| CLS-003 | [cd_003_infrastructure_adapters.puml](cd_003_infrastructure_adapters.puml) | Infrastructure | One adapter class per port + platform Hasher/HLC |
| CLS-004 | [cd_004_interface_composition.puml](cd_004_interface_composition.puml) | Interface + Composition | REST/CLI/TUI driving adapters, gate pipeline, DI wiring |

## Layer coverage (Clean Architecture A–Z)

| CA layer | Diagram | Package modules covered |
|----------|---------|-------------------------|
| Entities / domain | CLS-001 | `shared_domain`, `directives_domain`, `compiled_rules_domain`, `inspections_domain`, `findings_domain`, `conflicts_domain`, auth grants, certification **payload types** |
| Use cases | CLS-002 | `directives_application`, `compiled_rules_application` (C4: `compilation_application`), `inspections_application`, `findings_application` |
| Interface adapters (driven) | CLS-003 | `*_infrastructure` including `DetectionEvaluator`, `DenialAuditAdapter` |
| Interface adapters (driving) | CLS-004 | `rest_interface`, `cli_interface`, `tui_interface` |
| Frameworks & drivers | CLS-003 (implements only) | Store **access** via adapters; store **semantics** remain in spec |
| Composition / main | CLS-004 | `composition_root` (`ApplicationContainer`, `PortBindings`, `OutboxDrainScheduler`) |

## Resource-oriented design (ROD)

Use cases are **Verb + Resource** types (or a lifecycle façade with explicit verb methods):

| Resource cluster | Use cases (CLS-002) |
|------------------|---------------------|
| Directives | `CreateDirective`, `GetDirective`, `ListDirectives`, `UpdateDirective`, `LifecycleTransitions` (Retire/Fork/Merge/Split/Restore) |
| Compilation | `CompileDirectives`, `PublishCompiledRules`, `DrainOutbox`, `ValidateDirectiveDocuments` |
| Inspections | `CreateInspection`, `GetInspection`, `RunInspectionPipeline` |
| Findings | `GetFinding`, `ListFindings`, `TransitionFinding`, `GetFindingGuidance`, `AttachEvidence`, `OpenFindings`, `ListFindingAggregates`, `ReviewConflictArtifact` |

Port methods use the same Verb+Resource vocabulary (`GetDirective`, `SaveDirective`, `AppendFindingEvent`, …).

## ISP ports (method authority = this view)

| Port | Owner application package | Implementer class (CLS-003) |
|------|---------------------------|----------------------------|
| `DirectiveRepository` | `directives_application` | `SqlDirectiveWriter` |
| `CompilerReadPort` | `compiled_rules_application` | `SqlCompilerReader` |
| `GuidanceReadPort` | `findings_application` | `SqlGuidanceReader` |
| `CompiledRulesRepository` | `compiled_rules_application` | `ContentAddressedCompiledRulesRepository` |
| `FindingEventRepository` | `findings_application` | `AppendOnlyFindingEventRepository` |
| `FindingOpenPort` | `findings_application` | `OpenFindings` (use-case façade, CLS-002) |
| `DenialAuditPort` | `findings_application` | `DenialAuditAdapter` |
| `InspectionArtifactPort` | `inspections_application` | `InspectionArtifactAdapter` |
| `FindingArtifactPort` | `findings_application` | `FindingArtifactAdapter` |
| `CertificationArtifactPort` | composition / offline tool | `CertificationArtifactAdapter` |
| `TargetSourcesGateway` | `inspections_application` | `HttpTargetSourcesGateway` |

Module ownership of ports: [`../package/README.md`](../package/README.md). Peer graph: [`../c4-model/`](../c4-model/README.md).

## Shared styles

[`common/cd_styles.puml`](common/cd_styles.puml) — local `!include` only (no `!includeurl`).

| Archetype | Background |
|-----------|------------|
| Aggregate Root | `#E0F2F1` |
| Value Object / DTO / Read Model | `#E8EAF6` |
| Domain Event / Enum | `#FFF8E1` |
| Domain Service / Use Case | `#E8F5E9` |
| Port | `#FCE4EC` |
| Entity | `#ECEFF1` |
| Adapter | `#FFE0B2` |
| Interface adapter | `#BBDEFB` |

## Related

- [Package diagrams](../package/README.md) — modules and edges  
- [C4 architecture](../c4-model/README.md) — product peers  
- [Deployment](../deployment/README.md) — topology / ops  
- [State machines](../state/README.md) — FSM visualization  
- [Spec contracts](../spec/README.md) · [Schema](../schema/README.md)  
- [View concerns](../standards/view_concerns.md)
