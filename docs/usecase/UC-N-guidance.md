# UC-N — Guidance & Analytics

| ID | Use case | Actor | Notes | Stories |
| :--- | :--- | :--- | :--- | :--- |
| UC-N-01 | Resolve guidance for finding/rule | either / AI | `paired_policy_ref` → doctrine | (policy runtime_usage) |
| UC-N-02 | View analytics aggregates | Official | Read-only event projections | US-GA-001 related AA-01 |
| UC-N-03 | Propose directive change from analytics | Official | Mediated feedback via UC-G-02 | AA-01 |

**Forbidden:** analytics or guidance writers mutating CG-IR or FSM.

**Refs:** `policy_doctrine.yaml` runtime_usage, C4 Finding Analyzer, design ports `PolicyDoctrineReader`.
