# Selma Package Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.1.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

PlantUML package diagrams for Clean Architecture with **`{resource}_{layer}`** modules and nested subpackages (`use_cases` / `ports` / `adapters` / `services`). This section is an **implementation view**: structure and dependencies are drawn on the diagram; behavioral contracts stay in `spec/`. It must **not** invent new product peers, rename C4 IDs, or patch incomplete structure with diagram notes.

## Role in authority order

| Rank | Source | This section |
| ---: | :--- | :--- |
| 1 | Spec contracts | Does not redefine; ports and non-peers point at contracts |
| 2 | Schema | N/A (no schemas owned here) |
| 3 | **C4** ([`../c4-model/`](../c4-model/README.md)) | **Structural SSoT** — every package maps to a peer or is labeled non-peer |
| 4 | Deployment ([`../deployment/`](../deployment/README.md)) | Process topology: v1 single `application` container; stores in data zone |
| — | Package (this dir) | Module layout + dependency rule for implementors |

## Usage

```bash
plantuml docs/package/pkg_001_clean_architecture.puml
plantuml -tsvg docs/package/*.puml
```

## Diagram Index

| ID | File | Description |
|----|------|-------------|
| PKG-001 | [pkg_001_clean_architecture.puml](pkg_001_clean_architecture.puml) | Nested `{resource}_{layer}` packages → subpackages → types; C4 peer tags; ports; stores; cross-app edges |

## Nested package layout (PKG-001)

Every resource package is a **container with subpackages**, not a single flat component:

| Layer package | Required subpackages | Typical contents |
|---------------|----------------------|------------------|
| `*_interface` | `routing` or `commands` / `screens`, `gate` | Routers, `CapabilityEnforcer`, `DenialAuditClient` |
| `*_application` | `use_cases`, `ports` | ROD use cases; owned port interfaces |
| `*_domain` | `aggregates` and/or `services` (plus `shared_domain` id/time) | Aggregates, `FindingFsm`, `ResolveConflict` |
| `*_infrastructure` | `adapters` (+ `evaluators` / `client` / platform slices) | Repository/gateway adapters, `DetectionEvaluator`, HLC/Hasher |
| `composition_root` | `wiring`, `scheduling` | DI, outbox drain schedule |
| stores | one package per C4 `*_store` | Database symbols only (frameworks & drivers) |

Empty packages are non-conformant: if a module exists, show its subpackages and at least one representative type.

## Module naming

| Layer suffix | Responsibility | C4 ring |
|--------------|----------------|---------|
| `*_domain` | Aggregates, pure domain services (`FindingFsm`, `ResolveConflict`) | Domain (not drawn as C4 components) |
| `*_application` | Use cases (ROD operations) + port interfaces | `*_application` components |
| `*_infrastructure` | Repositories, gateways, pure evaluators, platform utils | `*_repository` / `*_gateway` |
| `*_interface` | REST / CLI / TUI + shared `CapabilityEnforcer` | `api` + container `clients` |

## Package ↔ C4 map (canonical)

Aligned with [`../c4-model/README.md`](../c4-model/README.md) "Package alignment" and [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml).

| Package module | C4 entity | Notes |
|----------------|-----------|--------|
| `directives_application` / `directives_domain` | `directives_application` | Domain not a C4 peer |
| `compiled_rules_application` / `compiled_rules_domain` | **`compilation_application`** | Naming dual — see below |
| `compiled_rules_infrastructure` | `compiled_rules_repository` → `compiled_rules_store` | CAS adapter |
| `directives_infrastructure` | `directives_repository` → `directives_store` | Also implements `CompilerReadPort`, `GuidanceReadPort` |
| `inspections_application` / `inspections_domain` | `inspections_application` | |
| `inspections_infrastructure` | `target_sources_gateway` → `target_sources` | Plus pure `DetectionEvaluator` (non-peer) |
| `findings_application` / `findings_domain` | `findings_application` | `FindingFsm` is domain-only |
| `findings_infrastructure` | `finding_events_repository` → `finding_events_store` | Also implements `DenialAuditPort` |
| `artifacts_infrastructure` | `artifacts_repository` → `artifacts_store` | Shared client for inspect / findings / offline cert |
| `rest_interface` / `cli_interface` / `tui_interface` | `api` + `clients` | Capability enforced only at gate |
| `conflicts_domain` (`ResolveConflict`) | **not a C4 peer** | In-process library used by compile + inspect |
| `platform_infrastructure` (Hasher, HLC) | **not a C4 peer** | Supporting utilities |

### Naming dual (intentional)

| Layer | Name | Why |
|-------|------|-----|
| C4 component ID | `compilation_application` | Emphasizes hermetic compile *process* |
| Package prefix | `compiled_rules_application` / `compiled_rules_infrastructure` | Emphasizes the *resource* written (`compiled_rules_store`) |

Do **not** introduce a C4 peer ID `compiled_rules_application`. Do **not** rename packages to `compilation_*` without a `design_contract_version` bump.

Forbidden legacy IDs (must not appear as peers): see `forbidden_ids` in [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml).

## Application ports (ISP)

Ports are owned by application packages; implementers live in infrastructure. Matches C4 "Interface segregation" and [`../class/cd_002_application_services.puml`](../class/cd_002_application_services.puml).

| Port | Owner package | Implementer package | C4 implementer |
|------|---------------|---------------------|----------------|
| `DirectiveRepository` | `directives_application` | `directives_infrastructure` | `directives_repository` |
| `CompilerReadPort` | `compiled_rules_application` (C4: compilation) | `directives_infrastructure` | `directives_repository` |
| `GuidanceReadPort` | `findings_application` | `directives_infrastructure` | `directives_repository` |
| `CompiledRulesRepository` | compile **and** inspect apps (findings reads for SoD) | `compiled_rules_infrastructure` | `compiled_rules_repository` |
| `FindingEventRepository` | `findings_application` | `findings_infrastructure` | `finding_events_repository` |
| `DenialAuditPort` | `findings_application` | `findings_infrastructure` | `finding_events_repository` |
| `InspectionArtifactPort` | `inspections_application` | `artifacts_infrastructure` | `artifacts_repository` |
| `FindingArtifactPort` | `findings_application` | `artifacts_infrastructure` | `artifacts_repository` |
| `TargetSourcesGateway` | `inspections_application` | `inspections_infrastructure` | `target_sources_gateway` |
| `CertificationArtifactPort` | `certification_tool` (offline non-peer) | `artifacts_infrastructure` | may write `artifacts_store` kind=certification |

### DenialAuditPort (gate side-effect)

| Item | Rule |
| :--- | :--- |
| Owner | `findings_application` (application-owned port) |
| Implementer | `findings_infrastructure` / C4 `finding_events_repository` |
| Consumer | `api` / `rest_interface` only (capability gate) |
| Surface | `AppendDenial(...)` only |
| Why not full findings UCs | Avoid circular dependency when the denied action would have entered `findings_application` |
| Normative fields | [`../spec/contracts/finding_lifecycle/sod_contract.yaml`](../spec/contracts/finding_lifecycle/sod_contract.yaml) |

## Cross-application dependencies (from C4 Component diagram)

PKG-001 must reflect these C4 edges (not invent others):

| From | To | Relationship |
|------|-----|--------------|
| `directives_application` | `compilation_application` (`compiled_rules_application`) | `compile_request` outbox (async; same process in v1) |
| `compilation_application` | `directives_repository` | `CompilerReadPort` — short read-lock load of executables |
| `compilation_application` | `compiled_rules_repository` | Publish CG-IR snapshots |
| `inspections_application` | `target_sources_gateway` | Optional remote target pull |
| `inspections_application` | `compiled_rules_repository` | Load frozen compiled rules |
| `inspections_application` | `findings_application` | Open findings after evaluation |
| `inspections_application` | `artifacts_repository` | Inspection snapshots / traces |
| `findings_application` | `finding_events_repository` | Append + hydrate from event stream |
| `findings_application` | `compiled_rules_repository` | Creator provenance for SoD |
| `findings_application` | `directives_repository` | `GuidanceReadPort` — doctrine by `paired_policy_ref` |
| `findings_application` | `artifacts_repository` | Conflict / evidence artifacts |
| `api` | each `*_application` | Resource operations only |
| `api` | `DenialAuditPort` | Capability-denial audit only (drawn as → `finding_events_repository` on C4) |

**Dependency rule (Clean Architecture + C4):**

```
clients → api → *_application → *_repository | *_gateway → *_store | externals
```

Never: `api` → `*_store`; never: repository → use case; never: store → component; never: `api` → arbitrary repository methods beyond `DenialAuditPort.AppendDenial(...)`.

## Domain services (not C4 peers)

| Concern | Package | Consumers |
|---------|---------|-----------|
| `ResolveConflict` | `conflicts_domain` | `compiled_rules_application`, `inspections_application` (in-process) |
| `FindingFsm` (contract alias `finding_fsm_engine`) | `findings_domain` | `findings_application` — all lifecycle transitions and SoD |
| Capability catalog / SoD matrix | enforced at `api` via `CapabilityEnforcer` | Normative: [`../spec/contracts/authorization/`](../spec/contracts/authorization/) |

When compile and inspect **deployables are split**, both MUST load the **same versioned** `conflicts_domain` library artifact from a single release train. Forking a private copy is non-conformant. See [`../deployment/README.md`](../deployment/README.md) "Compilation (hermetic)" and C4 "Not C4 peers".

## Deployment alignment (DEP-001)

| Deploy unit | Package contents |
|-------------|------------------|
| C4 container `application` (v1 single process) | `*_interface` + all `*_application` + all `*_infrastructure` + domain libs + composition/DI + outbox drain |
| Data zone | Four C4 stores only — no application packages |
| External optional | `target_sources` via `inspections_infrastructure` gateway |
| Not deploy peers | `certification_tool`, CI/CD, audit export, remediation ticketing |

**v1 process model:** hermetic compile runs **in-process** with the Application after durable directive writes (outbox drain). Scale-out to a dedicated compile worker is a future option and does **not** change C4 peer IDs or package names.

Production store constraints (owned by deployment/spec, not re-specified here): separate PostgreSQL failure domains for `directives_store` vs `finding_events_store`; S3-compatible CAS for production `compiled_rules_store`.

## Not in core product packages (registry non-peers)

| Concern | Where it lives |
|---------|----------------|
| `certification_tool` (AA-01…AA-08) | Offline/CI; may write `artifacts_store` kind=certification |
| Authorization policy data | Spec contracts + OpenAPI security; enforcement only at `api` |
| Detection engines as freestanding peers | `DetectionEvaluator` under `inspections_infrastructure` only |
| Guidance / analytics engines | Read models inside `findings_application` (`guidance_only`) |
| Governance Contracts Git corpus | Removed; instances only in `directives_store` |

## Dependency notes (PKG-001)

- `rest_interface` → `DenialAuditPort` for capability-denial audit only (not full findings use cases)
- `CapabilityEnforcer` is a **shared library** used by REST/CLI/TUI — not reimplemented per adapter; not a C4 peer
- `findings_infrastructure` implements both `FindingEventRepository` and `DenialAuditPort`
- `compiled_rules_application` and `inspections_application` both depend on `conflicts_domain` for `ResolveConflict` (same versioned library when split across processes)
- `findings_application` depends on `findings_domain.FindingFsm` for all lifecycle transitions and SoD
- `artifacts_infrastructure` implements ports owned by findings and inspections (shared object-store adapter); offline cert uses `CertificationArtifactPort`
- `directives_application` enqueues `compile_request` outbox in the same DB TX as directive mutation; `compiled_rules_application` drains it
- `platform_infrastructure` (Hasher, HybridLogicalClock) supports event append ordering; HLC node state persistence is a deployment concern

## Related Documents

- [C4 Architecture](../c4-model/README.md) — structural SSoT
- [Class Diagrams](../class/README.md) — types and port methods inside packages
- [Deployment](../deployment/README.md) — topology, TLS, RPO/RTO
- [Standards / C4 registry](../standards/c4_registry.yaml)
- [Spec contracts](../spec/README.md)
