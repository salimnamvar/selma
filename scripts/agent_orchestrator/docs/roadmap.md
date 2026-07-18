# Development roadmap

Phased delivery so specialized AI agents can implement without redesigning.

---

## Phase 0 — Foundation (COMPLETE)

Owner: Architecture (Grok)

- [x] Repository package structure
- [x] Domain models, enums, exceptions
- [x] Ports: agent, repository, service
- [x] Settings skeleton + example YAML
- [x] CLI command surface (stubs)
- [x] Architecture docs, ADRs, roles, backlog
- [x] Contribution guidelines for AI agents

**Exit criteria:** Implementers can code against protocols without architecture questions.

---

## Phase 1 — Configuration load path

Owner: Coder (OpenCode) + Review (Mimo)

- [ ] Pydantic (or equivalent) schema for YAML files
- [ ] YAML repositories implementing repository protocols
- [ ] `validate-config` CLI command
- [ ] Unit tests for mapping YAML → domain
- [ ] Error messages for missing/invalid config

**Exit criteria:** Example configs under `config/examples/` validate cleanly.

---

## Phase 2 — Workflow engine (in-process)

Owner: Coder (OpenCode)

- [ ] `WorkflowExecutionService` implementing the service port
- [ ] Linear + `depends_on` step scheduling (keep simple; no distributed queue)
- [ ] Workflow state repository (JSON/YAML on disk)
- [ ] `run` and `status` CLI commands
- [ ] Fake/no-op agent adapter for dry runs

**Exit criteria:** Dry-run workflow walks all steps with fake agent.

---

## Phase 3 — Artifact management

Owner: Coder + Refactorer (Poolside)

- [ ] Artifact repository (filesystem layout under `.orchestrator/artifacts`)
- [ ] Register outputs from `ExecutionResult`
- [ ] Pass input artifacts into `ExecutionContext`
- [ ] Tests for path safety (no escape from workspace)

**Exit criteria:** Artifacts round-trip across steps in dry-run.

---

## Phase 4 — Review gates and iteration loops

Owner: Coder + Reviewer role design

- [ ] `ReviewGateService`
- [ ] Map review agent result → `ReviewResult` / `ReviewDecision`
- [ ] Iteration counters + `max_iterations` enforcement
- [ ] `on_reject` re-queue policy (minimal: re-run step id)

**Exit criteria:** Example workflow can REQUEST_CHANGES then APPROVE with fake agents.

---

## Phase 5 — First real agent adapters

Owner: Implementation specialists

Priority order (suggested):

1. Subprocess-based generic CLI adapter (parameterized)
2. OpenCode adapter
3. Poolside adapter
4. Mimo adapter

Each adapter:

- Implements `AgentProtocol`
- Registers with `AgentFactory`
- Has isolated unit tests (mocked subprocess)
- Documents required binaries/env in adapter module docstring

**Exit criteria:** One real end-to-end run on a sample task in a sandbox workspace.

---

## Phase 6 — Hardening

Owner: Poolside (refactor/test) + Mimo (review)

- [ ] Structured logging throughout
- [ ] Rich status output for long runs
- [ ] Cancellation / resume from state
- [ ] Coverage gates for domain + service
- [ ] pyright clean for package
- [ ] Security review: path traversal, command injection in adapters

---

## Phase 7 — Extension (later)

- Multiple workflows per file / workflow library
- Parallel steps where `depends_on` allows
- Plugin entry points (`importlib.metadata`) for third-party adapters
- Optional metrics export

Do not start Phase 7 before Phase 6 exit criteria.

---

## Dependency between phases

```text
0 Foundation
    → 1 Config load
        → 2 Engine + fake agent
            → 3 Artifacts
                → 4 Review gates
                    → 5 Real adapters
                        → 6 Hardening
                            → 7 Extensions
```

Phases 3 and 4 may partially overlap after Phase 2 if interfaces stay stable.
