# Selma Package Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.1.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

## View concern

| | |
| :--- | :--- |
| **Answers** | *How* is source code modularized under Clean Architecture? |
| **Owns** | `{resource}_{layer}` packages, use cases, ISP ports, domain libs, infrastructure adapters, composition root, module dependency edges |
| **Does not own** | Peer inventing (C4 registry), component Rel graph semantics (C4 Component), network zones / TLS / failure domains / RPO (deployment), FSM tables / locks (spec) |
| **Join key** | C4 peer IDs on package titles only — never redefine them |

PlantUML package diagrams are an **implementation view**. Behavior stays in `spec/`; product structure in `c4-model/`; runtime topology in `deployment/`.

## Source layout (like C4 `common/`)

| Path | Role | Edit when… |
| :--- | :--- | :--- |
| [`common/pkg_styles.puml`](common/pkg_styles.puml) | Colours, `packageStyle`, `<<port>>` skin | Visual language |
| [`common/pkg_identities.puml`](common/pkg_identities.puml) | Titles, port/store names, alias registry | Rename labels |
| [`common/pkg_section_interface.puml`](common/pkg_section_interface.puml) | `*_interface` | REST/CLI/TUI modules |
| [`common/pkg_section_composition.puml`](common/pkg_section_composition.puml) | `composition_root` | DI / outbox scheduler |
| [`common/pkg_section_application.puml`](common/pkg_section_application.puml) | `*_application` + ports | Use cases / ISP ports |
| [`common/pkg_section_domain.puml`](common/pkg_section_domain.puml) | `*_domain` | Aggregates / domain services |
| [`common/pkg_section_infrastructure.puml`](common/pkg_section_infrastructure.puml) | `*_infrastructure` | Adapters / platform |
| [`common/pkg_section_stores.puml`](common/pkg_section_stores.puml) | Store **symbols** only (C4 IDs) | Frameworks ring targets |
| [`common/pkg_connections.puml`](common/pkg_connections.puml) | All module edges | Wiring / implements |
| [`pkg_001_clean_architecture.puml`](pkg_001_clean_architecture.puml) | Orchestrator | Include order only |

**Include order:** `cd_styles` → `pkg_styles` → `pkg_identities` → sections → `pkg_connections`.

## Usage

```bash
plantuml docs/package/pkg_001_clean_architecture.puml
plantuml -tsvg docs/package/*.puml
```

## Diagram Index

| ID | File | Description |
|----|------|-------------|
| PKG-001 | [pkg_001_clean_architecture.puml](pkg_001_clean_architecture.puml) | CA module map via `common/` includes |

## Package layout

| Layer | Contents | Section file |
|-------|----------|--------------|
| `*_interface` | Routers/commands/screens + gate (`CapabilityEnforcer`, filters) | `pkg_section_interface` |
| `*_application` | ROD use cases + owned `<<port>>` rectangles | `pkg_section_application` |
| `*_domain` | Aggregates, `FindingFsm`, `ResolveConflict`, shared VOs | `pkg_section_domain` |
| `*_infrastructure` | Adapters, `DetectionEvaluator`, Hasher/HLC | `pkg_section_infrastructure` |
| `composition_root` | Container, PortBindings, OutboxDrainScheduler | `pkg_section_composition` |
| frameworks & drivers | Symbols for C4 `*_store` + `target_sources` (not deploy tech) | `pkg_section_stores` |

**Rules:** every package and leaf has ≥1 edge in `pkg_connections.puml`; no decorative subpackages; ports are `[Name] <<port>>` boxes (never circle `interface`).

## Module naming

| Suffix | Responsibility | C4 ring / peer |
|--------|----------------|----------------|
| `*_domain` | Aggregates, pure domain services | Domain (not a C4 peer) |
| `*_application` | Use cases + port ownership | C4 `*_application` (except compile dual) |
| `*_infrastructure` | Adapters implementing ports | C4 `*_repository` / `*_gateway` |
| `*_interface` | REST / CLI / TUI + shared enforcer | C4 `api` + `clients` |

## Package ↔ C4 map

Peer definitions: [`../c4-model/`](../c4-model/README.md) + [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml).

| Package module | C4 entity |
|----------------|-----------|
| `directives_application` / `directives_domain` | `directives_application` |
| `compiled_rules_application` / `compiled_rules_domain` | **`compilation_application`** |
| `compiled_rules_infrastructure` | `compiled_rules_repository` |
| `directives_infrastructure` | `directives_repository` |
| `inspections_application` / `inspections_domain` | `inspections_application` |
| `inspections_infrastructure` | `target_sources_gateway` (+ `DetectionEvaluator` non-peer) |
| `findings_application` / `findings_domain` | `findings_application` |
| `findings_infrastructure` | `finding_events_repository` (+ `DenialAuditPort` implementer) |
| `artifacts_infrastructure` | `artifacts_repository` |
| `rest_interface` / `cli_interface` / `tui_interface` | `api` + `clients` |
| `conflicts_domain` | not a peer — in-process with compile + inspect |
| `platform_infrastructure` | not a peer |

### Naming dual

| C4 peer ID | Package prefix |
|------------|----------------|
| `compilation_application` | `compiled_rules_application` / `compiled_rules_infrastructure` |

Do not invent C4 peer `compiled_rules_application`. Forbidden IDs: registry `forbidden_ids`.

## Application ports (ISP) — owned here

| Port | Owner package | Implementer package | C4 adapter peer |
|------|---------------|---------------------|-----------------|
| `DirectiveRepository` | `directives_application` | `directives_infrastructure` (`SqlDirectiveWriter` or equivalent) | `directives_repository` |
| `CompilerReadPort` | `compiled_rules_application` (C4: `compilation_application`) | `directives_infrastructure` (`SqlCompilerReader`) | `directives_repository` |
| `GuidanceReadPort` | `findings_application` | `directives_infrastructure` (`SqlGuidanceReader`) | `directives_repository` |
| `CompiledRulesRepository` | compile + inspect (+ findings SoD) | `compiled_rules_infrastructure` | `compiled_rules_repository` |
| `FindingEventRepository` | `findings_application` | `findings_infrastructure` (`FindingEventRepositoryAdapter`) | `finding_events_repository` |
| `DenialAuditPort` | `findings_application` | `findings_infrastructure` (`DenialAuditAdapter` only) | `finding_events_repository` |
| `FindingOpenPort` | `findings_application` | `findings_application` (use-case facade) | n/a — peer port for `inspections_application` |
| `InspectionArtifactPort` | `inspections_application` | `artifacts_infrastructure` | `artifacts_repository` |
| `FindingArtifactPort` | `findings_application` | `artifacts_infrastructure` | `artifacts_repository` |
| `TargetSourcesGateway` | `inspections_application` | `inspections_infrastructure` | `target_sources_gateway` |
| `CertificationArtifactPort` | `certification_tool` / API system capability | `artifacts_infrastructure` | `artifacts_repository` (prod via API; offline local only) |

**ISP hardening:** One physical connection pool MAY back multiple adapters, but
each port MUST be a **separate adapter class** (or narrow façade) so
`compiled_rules_application` cannot call mutating `DirectiveRepository` methods
via a `CompilerReadPort` reference, and `api` cannot call full
`FindingEventRepository` methods via `DenialAuditPort`.

Port method shapes: [`../class/cd_002_application_services.puml`](../class/cd_002_application_services.puml).  
Gate denial path semantics: [`../c4-model/`](../c4-model/README.md) DenialAuditPort + finding-lifecycle SoD contract.

## Module edges vs C4 component edges

- **C4 Component** owns *which peers may call which peers* (product structure).
- **Package** owns *which modules/ports implement that* (code structure).
- Edges in `pkg_connections.puml` must **conform** to the C4 dependency rule; they must not invent new peers.

```
clients → api → *_application → *_repository | *_gateway → *_store | externals
```

## Domain services (not C4 peers)

| Service | Package | Consumers |
|---------|---------|-----------|
| `ResolveConflict` | `conflicts_domain` | compile + inspect application packages |
| `FindingFsm` | `findings_domain` | `findings_application` |
| `CapabilityEnforcer` | shared under `*_interface` | REST/CLI/TUI only |

Shared `conflicts_domain` version across split deployables: [`../deployment/README.md`](../deployment/README.md) Compilation section (ops constraint), C4 non-peers (structural note).

## Related

- [C4 Architecture](../c4-model/README.md) — structural SSoT
- [Class Diagrams](../class/README.md) — types inside packages
- [Deployment](../deployment/README.md) — topology / TLS / RPO
- [Standards / C4 registry](../standards/c4_registry.yaml)
- [Spec contracts](../spec/README.md)
