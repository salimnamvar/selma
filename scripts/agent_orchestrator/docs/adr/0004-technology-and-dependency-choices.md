# ADR 0004: Technology and dependency choices

## Status

Accepted

## Context

The monorepo targets Python 3.13, pydantic, ruff, pyright, and pytest. Scripts
such as `context_builder` already use Typer and pydantic-settings. The
orchestrator should not introduce a parallel toolchain.

## Decision

| Concern | Choice |
| :--- | :--- |
| Language | Python `>=3.13,<3.14` |
| CLI | Typer |
| Settings | pydantic-settings |
| Validation | Pydantic v2 |
| Config files | YAML via PyYAML |
| Logging | stdlib logging (+ Rich where useful in CLI) |
| Tests | pytest |
| Lint/format | ruff |
| Types | pyright |
| Domain models | dataclasses (align with `context_builder`) |

Domain models intentionally use **dataclasses**, not Pydantic models, to keep
the domain free of validation framework coupling. Infrastructure may use
Pydantic models as DTOs when loading YAML, then map to domain.

## Consequences

**Positive**

- Consistency with selma tooling
- Fast onboarding for agents already used on this repo

**Negative**

- Mapping layer between Pydantic DTOs and dataclasses (acceptable cost)

## Alternatives considered

- **Pydantic domain models everywhere:** convenient but couples domain to framework
- **Click instead of Typer:** diverges from context_builder
- **TOML-only config:** less common for nested workflow graphs than YAML
