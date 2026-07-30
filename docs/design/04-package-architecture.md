# 04 — Package Architecture

Target layout for Implementation. Naming follows:

1. **Clean Architecture** — dependencies point inward (interface → application → domain ← infrastructure).
2. **`<name>_<layer>` modules** — resource (or concern) name first, layer second.
3. **Resource-Oriented Design (ROD)** — modules and types are named after resources (`directives`, `findings`, …).

## Naming convention

| Pattern | Rule | Examples |
| :--- | :--- | :--- |
| Package / module | `{resource}_{layer}` snake_case | `directives_domain`, `findings_application` |
| Layer tokens | `domain` \| `application` \| `infrastructure` \| `interface` | — |
| Cross-cutting | `{concern}_{layer}` | `shared_domain`, `authorization_domain` |
| Composition root | `composition` only (no resource prefix) | wires all layers |
| Python import path | `selma.{resource}_{layer}....` | `selma.directives_domain.model` |

**Forbidden:** layer-first trees that hide the resource (`domain/directives` alone is allowed only as *internal* subpackage of `directives_domain`, not as the top-level module name). Prefer **resource_layer** at the top level so every module states *what* and *which CA ring*.

## Target tree

```
src/selma/
  # ── Domain (innermost) ───────────────────────────────────
  shared_domain/                 # LineageId, Hlc, hashes, errors
  directives_domain/             # Directive aggregate, LineageService
  compiled_rules_domain/         # CgIrSnapshot, ControlNode, edges
  inspections_domain/            # Target, InspectionSnapshot, DetectionOutcome
  findings_domain/               # Finding aggregate, FindingFsm, disposition
  conflicts_domain/              # ConflictArtifact, ResolveConflict (pure)
  authorization_domain/          # CapabilityId, ActorCapabilityGrant
  certifications_domain/         # Gate IDs, CertificationRun model

  # ── Application (use cases + ports) ──────────────────────
  directives_application/        # Create/Get/List/Update/Retire/Fork… + ports
  compiled_rules_application/    # CompileDirectives, PublishCompiledRules + ports
  inspections_application/       # CreateInspection, GetInspection + ports
  findings_application/          # Get/List/Acknowledge/Waive… + GetFindingGuidance
  conflicts_application/         # ListConflictArtifacts, ReviewConflictArtifact
  certifications_application/    # RunArchitecturalCertification (offline/CI)
  authorization_application/     # CheckCapability (used by interface)

  # ── Infrastructure (driven adapters) ─────────────────────
  directives_infrastructure/     # SqlDirectiveRepository
  compiled_rules_infrastructure/ # ContentAddressedCompiledRulesRepository
  findings_infrastructure/       # AppendOnlyFindingEventRepository
  artifacts_infrastructure/      # ObjectArtifactRepository (inspections, conflicts, cert)
  inspections_infrastructure/    # HttpTargetSourcesGateway (optional)
  detections_infrastructure/     # DetectionEngine, pattern/structural evaluators
  authorization_infrastructure/  # CapabilitySource
  platform_infrastructure/       # hashing, clock, bootstrap, logging

  # ── Interface (driving adapters) ─────────────────────────
  rest_interface/                # FastAPI resource routers → application
  cli_interface/
  tui_interface/

  composition/                   # DI wiring only
```

## Resource → module map

| Resource (ROD) | Domain module | Application module | Infrastructure module |
| :--- | :--- | :--- | :--- |
| Directives | `directives_domain` | `directives_application` | `directives_infrastructure` |
| Compiled rules | `compiled_rules_domain` | `compiled_rules_application` | `compiled_rules_infrastructure` |
| Inspections | `inspections_domain` | `inspections_application` | `inspections_infrastructure` (+ `artifacts_infrastructure`) |
| Findings | `findings_domain` | `findings_application` | `findings_infrastructure` |
| Conflict artifacts | `conflicts_domain` | `conflicts_application` | `artifacts_infrastructure` |
| Certifications | `certifications_domain` | `certifications_application` | `artifacts_infrastructure` |
| Authorization | `authorization_domain` | `authorization_application` | `authorization_infrastructure` |

## C4 ownership (stable IDs)

| C4 component | Modules |
| :--- | :--- |
| `api` | `rest_interface` + capability checks in `authorization_application` |
| `compilation` | `compiled_rules_application` (+ `directives_application` read path) |
| `inspection` | `inspections_application` |
| `findings` | `findings_application` |
| `directives_repository` | `directives_infrastructure` |
| `compiled_rules_repository` | `compiled_rules_infrastructure` |
| `finding_events_repository` | `findings_infrastructure` |
| `artifacts_repository` | `artifacts_infrastructure` |
| `target_sources_gateway` | `inspections_infrastructure` |

## Dependency rules

| From | May import | Must not import |
| :--- | :--- | :--- |
| `*_domain` | `shared_domain`, stdlib | any `*_application`, `*_infrastructure`, `*_interface` |
| `*_application` | `*_domain`, other `*_application` ports only via interfaces defined in application | `*_infrastructure`, frameworks |
| `*_infrastructure` | `*_domain`, application port interfaces, third parties | `*_interface` |
| `*_interface` | `*_application` use cases + DTOs | `*_domain` repositories, `*_infrastructure` (except via composition) |
| `composition` | all modules for wiring | — |

## Method naming (ROD) — summary

See [05-application-use-cases.md](05-application-use-cases.md) and [03-ports-and-adapters.md](03-ports-and-adapters.md).

| Kind | Pattern | Examples |
| :--- | :--- | :--- |
| Collection read | `List{Resources}` | `ListDirectives`, `ListFindings` |
| Instance read | `Get{Resource}` | `GetDirective`, `GetFinding` |
| Create | `Create{Resource}` | `CreateDirective`, `CreateInspection` |
| Update / lifecycle | Verb + Resource | `UpdateDirective`, `RetireDirective`, `AcknowledgeFinding` |
| Sub-resource | `Get{Resource}{Sub}` | `GetFindingGuidance`, `GetDirectiveExecutableDocument` |
| Ports | same verbs, no silent `find`/`save` | `GetDirective`, `SaveDirective`, `AppendFindingEvent` |

Generic `execute(...)` is **not** the public API name; use cases expose one primary ROD-named method (may still implement an internal `run` if needed).

## Configuration

| Concern | Module |
| :--- | :--- |
| Schema validation bootstrap | `platform_infrastructure` + `docs/schema/` |
| Role → capability matrix | projection of `authorization/role_matrix.yaml` |
| Compile provenance pins | `compiled_rules_application` / domain provenance VOs |

## What not to put in `*_domain`

- FastAPI / SQLAlchemy / HTTP
- JSON Schema library I/O
- Filesystem / RE2 bindings (`detections_infrastructure` only)
