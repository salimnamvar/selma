# Clean Architecture diagram palette

**SSoT:** [`ca_palette.puml`](ca_palette.puml)

All structural views (C4, package, class, deployment, state) include this
file and **must not invent hex codes** in diagram bodies.

## MACRO — CA layers (high-contrast hues)

Layers use **different hue families** (not tints of the same green/blue) so
rings stay distinct when several layers appear on one diagram.

| Layer (outer → inner) | Solid | Fill / border | Hue family | Used for |
| :--- | :--- | :--- | :--- | :--- |
| **Actors** | `#3F51B5` | `#E8EAF6` / `#3F51B5` | Indigo | People, external user zone |
| **Interface** | `#0288D1` | `#E1F5FE` / `#0288D1` | Sky cyan-blue | Driving adapters, clients, REST, public edge |
| **Application** | `#00897B` | `#E0F2F1` / `#00897B` | Teal | `*_application` use cases, app process zone |
| **Domain** | `#7B1FA2` | `#F3E5F5` / `#7B1FA2` | Violet | Entities, domain services, `*_domain` |
| **Infrastructure** | `#EF6C00` | `#FFF3E0` / `#EF6C00` | Vivid orange | Driven adapters `*_repository` / `*_gateway` |
| **Frameworks** | `#2E7D32` | `#E8F5E9` / `#2E7D32` | Forest green | `*_store`, data zone, durable success |
| **External** | `#607D8B` | `#ECEFF1` / `#607D8B` | Blue-grey | `target_sources`, optional externals |
| **Composition** | `#283593` | `#E8EAF6` / `#283593` | Deep indigo | Composition root / DI (not a C4 peer) |

```text
actors → interface → application → domain
                  ↘ infrastructure → frameworks | external
```

### Why these hues

| Collision avoided | How |
| :--- | :--- |
| Application vs Frameworks | Teal vs forest green (was both “green”) |
| Domain vs Composition | Violet `#7B1FA2` vs deep indigo `#283593` |
| Infrastructure vs Hermetic | Orange `#EF6C00` vs gold `#F9A825` |
| Interface vs Actors | Sky blue vs indigo |
| Gate vs Domain | Crimson vs violet |

## MICRO — cross-cutting concerns

| Concern | Solid | Fill | When |
| :--- | :--- | :--- | :--- |
| **Gate** | `#C62828` | `#FFEBEE` | Capability deny, ports, permission edges |
| **Hermetic** | `#F9A825` | `#FFFDE7` | Compile-only, pure evaluation, domain events |
| **Terminal** | `#37474F` | `#ECEFF1` | Lifecycle sinks, retired |
| **Entity** | `#546E7A` | `#ECEFF1` | Non-root entities (class) |
| **Async / mediated / immutable** | see `ca_palette.puml` | — | C4 relationship tags |

## View alias tables

| View | Styles file | Local aliases map to |
| :--- | :--- | :--- |
| C4 | `docs/c4-model/common/c4_styles.puml` | C4 element + rel tags |
| Package | `docs/package/common/pkg_styles.puml` | Layer package rings |
| Class | `docs/class/common/cd_styles.puml` | Layer packages + type archetypes |
| Deployment | `docs/deployment/common/dep_styles.puml` | Zones |
| State | `docs/state/common/state_styles.puml` | `$STATE_COLOR_*` lifecycle micro |

### State micro → CA macro

| `$STATE_COLOR_*` | CA meaning | Solid |
| :--- | :--- | :--- |
| `ACTOR` | Actors | `#3F51B5` |
| `RESOURCE` | Interface | `#0288D1` |
| `PROCESS` | Application | `#00897B` |
| `DOMAIN` | Domain | `#7B1FA2` |
| `PENDING` | Infrastructure | `#EF6C00` |
| `STORE` | Frameworks | `#2E7D32` |
| `GATE` | Gate | `#C62828` |
| `TERMINAL` | Terminal | `#37474F` |
| `EXTERNAL` | External | `#607D8B` |

## Edit policy

1. Change hex only in `ca_palette.puml`.
2. Re-export view aliases if you add new tokens.
3. Keep package/section `#fill/border` **literals equal** to palette `$CA_PKG_*` values.
4. Run `python scripts/check_design_alignment.py`.
