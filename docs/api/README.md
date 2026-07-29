# Selma API Contract Specifications

Normative API contracts for the Selma governance system. These specifications
define the HTTP interface between clients and the Selma application service.

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

The API follows ROD principles. Each resource maps to a domain entity with
standard HTTP methods and sub-resource navigation via HATEOAS links.

| Resource Family     | Path Pattern                                       | Methods                    |
|---------------------|----------------------------------------------------|----------------------------|
| Directives          | `/directives/{lineage_id}`                         | GET, PUT, DELETE           |
| Directive Revisions | `/directives/{lineage_id}/revisions/{revision}`    | GET                        |
| Compilations        | `/directives/{lineage_id}/compilations`            | POST, GET                  |
| Inspections         | `/inspections`                                     | POST, GET                  |
| Inspection          | `/inspections/{inspection_id}`                     | GET                        |
| Inspection Findings | `/inspections/{inspection_id}/findings`            | GET                        |
| Findings            | `/findings/{finding_id}`                           | GET, PATCH                 |
| Finding Events      | `/findings/{finding_id}/events`                    | GET                        |
| Finding Guidance    | `/findings/{finding_id}/guidance`                  | GET                        |
| Conflicts           | `/conflicts`                                       | GET                        |
| Conflict Resolutions| `/conflicts/{conflict_id}/resolutions`             | POST                       |
| Certifications      | `/certifications`                                  | POST, GET                  |
| Certification       | `/certifications/{certification_id}`               | GET                        |

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
