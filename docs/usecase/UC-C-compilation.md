# UC-C — Compilation

| ID | Use case | Actor | Notes | Stories |
| :--- | :--- | :--- | :--- | :--- |
| UC-C-01 | Compile directive graph → CG-IR | System | Hermetic pipeline stages | US-CP-001 |
| UC-C-02 | Validate rule dataset | Official / System | Discriminator + complexity + portability | US-CP-002 |
| UC-C-03 | Incremental reuse compile | System | Dirty subgraph only | US-CP-003 |

**Forbidden:** loading policy doctrine for evaluation; non-RE2 regex; non-UTC timestamps.

**Refs:** `contracts/compilation/*`, `selma_compilation_pipeline.puml`, `selma_cgir_hash_chain.puml`.
