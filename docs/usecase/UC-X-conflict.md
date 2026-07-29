# UC-X — Conflict Resolution

| ID | Use case | Actor | Stories |
| :--- | :--- | :--- | :--- |
| UC-X-01 | Run conflict detection on CG-IR | Official / System | US-CD-001 |
| UC-X-02 | Apply deterministic precedence | System | US-PR-001 |
| UC-X-03 | Escalate unresolvable / cross-lineage advisory | System → Official | US-CD-001 |

**Precedence:** explicit override → compatible_overrides → priority → specificity → recency.

**Refs:** `contracts/conflict/*`, `selma_conflict_resolution.puml`.
