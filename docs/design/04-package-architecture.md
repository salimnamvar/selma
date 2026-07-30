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
      directives/           # Directives Adapter (executable + policy doctrine)
      cgir/                 # Compiled Rules Adapter
      events/               # Findings & Audit Trail Adapter
      artifacts/            # Snapshots Adapter
    detection/              # DetectionEngine impl, adapter registry
    targets/                # TargetGateway
    auth/                   # CapabilitySource
    hashing/
    clock/
    bootstrap/              # logging, lifespan, config load
  interfaces/
    rest/                   # api component (resource-oriented HTTP)
    cli/
    tui/
  composition/              # DI / wiring only
```

## Package ownership map

| Package | C4 components | Contracts |
| :--- | :--- | :--- |
| `domain.governance` | Directive aggregate | `directive/*` |
| `domain.compilation` | CG-IR models | `compilation/*` |
| `domain.inspection` | Target, InspectionSnapshot | `inspection/*` |
| `domain.finding` | Finding FSM models | `finding_lifecycle/*` |
| `domain.conflict` | ConflictArtifact, ResolveConflict (domain service) | `conflict/*` |
| `domain.authorization` | capability VOs | `authorization/*` |
| `application.use_cases.compilation` | `compilation` | `compilation/*` |
| `application.use_cases.inspection` | `inspection` | `inspection/*` |
| `application.use_cases.finding` | `findings` | `finding_lifecycle/*` |
| `application.use_cases.governance` | directive use cases via `api` | `directive/*` |
| `infrastructure.persistence.directives` | `directives_repository` | C4 `directives` |
| `infrastructure.persistence.cgir` | `compiled_rules_repository` | C4 `compiled_rules` |
| `infrastructure.persistence.events` | `finding_events_repository` | C4 `finding_events` |
| `infrastructure.persistence.artifacts` | `artifacts_repository` | C4 `artifacts` |
| `infrastructure.targets` | `target_sources_gateway` | optional |
| `infrastructure.detection` | supports compilation + inspection | detection_spec |
| `interfaces.*` | `clients` + `api` | `interfaces/*` |

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
# findings component → domain.finding + application.use_cases.finding
# compilation component → domain.compilation + application.use_cases.compilation
# directives_repository → infrastructure.persistence.directives
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
