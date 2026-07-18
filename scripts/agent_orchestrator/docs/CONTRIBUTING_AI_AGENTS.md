# Contribution guidelines for AI coding agents

This project is built by a **team of specialized agents**. You are not a solo
developer reinventing the product. Read this file before any edit.

---

## Team model

```text
Architecture Owner (Grok)
        │
        ▼
Primary Implementer (OpenCode) ──► produces code against contracts
        │
        ▼
Refactor / Test / Enhance (Poolside) ──► quality of implementation
        │
        ▼
Independent Reviewer (Mimo) ──► approve / request changes / reject
        │
        ▼
Architecture Owner ──► only when contracts or boundaries conflict
```

| Role | Typical agent | Scope |
| :--- | :--- | :--- |
| Architect | Grok | Contracts, ADRs, boundaries, conflict resolution |
| Coder | OpenCode | Feature implementation behind ports |
| Refactorer | Poolside | Tests, structure, performance, cleanup |
| Reviewer | Mimo | Independent review; **does not own the implementation** |

Detailed duties: `docs/roles/`.

---

## Hard rules (all agents)

1. **Read first:** `docs/architecture.md`, relevant ADR, and target protocol file.
2. **Do not change domain models or protocol signatures** without Architect decision + ADR.
3. **Do not import vendor agent SDKs** into `domain/` or `service/`.
4. **Do not implement “the whole system”** in one pass — work the backlog slice.
5. **Prefer extending existing modules** over new frameworks or layers.
6. **Match monorepo style:** absolute imports (no relative), Google docstrings,
   `a_` parameter prefix where the repo enforces it, double quotes, pathlib.
7. **No drive-by refactors** outside the assigned task.
8. **No secrets** in config examples or logs.
9. **Tests required** for new behavior in domain/service/repository.
10. **Leave the tree runnable:** if you touch CLI, keep `--help` working.

---

## What “done” means for an implementation task

- Protocol implemented or extended as specified
- Types check (pyright/ruff for touched files)
- Tests added or updated
- Example config still valid if schema changed (coordinate with Architect if schema changes)
- Short summary of decisions **that stayed within existing architecture**
- Explicit list of open questions / blockers for Architect if any

---

## What the Reviewer must verify

- Layer dependency direction preserved
- No vendor leakage into core
- Task scope respected (no gold-plating)
- Error types used correctly
- Tests meaningful (not only happy path when failure modes exist)
- Public contracts unchanged unless ADR present

Reviewer output should be structured: decision + findings list.  
Reviewer must **not** silently rewrite the implementation under review.

---

## Conflict resolution

| Conflict | Resolution owner |
| :--- | :--- |
| Two designs both fit protocols | Prefer simpler (KISS); Refactorer may choose |
| Need new protocol method | Architect + ADR |
| Need new domain field | Architect + ADR |
| Adapter needs core change | Challenge first; usually fix adapter |
| Disagreement after review loops exhausted | Architect |

---

## Configuration vs code

| Change type | Where |
| :--- | :--- |
| New agent instance / role binding | YAML config |
| New workflow step | YAML config |
| New vendor integration | New adapter module + factory registration |
| New orchestration behavior | Service (if fits existing ports) or Architect |

If a change can be done in YAML, **do not hardcode it**.

---

## Suggested commit discipline

Use Conventional Commits. Scopes examples:

- `orchestrator` — cross-cutting package
- `orchestrator-domain`
- `orchestrator-service`
- `orchestrator-adapter-opencode`
- `orchestrator-docs`

Examples:

```text
feat(orchestrator-service): implement workflow dry-run execution
fix(orchestrator-repo): validate depends_on references
docs(orchestrator): clarify review gate iteration policy
```

---

## Security baseline for implementers

- Never `shell=True` with unsanitized user input
- Resolve all paths under `workspace_path` before write
- Do not log full prompts if they may contain secrets (redact)
- Adapter subprocess: explicit argv list, timeouts, captured output size limits (Phase 6)

---

## When you are stuck

1. Re-read the protocol and architecture section
2. Check backlog ID and phase exit criteria
3. File an open question in the PR/summary for the Architect
4. Do **not** invent a parallel abstraction “just to unblock”
