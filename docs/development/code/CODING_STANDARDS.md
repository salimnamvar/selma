# Selma Coding Standards

**Audience:** humans and agents contributing to Selma  
**Scope:** all of `src/`, `tests/`, `scripts/`, and `docs/` when they prescribe behavior  
**Companion:** pair every change with `directive/rule/*.json` + `directive/policy/*.yaml`

---

## 1. What Selma is

Selma is a **governance platform**, not only a linter.

| Capability | Role |
| :--- | :--- |
| **Directive catalog** | Dataset of paired **rule** (executable) + **policy** (reasoning) |
| **Inspection** | Evaluate source against executable rules |
| **Reasoning / query** | Answer “what is the policy of XYZ?” for agents and humans |
| **Reporting** | Queryable findings + guidance for correction |

Directives under `directive/` are **coding principles we must follow while building Selma**.

---

## 2. Clean Architecture layers

Dependency rule: **inward only**. Outer layers may import inner layers; never the reverse.

```text
interfaces/          Textual TUI, CLI adapters
composition/         DI / wiring only
application/         use cases, ports (async), DTOs
domain/              entities, value objects, aggregates, domain services
infrastructure/      I/O: loaders, validators, parsers, evaluators, reporters
```

| Layer | Owns | Must not own |
| :--- | :--- | :--- |
| **domain** | Meaning of Rule, Policy, Directive, Finding; enums; invariants | File I/O, JSON Schema engines, Textual, paths to `schema/` |
| **application** | Orchestration, ports, DTOs | Concrete YAML/JSON loaders, AST libraries |
| **infrastructure** | Parse, validate documents, map **into** domain | Duplicate domain models |
| **interfaces** | UX / transport | Business rules |
| **composition** | Wire ports → adapters | Domain logic |

### Single sources of truth

| Concern | SSoT |
| :--- | :--- |
| Concept meaning + invariants | `src/selma/domain/` |
| On-disk document shape | `schema/` |
| Directive content (instances) | `directive/` |
| Normative algorithms (future) | `docs/future/spec/SPECIFICATION.md` |

**DRY:** one Python model per concept in **domain**. Infrastructure maps documents → domain; it does not redefine Rule/Policy.

---

## 3. DDD building blocks

| Block | Package | Examples |
| :--- | :--- | :--- |
| Entity | `domain/entities/` | `Rule`, `DirectivePolicy`, `Finding` |
| Aggregate | `domain/aggregates/` | `Directive` (rule + policy), `DirectiveCatalog` |
| Value object | `domain/value_objects/` | `RuleId`, enums, `RuleGuidance`, `Result` |
| Port | `application/ports/` | `DirectiveRepository`, `SourceParser`, `RuleEvaluator`, `FindingReporter` |
| Use case | `application/use_cases/` | `InspectSourceUseCase`, `QueryDirectiveUseCase` |

### Directive model (canonical)

```text
DirectiveCatalog
  └── Directive (lineage_id / Machine ID)
        ├── rule: Rule          # executable — from directive/rule/*.json
        └── policy: Policy?     # reasoning  — from directive/policy/*.yaml
```

- **Inspection / lint** uses `directive.rule` only (policy runtime prohibition).
- **Query / reasoning** uses `directive.policy` (and rule identity/metadata as needed).

---

## 4. Naming (Google + Resource-Oriented Design)

### Packages and modules

- Packages: short, lowercase, singular resource nouns when possible  
  (`directive`, `finding`, `inspection` preferred over vague `utils`, `helpers`, `common`).
- Modules: `snake_case.py`, one primary concept per module.
- Avoid stacking synonyms (`rule_schema_models` when the type is already `Rule`).

### Types and callables

| Kind | Style | Example |
| :--- | :--- | :--- |
| Classes | `PascalCase` | `DirectiveCatalog` |
| Functions / methods | `snake_case` verbs | `find_by_lineage_id` |
| Constants | `UPPER_SNAKE` | `INVALID_RESULT` |
| Private | leading `_` | `_load_rule_file` |
| Boolean locals (doctrine) | `b_continue` | control-flow flag |
| Parameters | `a_` prefix (ST-001) | `a_lineage_id` |

### Resource-oriented design (ROD)

Name APIs after **resources** and **standard verbs**:

| Verb | Meaning | Example |
| :--- | :--- | :--- |
| `get` / `find` | Read one | `find_by_lineage_id` |
| `list` | Read many | `list_active` |
| `create` / `add` | Insert | (authoring, future) |
| `update` / `replace` | Mutate | (authoring, future) |
| `delete` / `remove` | Remove | (authoring, future) |
| `query` | Filtered read / conversation | `query_policy` |
| `inspect` | Evaluate targets | `inspect_paths` |
| `report` | Present findings | `report_findings` |

Prefer `DirectiveRepository.list()` over `RuleLoader.load_everything()`.

---

## 5. Concurrency first (async architecture)

**Default:** async I/O and concurrent inspection.

| Concern | Approach |
| :--- | :--- |
| I/O-bound work | `async` / `await`, `asyncio.TaskGroup` or `gather` |
| CPU-bound AST | `asyncio.to_thread` or process pool (composition chooses) |
| Shared mutable state | forbidden without sync (SC-090 / SC-092) |
| Ports | `async def` on application ports |
| Sync libraries | wrap at infrastructure boundary |

Rules of thumb:

1. Application use cases are `async`.
2. Infrastructure adapters implement async ports (may offload blocking work).
3. Interfaces (Textual / CLI) drive an event loop; no nested `asyncio.run` inside libraries.
4. Prefer structured concurrency (`TaskGroup`) over fire-and-forget tasks.
5. Timeouts are configurable (SC-115); never hardcode infinite waits on external work.

---

## 6. Libraries over hand-rolled code

| Need | Prefer |
| :--- | :--- |
| Models / validation | Pydantic v2 |
| Interactive UX | Textual |
| YAML | PyYAML |
| JSON Schema (structural) | jschon |
| Lint/format of Selma itself | Ruff |
| Types | Pyright strict |

Do not reimplement validation trees, TUI frameworks, or result monads when a maintained library fits.

---

## 7. Universal directives (no project hardcoding)

Rules under `directive/rule/*.json` and policies under `directive/policy/*.yaml`
are **universal standards**. They MUST be written from language patterns and
governance knowledge — never from a single codebase's private names.

| Allowed | Forbidden |
| :--- | :--- |
| Language structure (dunders, generators, properties, `self`/`cls`) | Function-name allowlists (`unwrap`, `list_*`, product APIs) |
| Structural decorator patterns (e.g. schema field validators) | Framework product callouts as special cases (framework X only) |
| Catalogs of known hazardous APIs by semantics (`eval`, `datetime.now`) | Project path, module, or argument name inclusion/exclusion lists |
| Severity / priority / deontic type | “Exclude argument `xyz` because our app uses it” |

When Selma flags correct universal doctrine, **fix the code**. When the rule is
wrong for all languages/projects, **improve the rule/policy pair** — do not add
a one-off name exclusion.

## 8. Safe Coding Doctrine (project self-lint)

Implement and respect directives under `directive/`, especially:

| ID | Intent |
| :--- | :--- |
| SC-001 | Single exit (`b_continue`) |
| SC-002 | Zero `raise` in production paths (use `Result`) |
| SC-003 | Return `Result[T]` |
| SC-004 | No `INVALID_RESULT` as real return |
| SC-011 | `b_continue` pattern |
| SC-024 | Explicit return types |
| SC-070 | No module-level mutable state |
| SC-071 | Deterministic core logic |
| ST-001 | `a_` parameter prefix |

After every subtask:

1. Run Selma / Ruff on touched code.
2. Fix all findings before the next subtask.
3. If a rule is wrong or incomplete for a real pattern, **improve the paired rule + policy** (ask before large policy semantics changes).

---

## 9. Git commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <description>
```

| Type | When |
| :--- | :--- |
| `feat` | New capability |
| `fix` | Bug fix |
| `refactor` | Structure without behavior change intent |
| `docs` | Documentation only |
| `test` | Tests only |
| `chore` | Tooling / deps |

One logical subtask → one commit. Message in complete sentences when the body is needed.

---

## 10. Testing

- Unit tests mirror package layout under `tests/unit/`.
- Domain tests: pure, no I/O.
- Integration tests: real `directive/` + `schema/` when needed.
- Prefer factories for `Rule` / `Directive` over huge fixtures.

---

## 11. Policy runtime prohibition

`directive/policy/*.yaml` and doctrine models **must not** drive inspection evaluation.

- Inspection path: `Rule` only.
- Query / guidance path: `DirectivePolicy` (+ identity from `Rule`).
- Never copy `evaluator_*` fields into policy documents.

---

## 12. Checklist for every PR / agent session

- [ ] Domain concepts live only under `domain/`
- [ ] Infrastructure maps in; does not redefine domain types
- [ ] Ports are async; use cases orchestrate
- [ ] Names follow Google + ROD
- [ ] Directives still paired (rule + policy)
- [ ] Directives stay universal (no project name allowlists)
- [ ] Lint clean on changed paths (critical/high = zero)
- [ ] Conventional commit per subtask
