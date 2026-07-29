# UC-A — Authorization & SoD

| ID | Use case | Actor | Stories |
| :--- | :--- | :--- | :--- |
| UC-A-01 | Enforce capability at ingress / FSM / compile gates | System | US-CA-001 |
| UC-A-02 | Deny waive when actor in creator_provenance | System | US-SD-001 |
| UC-A-03 | Deny approve when actor submitted evidence | System | US-SD-002 |
| UC-A-04 | Apply role matrix for Official vs Compliance | System | US-RM-001 |

**On denial:** `403 CapabilityDenied`, audit event, **no** partial mutation.

**Refs:** `contracts/authorization/*`, `finding_lifecycle/sod_contract.yaml`, `selma_authorization.puml`.
