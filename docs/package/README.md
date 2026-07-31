# Selma Package Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.1.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

PlantUML package diagrams for Clean Architecture with **`{resource}_{layer}`** modules.

## Usage

```bash
plantuml docs/package/pkg_001_clean_architecture.puml
plantuml -tsvg docs/package/*.puml
```

## Diagram Index

| ID | File | Description |
|----|------|-------------|
| PKG-001 | [pkg_001_clean_architecture.puml](pkg_001_clean_architecture.puml) | Resource_layer packages + dependency rule |

## Module naming

| Layer suffix | Responsibility |
|--------------|----------------|
| `*_domain` | Aggregates, pure domain services |
| `*_application` | Use cases (ROD operations) + port interfaces |
| `*_infrastructure` | Repositories, gateways, engines |
| `*_interface` | REST / CLI / TUI driving adapters |

## Alignment with C4

Package structure aligns with C4 entities (layer postfixes):

| Package module | C4 entity |
|----------------|-----------|
| `directives_application` / `directives_domain` | `directives_application` |
| `directives_infrastructure` | `directives_repository` → `directives_store` |
| `compiled_rules_*` (compile path) | **C4 ID `compilation_application`** + `compiled_rules_repository` → `compiled_rules_store` |
| `inspections_*` | `inspections_application` (+ `target_sources_gateway`) |
| `findings_*` | `findings_application` + `finding_events_repository` → `finding_events_store` |
| `DenialAuditPort` (in `findings_application`) | Application-owned port; **implementer** = `finding_events_repository`; **consumer** = `api` / `rest_interface` |
| `artifacts_infrastructure` | `artifacts_repository` → `artifacts_store` |
| `conflicts_domain` (`ResolveConflict`) | Domain service (not a C4 component); depended on by `compiled_rules_application` and `inspections_application` |
| `rest_interface` / CLI / TUI | `api` + container `clients` |

### Naming dual (intentional)

| Layer | Name | Why |
|-------|------|-----|
| C4 component ID | `compilation_application` | Emphasizes hermetic compile *process* |
| Package prefix | `compiled_rules_application` / `compiled_rules_infrastructure` | Emphasizes the *resource* written (`compiled_rules_store`) |

Do not introduce a C4 peer ID `compiled_rules_application`. Do not rename packages to `compilation_*` without a design_contract_version bump.

### Application ports (ISP)

| Port | Owner package | Implementer package |
|------|---------------|---------------------|
| `DirectiveRepository` | `directives_application` | `directives_infrastructure` |
| `CompilerReadPort` | `compiled_rules_application` | `directives_infrastructure` |
| `GuidanceReadPort` | `findings_application` | `directives_infrastructure` |
| `DenialAuditPort` | `findings_application` | `findings_infrastructure` |
| `InspectionArtifactPort` / `FindingArtifactPort` | inspections / findings | `artifacts_infrastructure` (shared client) |

### Dependency notes (PKG-001)

- `rest_interface` → `DenialAuditPort` for capability-denial audit only (not full findings use cases)
- `findings_infrastructure` implements both `FindingEventRepository` and `DenialAuditPort`
- `compiled_rules_application` and `inspections_application` both depend on `conflicts_domain` for `ResolveConflict`
- `artifacts_infrastructure` implements ports owned by both findings and inspections applications (shared object-store adapter)

**Not in core packages:**
- `certification_tool` — Offline/CI tool suite (registry non-peer; may write `artifacts_store`)
- `authorization` — Enforced at `api` gate; catalog in [`../spec/contracts/authorization/`](../spec/contracts/authorization/)
- `detections` — Part of `inspections_application` / `inspections_infrastructure` pipeline

## Related Documents

- [C4 Architecture](../c4-model/README.md)
- [Class Diagrams](../class/README.md)
- [Deployment](../deployment/README.md)
- [Standards / C4 registry](../standards/c4_registry.yaml)
