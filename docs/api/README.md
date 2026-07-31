# Selma API

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.1.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

OpenAPI design for the HTTP interface between **Clients** and the **Application**
(`api` gate). Structure follows the same resource-grouped, Redocly-friendly
layout used for multi-file OpenAPI (paths by resource, shared components).

**Entry point:** [`openapi.yaml`](openapi.yaml)  
**Structural SSoT:** [`../c4-model/`](../c4-model/README.md) (Contract 1.1.0)  
**Behavioral SSoT:** [`../spec/contracts/`](../spec/contracts/)

## Layout

```text
docs/api/
├── openapi.yaml                 # Root document (info, tags, path $refs, component $refs)
├── redocly.yaml                 # Redocly CLI config (recommended ruleset)
├── .redocly.lint-ignore.yaml    # Documented lint suppressions
├── README.md                    # This file
├── paths/                       # Path Item Objects grouped by resource
│   ├── directives.yaml          # R1 Directive
│   ├── compilations.yaml        # R2 Compilation (nested under directives)
│   ├── inspections.yaml         # R3 Inspection
│   ├── findings.yaml            # R4 Finding (+ events, guidance)
│   └── artifacts.yaml           # R5 Artifact (+ conflict resolution)
├── components/
│   ├── parameters.yaml          # Shared path/query parameters
│   ├── responses.yaml           # Shared error responses
│   ├── schemas.yaml             # Wire schemas (+ $ref to JSON Schema files)
│   └── security.yaml            # BearerAuth
└── schemas/                     # JSON Schema for primary resource views
    ├── directive_view.json
    ├── finding_view.json
    ├── guidance_response.json
    ├── target_submission.json
    └── certification_result.json
```

## Resources (C4-aligned)

| # | Resource | Paths | C4 owner |
|---|----------|-------|----------|
| R1 | Directive | `/directives/{lineage_id}`, `…/revisions/{revision}` | `directives_application` |
| R2 | Compilation | `/directives/{lineage_id}/compilations` | `compilation_application` |
| R3 | Inspection | `/inspections`, `/inspections/{inspection_id}` | `inspections_application` |
| R4 | Finding | `/findings/{finding_id}`, `…/events`, `…/guidance` | `findings_application` |
| R5 | Artifact | `/artifacts`, `/artifacts/{artifact_id}`, `…/resolutions` | `artifacts_repository` |

### Not freestanding peers

| Concern | Exposure |
| :--- | :--- |
| Conflict detection | Domain `ResolveConflict` during compile/inspect; conflict **artifacts** under R5 |
| Human conflict resolve | `POST /artifacts/{id}/resolutions` (`conflict.resolve`) |
| Guidance / aggregates | R4 guidance sub-resource + findings read models (`analytics.view`) |
| Certification AA-01…AA-07 | Offline/CI `certification_tool`; results as artifacts `kind=certification` |

## Conventions

- **operationId:** semantic `verbNoun` (`getDirective`, `createInspection`, `listFindingEvents`)
- **Parameters / responses / schemas:** named components under `components/` (PascalCase keys)
- **JSON Schema views:** primary wire types in `schemas/` referenced from `components/schemas.yaml`
- **Errors:** uniform `Error` envelope; shared responses `Unauthorized`, `CapabilityDenied`, `NotFound`, `SchemaError`, `Conflict`, `FsmError`
- **Pagination:** `page_size` / `page_token` on list operations

## Lint & preview

```bash
# From docs/api (requires @redocly/cli)
npx @redocly/cli lint openapi.yaml
npx @redocly/cli preview-docs openapi.yaml

# Bundle to a single file if needed
npx @redocly/cli bundle openapi.yaml -o /tmp/selma-api.bundle.yaml
```

## Normative references

| Topic | Contract |
| :--- | :--- |
| Directive lifecycle | `docs/spec/contracts/directive/` |
| Compilation | `docs/spec/contracts/compilation/` |
| Inspection | `docs/spec/contracts/inspection/` |
| Finding FSM | `docs/spec/contracts/finding_lifecycle/` |
| Authorization | `docs/spec/contracts/authorization/` |
| REST behavior | `docs/spec/contracts/interfaces/rest_api.yaml` |
| Certification gates | `docs/spec/contracts/certification/gates.yaml` |
| Stores | `docs/spec/contracts/data_stores/` |

## Cross-cutting headers

| Header | Use |
|--------|-----|
| `Authorization: Bearer` | JWT authN (required) |
| `Idempotency-Key` | Safe retries on mutating POSTs |
| `If-Match` | Directive optimistic concurrency (ETag) |

See `components/security.yaml` and `spec/contracts/interfaces/rest_api.yaml`.
