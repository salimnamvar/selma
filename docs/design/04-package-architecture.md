# 04 — Package Architecture

Target layout for the Selma application. Paths are **design targets** for
Implementation; they describe ownership, not a requirement to rewrite
existing files in this documentation pass.

## Target tree

```
src/selma/
  domain/
    shared/                 # LineageId, Hlc, hashes, errors shared carefully
    governance/             # Directive aggregate, lineage services
    compilation/            # CgIr snapshot model, hash composition types
    inspection/             # Target, InspectionSnapshot, DetectionOutcome
    finding/                # Finding aggregate, FSM, disposition
    conflict/               # ConflictArtifact, resolve_conflict pure service
    authorization/          # Capability value objects (no I/O)
    certification/          # Gate IDs, CertificationRun model
  application/
    ports/                  # All outbound interfaces
    use_cases/
      governance/
      compilation/
      inspection/
      finding/
      conflict/
      guidance/
      certification/
    dto/                    # Request/response models at app boundary
  infrastructure/
    persistence/
      directives/           # Directives Adapter
      cgir/                 # Compiled Rules Adapter
      events/               # Findings & Audit Trail Adapter
      artifacts/            # Snapshots Adapter
    detection/              # DetectionEngine impl, adapter registry
    policy/                 # PolicyDoctrineReader (read-only)
    targets/                # TargetGateway
    auth/                   # CapabilitySource
    hashing/
    clock/
    bootstrap/              # logging, lifespan, config load
  interfaces/
    rest/                   # Application Service HTTP
    cli/
    tui/
  composition/              # DI / wiring only
```

## Package ownership map

| Package | C4 components | Contracts |
| :--- | :--- | :--- |
| `domain.governance` | directives domain | `directive/*` |
| `domain.compilation` | hermetic models | `compilation/*` |
| `domain.inspection` | inspector models | `inspection/*` |
| `domain.finding` | lifecycle_finder models | `finding_lifecycle/*` |
| `domain.conflict` | conflict_resolver models | `conflict/*` |
| `domain.authorization` | capability VOs | `authorization/*` |
| `application.use_cases.*` | application_service orchestration | `interfaces/*` + domain contracts |
| `infrastructure.persistence.*` | `*_adapter` | `data_stores/*` |
| `infrastructure.detection` | supports compiler + inspector | schema detection_spec |
| `infrastructure.policy` | finding_analyzer guidance | policy_doctrine |
| `interfaces.*` | selma_interface + app ingress | `interfaces/*` |

## Dependency rules (enforceable in Implementation)

| From | Allowed to import | Forbidden |
| :--- | :--- | :--- |
| `domain.*` | stdlib + domain siblings (prefer shared kernel) | application, infrastructure, interfaces |
| `application.*` | domain, application.ports, dto | infrastructure, frameworks optional only in dto |
| `infrastructure.*` | domain, application.ports, third parties | interfaces |
| `interfaces.*` | application use cases/dto | domain repositories, infrastructure (except composition) |
| `composition` | all layers for wiring | — |

## Module naming vs C4 IDs

Prefer package names that match ubiquitous language; map to C4 in module docstrings:

```
# lifecycle_finder component → domain.finding + application.use_cases.finding
# finding_fsm_engine contract alias → same packages
```

## Configuration layout (docs)

| Config concern | Location (design) |
| :--- | :--- |
| Rule / policy schema validation | infrastructure bootstrap + schema files under `docs/schema/` |
| Frozen environment pins | compilation provenance |
| Capability role matrix | config projection of `authorization/role_matrix.yaml` |

## What not to put in domain

- FastAPI / SQLAlchemy / HTTP clients
- JSON Schema library calls (application/infrastructure validators)
- File path I/O
- RE2 engine bindings (infrastructure.detection)

Domain may define **pure functions** that infrastructure detection must satisfy (purity AA-03).
