# Selma Class Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `docs/standards/VERSION` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *What types and methods* realize each Clean Architecture package? |
| **Owns 100%** | Aggregate/entity/VO/event members; domain service signatures; ISP **port method shapes**; ROD use-case classes; DTO fields; adapter method implements; interface router/command/screen types; composition-root types; shared `common/cd_*` identities and C4-aligned colors |
| **Does not own** | Package module trees / dependency edges (package/) · peer inventing / Component Rel (c4-model/) · zones / TLS / RPO (deployment/) · FSM transition tables as normative text (state/ + spec/) · store mutability / capability catalog (spec/) |
| **Join key** | C4 peer IDs + package module names (identical strings to package / state / deployment identities) |

**No PlantUML `note` blocks.** Encode design as types, stereotypes, fields, and methods.

## Source layout (like C4 / package / state / deployment `common/`)

| Path | Role | Edit when… |
| :--- | :--- | :--- |
| [`common/cd_styles.puml`](common/cd_styles.puml) | Skinparams + **semantic color macros** (C4-identical hex) | Visual language / harmony |
| [`common/cd_identities.puml`](common/cd_identities.puml) | Diagram titles, package module titles, C4 IDs, port names | Rename labels / peers |
| [`common/cd_section_domain_*.puml`](common/) | Domain modules by package | Aggregates / VOs / services |
| [`common/cd_section_domain_connections.puml`](common/cd_section_domain_connections.puml) | Domain type edges | Relationships |
| [`common/cd_section_app_*.puml`](common/) | Ports, DTOs, use cases | Application layer |
| [`common/cd_section_app_connections.puml`](common/cd_section_app_connections.puml) | Use case → port edges | Wiring |
| [`common/cd_section_infra_*.puml`](common/) | Adapters by infrastructure package | Implementers |
| [`common/cd_section_infra_connections.puml`](common/cd_section_infra_connections.puml) | `..|>` implements + platform | Adapter wiring |
| [`common/cd_section_iface_*.puml`](common/) | REST/CLI/TUI + composition | Driving adapters |
| [`common/cd_section_iface_connections.puml`](common/cd_section_iface_connections.puml) | Gate pipeline + UC edges | Interface wiring |
| [`cd_00N_*.puml`](.) | Orchestrators only | Include order |

**Include order:** `cd_styles` → `cd_identities` → `cd_section_*` → `*_connections`.

```bash
plantuml docs/class/*.puml
python scripts/check_design_alignment.py
```

## Color harmony (CA MACRO + class MICRO)

**SSoT:** [`../standards/common/ca_palette.puml`](../standards/common/ca_palette.puml) via [`common/cd_styles.puml`](common/cd_styles.puml).

### MACRO — package rings (identical to package diagram)

| Package ring | CA layer | Fill / border |
| :--- | :--- | :--- |
| `*_domain` | Domain | `#F3E5F5` / `#7B1FA2` |
| `*_application` | Application | `#E0F2F1` / `#00897B` |
| `*_infrastructure` | Infrastructure | `#FFF3E0` / `#EF6C00` |
| `*_interface` | Interface | `#E1F5FE` / `#0288D1` |
| `composition_root` | Composition | `#E8EAF6` / `#283593` |
| `application.ports` | Gate (micro) | `#FFEBEE` / `#C62828` |

### MICRO — type archetypes

| Archetype | CA mapping | Fill / border |
| :--- | :--- | :--- |
| Aggregate Root | Frameworks (durable) | `#E8F5E9` / `#2E7D32` |
| Value Object / DTO | Interface | `#E1F5FE` / `#0288D1` |
| Domain Service | Domain | `#F3E5F5` / `#7B1FA2` |
| Use Case | Application | `#E0F2F1` / `#00897B` |
| Port | Gate | `#FFEBEE` / `#C62828` |
| Domain Event / Enum | Hermetic (micro) | `#FFFDE7` / `#F9A825` |
| Adapter | Infrastructure | `#FFF3E0` / `#EF6C00` |
| Entity | micro entity | `#ECEFF1` / `#546E7A` |

**Rule:** change hex only in `ca_palette.puml`.

## Naming (aligned with other views)

| View | File pattern | Example |
| :--- | :--- | :--- |
| C4 | `c4_selma_{level}.puml` | `c4_selma_component.puml` |
| Package | `pkg_NNN_*.puml` | `pkg_001_clean_architecture.puml` |
| Deployment | `dep_NNN_*.puml` | `dep_001_production.puml` |
| State | `state_machine_NNN_*.puml` | `state_machine_001_finding_lifecycle.puml` |
| **Class** | `cd_NNN_*.puml` | `cd_001_domain_model.puml` |

| Element | Convention |
| :--- | :--- |
| Diagram ID | `CLS-NNN` / `Class NNN` in title and footer |
| Package boxes | Exact `*_domain` / `*_application` / `*_infrastructure` / `*_interface` strings from package identities |
| C4 subtitles | e.g. `compiled_rules_application` + `(C4: compilation_application)` |
| Port names | `DirectiveRepository`, `FindingOpenPort`, … (package `$PORT_*`) |
| Full words | Prefer `segregation of duties`, `hybrid logical clock`, `content-addressed storage` in stereotypes/prose |
| Type aliases | Stable PascalCase (`Directive`, `SqlDirectiveWriter`) |

## Diagram index

| ID | File | Clean Architecture layer | Sections |
|----|------|--------------------------|----------|
| CLS-001 | [cd_001_domain_model.puml](cd_001_domain_model.puml) | Domain | `cd_section_domain_*` |
| CLS-002 | [cd_002_application_services.puml](cd_002_application_services.puml) | Application | `cd_section_app_*` |
| CLS-003 | [cd_003_infrastructure_adapters.puml](cd_003_infrastructure_adapters.puml) | Infrastructure | `cd_section_infra_*` |
| CLS-004 | [cd_004_interface_composition.puml](cd_004_interface_composition.puml) | Interface + Composition | `cd_section_iface_*` |

## Layer coverage (Clean Architecture A–Z)

| CA layer | Diagram | Package modules covered |
|----------|---------|-------------------------|
| Entities / domain | CLS-001 | `shared_domain`, `directives_domain`, `compiled_rules_domain`, `inspections_domain`, `findings_domain`, `conflicts_domain`, auth grants, certification payload types |
| Use cases | CLS-002 | `directives_application`, `compiled_rules_application` (C4: `compilation_application`), `inspections_application`, `findings_application` |
| Interface adapters (driven) | CLS-003 | `*_infrastructure` including `DetectionEvaluator`, `DenialAuditAdapter` |
| Interface adapters (driving) | CLS-004 | `rest_interface` (paths = [`../api/`](../api/README.md) AIP-121/136), `cli_interface`, `tui_interface` |
| Composition / main | CLS-004 | `composition_root` |

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

## Related

- [Package diagrams](../package/README.md) — modules and edges  
- [C4 architecture](../c4-model/README.md) — product peers  
- [Deployment](../deployment/README.md) — topology / ops  
- [State machines](../state/README.md) — FSM visualization  
- [Spec contracts](../spec/README.md) · [Schema](../schema/README.md)  
- [View concerns](../standards/view_concerns.md)
