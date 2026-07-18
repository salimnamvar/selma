# AI Agent Collaboration Orchestrator

Configuration-driven CLI that coordinates multiple AI coding agents to
collaboratively execute software engineering workflows.

**Status:** Foundation only (architecture, contracts, governance).  
**Not yet implemented:** workflow engine, agent adapters, CLI behavior.

---

## Purpose

Define agents, roles, prompts, workflows, tasks, artifacts, review gates,
and iteration loops in configuration. The engine executes workflows without
code changes when new agents or steps are introduced.

Core system must never hardcode vendor agents (OpenCode, Mimo, Poolside,
Claude, GPT, Gemini). All agents plug in through adapters.

---

## Package layout

```text
agent_orchestrator/
├── controller/          # CLI (Typer) — user I/O only
├── service/             # Application use cases (ports in protocols.py)
├── repository/          # Persistence ports (protocols only at foundation)
├── domain/              # Entities, enums, exceptions (no I/O)
├── infrastructure/      # Settings, agent adapter ports, FS/subprocess later
│   └── agents/          # AgentProtocol + future adapters
├── config/examples/     # Canonical YAML examples
├── docs/                # Architecture, ADRs, roadmap, agent roles
├── tests/               # Test package root (empty at foundation)
├── main.py              # Entry point
└── pyproject.toml       # Package metadata + approved dependencies
```

---

## Layers (Clean Architecture)

| Layer | Responsibility | Depends on |
| :--- | :--- | :--- |
| **Controller** | CLI commands, argument validation, invoke services | Service ports, domain |
| **Service** | Workflow execution, agent coordination, lifecycle | Domain, repository ports, agent port |
| **Repository** | Load agents/workflows, store artifacts | Domain |
| **Domain** | Entities, value objects, enums, domain errors | Nothing |
| **Infrastructure** | Adapters: YAML, FS, subprocess, external agents | Domain ports |

Dependency rule: dependencies point **inward**. Domain has zero framework
imports beyond stdlib typing/dataclasses.

---

## Quick start (after implementation)

```bash
# From monorepo root (planned)
export PYTHONPATH=scripts
python -m agent_orchestrator run --workflow config/examples/workflow.yaml

# Or installed console script (planned)
agent-orchestrator run --workflow path/to/workflow.yaml
```

Foundation CLI currently exposes command surface only; commands raise
`NotImplementedError` until services are implemented.

---

## Documentation map

| Document | Contents |
| :--- | :--- |
| [docs/architecture.md](docs/architecture.md) | System design, boundaries, data flow |
| [docs/dependencies.md](docs/dependencies.md) | Approved stack and non-goals |
| [docs/roadmap.md](docs/roadmap.md) | Phased delivery plan |
| [docs/backlog.md](docs/backlog.md) | Initial TODO backlog |
| [docs/CONTRIBUTING_AI_AGENTS.md](docs/CONTRIBUTING_AI_AGENTS.md) | Rules for AI coding agents |
| [docs/roles/](docs/roles/) | Architect / Coder / Reviewer responsibilities |
| [docs/adr/](docs/adr/) | Architecture Decision Records |

---

## Engineering team model

```text
Grok        → Architecture Owner (foundation + conflict decisions)
OpenCode    → Primary Implementer (Coder role)
Poolside    → Refactoring / Test / Enhancement
Mimo        → Independent Reviewer
Grok        → Architecture decisions when conflicts appear
```

See `docs/roles/` and `docs/CONTRIBUTING_AI_AGENTS.md`.

---

## Principles (non-negotiable)

- Clean Architecture + Controller-Service-Repository
- SOLID, DRY, KISS, SRP, high cohesion / low coupling
- Configuration-driven execution
- Agent = plugin/adapter behind `AgentProtocol`
- Prefer mature libraries; no reinvention of CLI/config/validation/logging
- No premature frameworks or unnecessary abstractions

---

## License

Apache-2.0 — see repository root `LICENSE`.
