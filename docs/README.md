# Selma Documentation

| Area | Path | Role |
| :--- | :--- | :--- |
| **Specification contracts** | [`spec/`](spec/README.md) | Normative behavior (`contracts/`) |
| **Schemas** | [`schema/`](schema/) | Rule + policy structure (v1.0.0) |
| **C4 architecture** | [`c4-model/`](c4-model/README.md) | Context / container / component |
| **State machines** | [`state-machine/`](state-machine/README.md) | FSMs and pipelines |
| **Design Freeze** | [`design/`](design/README.md) | DDD, ports, packages, use cases |
| **Use case catalog** | [`usecase/`](usecase/README.md) | Human-facing UC index |
| **Project phases** | [`mindmap/`](mindmap/README.md) | Phase status |

## Authority

1. `spec/contracts/` — what the system MUST do  
2. `schema/` — data shapes  
3. `design/` — how Implementation is structured  
4. `c4-model/` + `state-machine/` — structure and behavior diagrams  

Archives under `spec/ARCHIVE_*` are historical only.

## Implementation

Do not start coding from archives. Start from Design Freeze + contracts.
Gap checklist: [`design/08-implementation-gap-map.md`](design/08-implementation-gap-map.md).
