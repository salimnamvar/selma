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
| `compiled_rules_*` (compile path) | `compilation_application` + `compiled_rules_repository` → `compiled_rules_store` |
| `inspections_*` | `inspections_application` (+ `target_sources_gateway`) |
| `findings_*` | `findings_application` + `finding_events_repository` → `finding_events_store` |
| `artifacts_infrastructure` | `artifacts_repository` → `artifacts_store` |
| `conflicts_domain` | Domain service (not a C4 component) |
| `rest_interface` / CLI / TUI | `api` + container `clients` |

**Not in core packages:**
- `certifications` — Offline/CI tool suite (separate directory)
- `authorization` — Enforced at `api` gate (cross-cutting concern)
- `detections` — Part of `inspections_application` pipeline

## Related Documents

- [C4 Architecture](../c4-model/README.md)
- [Class Diagrams](../class/README.md)
