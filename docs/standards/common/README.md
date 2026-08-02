# Clean Architecture diagram palette

**SSoT:** [`ca_palette.puml`](ca_palette.puml)

All structural views (C4, package, class, deployment, state) include this
file and **must not invent hex codes** in diagram bodies.

## Macro (CA layers — identical across views)

| Layer (outer → inner) | Solid | Package/zone fill/border | Used for |
| :--- | :--- | :--- | :--- |
| **Actors** | `#4A6FA5` | `#E8EEF5` / `#4A6FA5` | People, external user zone |
| **Interface** | `#3B7DD8` | `#EEF4FC` / `#3B7DD8` | Driving adapters, clients, REST shell, public edge |
| **Application** | `#1B7A6E` | `#E8F5E9` / `#1B7A6E` | `*_application` use cases, application zone process |
| **Domain** | `#8E44AD` | `#F3E5F5` / `#8E44AD` | Entities, domain services, `*_domain` packages |
| **Infrastructure** | `#B9770E` | `#FEF5E7` / `#B9770E` | Driven adapters `*_repository` / `*_gateway` |
| **Frameworks** | `#2C6E49` | `#E8F5E9` / `#2C6E49` | `*_store`, data zone, durable success |
| **External** | `#8A9199` | `#F0F0F0` / `#8A9199` | `target_sources`, optional externals |
| **Composition** | `#5E35B1` | `#EDE7F6` / `#5E35B1` | Composition root / DI wiring (not a C4 peer) |

Dependency rule still:

```text
actors → interface → application → domain
                  ↘ infrastructure → frameworks | external
```

## Micro (cross-cutting concerns — any view)

| Concern | Solid | When |
| :--- | :--- | :--- |
| **Gate** | `#A93226` | Capability deny, ports, permission edges |
| **Hermetic** | `#B9770E` | Compile-only, pure evaluation (same solid family as infrastructure) |
| **Terminal** | `#4A4A4A` | Lifecycle sinks, retired |
| **Entity** | `#546E7A` | Identity-bearing non-root entities (class micro) |
| **Async / mediated / immutable** | see `ca_palette.puml` | C4 relationship tags only |

## View alias tables

| View | Styles file | Local aliases map to |
| :--- | :--- | :--- |
| C4 | `docs/c4-model/common/c4_styles.puml` | C4 element + rel tags |
| Package | `docs/package/common/pkg_styles.puml` | Layer package rings |
| Class | `docs/class/common/cd_styles.puml` | Layer packages + type archetypes |
| Deployment | `docs/deployment/common/dep_styles.puml` | Zones |
| State | `docs/state/common/state_styles.puml` | `$STATE_COLOR_*` lifecycle micro |

### State micro → CA macro

| `$STATE_COLOR_*` | CA meaning |
| :--- | :--- |
| `ACTOR` | Actors |
| `RESOURCE` | Interface (resource/container) |
| `PROCESS` | Application (in-flight use-case work) |
| `DOMAIN` | Domain |
| `PENDING` | Infrastructure / hermetic (queued, awaits) |
| `STORE` | Frameworks (durable success) |
| `GATE` | Gate |
| `TERMINAL` | Terminal |
| `EXTERNAL` | External |

## Edit policy

1. Change hex only in `ca_palette.puml`.
2. Re-export view aliases if you add new tokens.
3. Run `python scripts/check_design_alignment.py`.
4. Prefer package color strings `$CA_PKG_*` documented values in sections (PlantUML package `#fill/border` may need literal hex — keep literals **equal** to palette).
