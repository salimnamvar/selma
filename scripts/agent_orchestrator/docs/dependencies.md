# Dependency selection

Approved stack for the Agent Collaboration Orchestrator.  
Do not add runtime dependencies without an ADR or Architect approval.

---

## Runtime

| Library | Version floor | Purpose | Replaces reinventing |
| :--- | :--- | :--- | :--- |
| Python | `>=3.13,<3.14` | Language | — |
| pydantic | `>=2` | Validation / structured data | Custom validators |
| pydantic-settings | `>=2` | Env + settings | ad-hoc `os.environ` |
| typer | `>=0.12` | CLI | argparse boilerplate |
| rich | `>=13` | Readable CLI/logging output | custom color/format |
| PyYAML | `>=6` | Config load/dump | custom YAML parser |

## Development

| Library | Purpose |
| :--- | :--- |
| pytest | Tests |
| pytest-cov | Coverage |
| ruff | Lint + format |
| pyright | Static types (strict mode preferred) |

---

## Explicitly out of scope (do not add casually)

| Temptation | Why not |
| :--- | :--- |
| Celery / Airflow / Prefect | Overkill; this is a local CLI orchestrator first |
| SQLAlchemy / DB | Filesystem + YAML state is enough initially |
| Custom HTTP agent bus | Adapters wrap existing CLIs/APIs |
| langchain / llama-index | Core must stay vendor-neutral |
| click (instead of Typer) | Typer is the project standard |
| mypy **and** pyright | Prefer pyright to match monorepo unless ADR says otherwise |
| loguru | stdlib logging + Rich handlers is enough |

---

## Logging

- Use **stdlib `logging`**
- Optional Rich `RichHandler` in controller/bootstrap only
- Domain and services log via injected logger or module logger — no `print` in non-CLI layers

---

## Monorepo note

Root `selma/pyproject.toml` currently owns the main package. This package’s
`scripts/agent_orchestrator/pyproject.toml` records the **approved dependency
set**. When wiring into the monorepo:

1. Add runtime deps to root `dependencies` or an optional extra `orchestrator`
2. Ensure `PYTHONPATH` includes `scripts` for imports
3. Extend ruff/pyright `include`/`src` if type-checking this package strictly

Do not fork packaging strategy mid-implementation without an ADR.
