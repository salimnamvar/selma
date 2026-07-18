# ADR 0001: Clean Architecture and CSR layering

## Status

Accepted

## Context

Multiple AI agents will implement this system. Without explicit layers, agents
tend to mix CLI, filesystem, and vendor SDKs into “god modules,” making
parallel work unsafe.

The monorepo already uses Clean Architecture patterns (`src/domain`, and
`scripts/context_builder` with controller/service/repository/domain/infrastructure).

## Decision

Adopt Clean Architecture with Controller-Service-Repository boundaries:

| Layer | Allowed to know |
| :--- | :--- |
| Domain | Stdlib + domain only |
| Service | Domain + protocols |
| Repository (ports) | Domain |
| Infrastructure | Domain + external libs; implements ports |
| Controller | Typer + settings + service ports |

Package layout mirrors `scripts/context_builder` for consistency inside selma.

## Consequences

**Positive**

- Clear ownership for specialized agents
- Swappable adapters and repositories
- Testability via fakes

**Negative**

- More files than a single-script tool
- Requires discipline not to “just import YAML in the service”

## Alternatives considered

- **Single module script:** fastest demo; fails multi-agent collaboration
- **Framework-heavy DI container:** premature complexity for a CLI
- **Hexagonal naming only without CSR:** less familiar to this monorepo’s agents
