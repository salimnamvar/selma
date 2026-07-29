# UC-I — Inspection

| ID | Use case | Actor | Capability | Stories |
| :--- | :--- | :--- | :--- | :--- |
| UC-I-01 | Submit target for inspection | Compliance | `inspection.submit` | US-IP-001 |
| UC-I-02 | Reinspect target | Compliance | `inspection.reinspect` | US-IP-001 |
| UC-I-03 | View inspection snapshot | either | read | — |
| UC-I-04 | Explain finding causality | either | `finding.view` | US-IP-002 |

**Pipeline:** normalize → classify → select controls → evaluate → aggregate → report.

**Invariant:** evaluation uses CG-IR only; `paired_policy_ref` is carried for later guidance.

**Refs:** `contracts/inspection/*`, `selma_inspection_pipeline.puml`.
