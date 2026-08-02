# Selma Package Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `1.1.0` · Structural SSoT for **peers:** [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *How* is source code modularized under Clean Architecture? |
| **Owns 100%** | `{resource}_{layer}` packages, use cases, ISP port **ownership**, domain libs, infrastructure adapter classes, composition root, module dependency edges |
| **Does not own** | Peer inventing / Component Rel graph (C4) · zones / TLS / failure domains / RPO (deployment) · FSM tables / locks / capability catalog (spec) · store mutability semantics (spec) |
| **Join key** | C4 peer IDs on package titles only — never redefine them |

PlantUML package diagrams are an **implementation view**. Behavior stays in `spec/`; product structure in `c4-model/`; runtime topology in `deployment/`; FSMs in `state/`.

## Source layout

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

```bash
plantuml docs/package/pkg_001_clean_architecture.puml
```

## Diagram index

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
| `findings_infrastructure` | `finding_events_repository` + `DenialAuditAdapter` (ISP) |
| `artifacts_infrastructure` | `artifacts_repository` |
| `rest_interface` / `cli_interface` / `tui_interface` | `api` + `clients` |
| `conflicts_domain` | not a peer — in-process with compile + inspect |
| `platform_infrastructure` | not a peer |

### Naming dual

| C4 peer ID | Package prefix |
|------------|----------------|
| `compilation_application` | `compiled_rules_application` / `compiled_rules_infrastructure` |

Do not invent C4 peer `compiled_rules_application`. Forbidden: registry `forbidden_c4_peer_ids`.

## Application ports (ISP) — owned here

| Port | Owner package | Implementer package | C4 adapter peer |
|------|---------------|---------------------|-----------------|
| `DirectiveRepository` | `directives_application` | `directives_infrastructure` (`SqlDirectiveWriter`) | `directives_repository` |
| `CompilerReadPort` | `compiled_rules_application` (C4: `compilation_application`) | `directives_infrastructure` (`SqlCompilerReader`) | `directives_repository` |
| `GuidanceReadPort` | `findings_application` | `directives_infrastructure` (`SqlGuidanceReader`) | `directives_repository` |
| `CompiledRulesRepository` | compile + inspect (+ findings SoD) | `compiled_rules_infrastructure` | `compiled_rules_repository` |
| `FindingEventRepository` | `findings_application` | `findings_infrastructure` (`FindingEventRepositoryAdapter`) | `finding_events_repository` |
| `DenialAuditPort` | `findings_application` | `findings_infrastructure` (`DenialAuditAdapter` only) | `finding_events_repository` |
| `FindingOpenPort` | `findings_application` | `findings_application` (`OpenFindings` use-case facade) | n/a — peer port for `inspections_application` |
| `InspectionArtifactPort` | `inspections_application` | `artifacts_infrastructure` | `artifacts_repository` |
| `FindingArtifactPort` | `findings_application` | `artifacts_infrastructure` | `artifacts_repository` |
| `TargetSourcesGateway` | `inspections_application` | `inspections_infrastructure` | `target_sources_gateway` |
| `CertificationArtifactPort` | composition binds offline `certification_tool` | `artifacts_infrastructure` | `artifacts_repository` |

**ISP rule:** one physical pool MAY back multiple adapters; each port MUST be a **separate adapter class** so a `CompilerReadPort` reference cannot mutate directives, and `api` cannot use full `FindingEventRepository` via `DenialAuditPort`.

**Port and use-case method shapes:** [`../class/`](../class/README.md) (CLS-002 owns signatures; this view owns module ownership only).  
Denial-audit **wire path** on Component diagram: [`../c4-model/`](../c4-model/README.md). Normative denial fields: [`../spec/contracts/finding_lifecycle/sod_contract.yaml`](../spec/contracts/finding_lifecycle/sod_contract.yaml).

## Module edges vs C4 component edges

- **C4 Component** owns which **peers** may call which peers.
- **Package** owns which **modules/ports** implement that.
- Edges in `pkg_connections.puml` must **conform** to the C4 dependency rule; they must not invent new peers.

```
clients → api → *_application → *_repository | *_gateway → *_store | externals
```

## Domain services (not C4 peers)

| Service | Package | Consumers |
|---------|---------|-----------|
| `ResolveConflict` | `conflicts_domain` | `compiled_rules_application`, `inspections_application` |
| `FindingFsm` | `findings_domain` | `findings_application` |
| `CapabilityEnforcer` | shared under `*_interface` | REST/CLI/TUI only |

Shared library versioning when compile/inspect deployables split: **ops constraint** in [`../deployment/`](../deployment/README.md); structural non-peer note in C4.

## Related

- [C4 Architecture](../c4-model/README.md) — structural SSoT  
- [Class Diagrams](../class/README.md) — types inside packages  
- [Deployment](../deployment/README.md) — topology / TLS / RPO  
- [State machines](../state/README.md) — FSM visualization  
- [Standards / C4 registry](../standards/c4_registry.yaml) · [View concerns](../standards/view_concerns.md)  
- [Spec contracts](../spec/README.md)
