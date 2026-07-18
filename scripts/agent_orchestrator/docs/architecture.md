# Architecture — AI Agent Collaboration Orchestrator

**Audience:** implementers (human or AI) who must not invent architecture.  
**Status:** Foundation approved. Implementation follows this document + ADRs.

---

## 1. Problem statement

Software teams increasingly use multiple AI coding agents. Without coordination:

- agents overwrite each other’s work
- roles blur (reviewer implements; coder redesigns)
- workflows live in chat history, not versioned config
- vendor lock-in creeps into core logic

This project provides a **configuration-driven orchestration framework** that
assigns agents to roles, runs ordered workflows, enforces review gates, and
stores artifacts — independent of any single agent vendor.

---

## 2. Goals and non-goals

### Goals

- Define agents, roles, prompts, workflows, tasks, artifacts, review gates, loops
- Execute workflows from YAML without code changes for new steps/agents
- Isolate vendors behind `AgentProtocol`
- Clean Architecture + Controller-Service-Repository
- Production-grade typing, packaging, logging, testing standards

### Non-goals (foundation and near-term)

- Building a general DAG workflow SaaS
- Replacing CI/CD systems
- Implementing full multi-tenant auth
- Embedding LLM SDKs in the core
- Auto-discovering agents on the network
- GUI / web UI

---

## 3. Architectural principles

| Principle | Application here |
| :--- | :--- |
| Clean Architecture | Domain at center; infrastructure at edges |
| CSR | Controller → Service → Repository |
| Dependency inversion | Services depend on protocols, not YAML/FS/CLI vendors |
| SOLID / SRP | One reason to change per module |
| KISS / DRY | Prefer Typer, Pydantic, PyYAML over custom parsers |
| Explicit boundaries | No domain imports of Typer/Rich/subprocess |

---

## 4. Logical layers

```text
┌─────────────────────────────────────────────────────────────┐
│ Controller (Typer CLI)                                      │
│  - parse args, validate user input, print results           │
└────────────────────────────┬────────────────────────────────┘
                             │ uses
┌────────────────────────────▼────────────────────────────────┐
│ Service (application use cases)                             │
│  - WorkflowExecution, AgentCoordination, Artifacts, Reviews │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
    ┌───────────▼───────────┐     ┌───────────▼───────────────┐
    │ Repository ports      │     │ AgentProtocol             │
    │ agents/workflows/     │     │ (adapter plugins)         │
    │ artifacts/state       │     │                           │
    └───────────┬───────────┘     └───────────┬───────────────┘
                │                             │
┌───────────────▼─────────────────────────────▼───────────────┐
│ Infrastructure                                              │
│  YAML loaders, FS, subprocess, OpenCode/Mimo/Poolside/...   │
└─────────────────────────────────────────────────────────────┘
                             │ maps to/from
┌────────────────────────────▼────────────────────────────────┐
│ Domain                                                      │
│  AgentDefinition, Role, Task, Workflow, Artifact,           │
│  ReviewResult, WorkflowState, ExecutionResult, enums, errors│
└─────────────────────────────────────────────────────────────┘
```

### Layer rules

1. **Domain** — pure data + domain exceptions. No I/O. No Typer/Pydantic Settings.
2. **Service** — orchestration logic; inject ports via constructor.
3. **Repository** — load/save domain objects; no agent execution.
4. **Infrastructure** — implement ports; may use PyYAML, pathlib, subprocess.
5. **Controller** — thin; map CLI → settings → service calls → user output.

---

## 5. Domain model (summary)

| Type | Role |
| :--- | :--- |
| `Role` | Responsibility catalog entry |
| `AgentDefinition` | Config binding: id → adapter + role + prompt |
| `PromptTemplate` | Reusable prompt content |
| `Task` | Unit of work for one agent |
| `ReviewGate` | Quality gate + iteration policy |
| `WorkflowStep` | Task and/or gate with dependencies |
| `Workflow` | Ordered/dependency-aware step collection |
| `Artifact` | Durable output (design, source, review, …) |
| `ReviewResult` | Gate decision + findings |
| `WorkflowState` | Runtime run state |
| `ExecutionContext` | Input to `AgentProtocol.execute` |
| `ExecutionResult` | Output from `AgentProtocol.execute` |

Full field contracts: `domain/models.py`, `domain/enums.py`.

---

## 6. Agent adapter model

```text
Core ──execute(task, context)──► AgentProtocol
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
        OpenCodeAdapter         MimoAdapter           PoolsideAdapter
        (future)                (future)              (future)
```

Rules:

- Core imports **only** `AgentProtocol` / `AgentFactoryProtocol`
- Adapter name in YAML (`adapter: mimo`) is a **registry key**, not an import path in domain
- Adapters own vendor CLI flags, env vars, and error mapping
- Prefer returning `ExecutionResult(success=False, …)` for agent failures; raise for misconfiguration

See [ADR 0002](adr/0002-agent-adapter-plugin-model.md).

---

## 7. Configuration model

Canonical files (under `config/` or `--config-dir`):

| File | Contents |
| :--- | :--- |
| `agents.yaml` | Agent registry |
| `roles.yaml` | Role catalog |
| `workflow.yaml` | Workflow definition(s) |
| `prompts.yaml` | Prompt templates |

Examples: `config/examples/`.

Settings: `OrchestratorSettings` (`AO_*` env prefix) for paths and log level.

Loading path (planned):

```text
YAML → infrastructure repository → domain models → service
```

Validation: Pydantic models in infrastructure **or** domain constructors + explicit validators — choose one approach in Phase 1 and document in code; do not dual-validate inconsistently.

---

## 8. Runtime flow (target)

1. CLI `run` loads settings + config dir
2. Repositories materialize `Workflow`, agents, roles, prompts
3. Service creates `WorkflowState` (run id), persists it
4. For each eligible step:
   - Build `Task` + `ExecutionContext`
   - Resolve agent via factory
   - `agent.execute(task, context)` → `ExecutionResult`
   - Register artifacts
   - If review gate: dispatch review task → `ReviewResult`
   - If `REQUEST_CHANGES` and iterations remain: re-run producing step
   - Else advance or fail
5. Terminal step → `WorkflowStatus.COMPLETED`

---

## 9. Package layout

```text
scripts/agent_orchestrator/
  controller/cli.py          # Typer surface (stubs)
  service/protocols.py       # Use-case ports
  repository/protocols.py    # Persistence ports
  domain/                    # Models, enums, exceptions
  infrastructure/
    config.py                # Pydantic Settings
    agents/protocol.py       # AgentProtocol
  config/examples/           # Reference YAML
  docs/                      # This document + ADRs + governance
  main.py
  pyproject.toml
```

Monorepo import pattern (same as `context_builder`):

```bash
export PYTHONPATH=scripts
python -m agent_orchestrator --help
```

---

## 10. Error model

All failures use typed exceptions under `domain/exceptions.py` with stable
`reason` codes. Controllers catch `OrchestratorError` and print user-facing
messages; do not leak stack traces by default (log them at DEBUG/ERROR).

---

## 11. Testing strategy (planned)

| Layer | Style |
| :--- | :--- |
| Domain | Pure unit tests, no I/O |
| Service | Unit tests with fake repositories + fake agents |
| Repository | Integration tests against temp YAML/FS |
| Adapters | Optional integration tests behind markers |
| CLI | Typer CliRunner smoke tests |

Foundation does not include test implementations beyond package placeholders.

---

## 12. What implementers may change freely

- Concrete service/repository/adapter code behind protocols
- Test fixtures and helpers
- Log message wording
- Internal private helpers (`_foo`)

## What implementers must not change without Architect / ADR

- Domain model field names and semantics
- Protocol method signatures
- Layer dependency direction
- Introduction of vendor imports into domain/service
- New top-level architectural layers

---

## 13. Related documents

- [dependencies.md](dependencies.md)
- [roadmap.md](roadmap.md)
- [backlog.md](backlog.md)
- [CONTRIBUTING_AI_AGENTS.md](CONTRIBUTING_AI_AGENTS.md)
- [roles/](roles/)
- [adr/](adr/)
