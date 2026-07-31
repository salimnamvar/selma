# Selma API Contract Specifications

Normative API contracts for the HTTP interface between **Clients** and the
**Application** (`api` gate). Structure aligns with
[`../c4-model/README.md`](../c4-model/README.md) resource-oriented surface.

## Structure

```
docs/api/
├── README.md                              # This index
├── openapi/
│   └── selma-api.yaml                     # OpenAPI 3.0 specification
└── schemas/
    ├── target_submission.json             # JSON Schema: inspection target
    ├── guidance_response.json             # JSON Schema: guidance resolution
    ├── finding_view.json                  # JSON Schema: finding representation
    ├── directive_view.json                # JSON Schema: directive representation
    └── certification_result.json          # JSON Schema: certification result
```

## Resource-Oriented Design

Primary collections match C4 stores / use-case clusters:

| Resource Family     | Path Pattern                                       | Methods                    | C4 owner |
|---------------------|----------------------------------------------------|----------------------------|----------|
| Directives          | `/directives/{lineage_id}`                         | GET, PUT, DELETE           | `directives_store` + `directives_repository` |
| Directive Revisions | `/directives/{lineage_id}/revisions/{revision}`    | GET                        | same |
| Compilations        | `/directives/{lineage_id}/compilations`            | POST, GET                  | `compilation_application` → `compiled_rules_store` |
| Inspections         | `/inspections`                                     | POST, GET                  | `inspections_application` + `artifacts_store` |
| Inspection          | `/inspections/{inspection_id}`                     | GET                        | same |
| Inspection Findings | `/inspections/{inspection_id}/findings`            | GET                        | `findings_application` |
| Findings            | `/findings/{finding_id}`                           | GET, PATCH                 | `findings_application` + `finding_events_store` |
| Finding Events      | `/findings/{finding_id}/events`                    | GET                        | `finding_events_store` |
| Finding Guidance    | `/findings/{finding_id}/guidance`                  | GET                        | `findings_application` + doctrine via `directives_repository` |
| Artifacts           | `/artifacts` (as exposed)                          | GET                        | `artifacts_store` |
| Conflicts           | `/conflicts`                                       | GET                    | `findings_application` (via `ResolveConflict` domain service) |
| Conflict Resolutions| `/conflicts/{conflict_id}/resolutions`             | POST                   | same |
| Certifications      | `/certifications`                                  | POST, GET              | `api` (delegates to external CI tool suite) |
| Certification       | `/certifications/{certification_id}`               | GET                    | same |

## Authentication

All endpoints require Bearer token authentication. Tokens encode actor identity
and capability set. Capability checks are enforced per the authorization contract
(`docs/spec/contracts/authorization/capabilities.yaml`).

## Error Model

All errors return a uniform JSON envelope:

```json
{
  "error": {
    "code": "CapabilityDenied",
    "message": "Actor lacks required capability: finding.waive",
    "details": { ... },
    "request_id": "req_abc123"
  }
}
```

Standard HTTP status codes: 400 (SchemaError), 401 (Unauthorized),
403 (CapabilityDenied), 404 (NotFound), 409 (Conflict).

## Normative References

- Directive lifecycle: `docs/spec/contracts/directive/lifecycle.yaml`
- Finding FSM states: `docs/spec/contracts/finding_lifecycle/states.yaml`
- Finding transitions: `docs/spec/contracts/finding_lifecycle/transitions.yaml`
- Finding schema: `docs/spec/contracts/inspection/finding_contract.yaml`
- Certification gates: `docs/spec/contracts/certification/gates.yaml`
- Conflict detection: `docs/spec/contracts/conflict/detection.yaml`
- REST API behavior: `docs/spec/contracts/interfaces/rest_api.yaml`
