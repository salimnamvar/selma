# Initial TODO backlog

Prioritized work items for implementers. Check items off in PRs; do not remove
history — mark done with date/PR if desired.

Legend: `P0` blocker · `P1` near-term · `P2` later · `P3` nice-to-have

---

## Configuration & domain mapping

| ID | Pri | Item | Notes |
| :--- | :--- | :--- | :--- |
| B01 | P0 | YAML → `AgentDefinition` mapper | `agents.yaml` |
| B02 | P0 | YAML → `Workflow` mapper | nested steps/tasks/gates |
| B03 | P0 | YAML → `Role` / `PromptTemplate` mappers | roles + prompts |
| B04 | P0 | Config validation CLI | `validate-config` |
| B05 | P1 | Cross-ref validation | agent role_id, prompt_ref, step depends_on |
| B06 | P2 | JSON Schema export for YAML | optional editor support |

## Repositories

| ID | Pri | Item | Notes |
| :--- | :--- | :--- | :--- |
| B10 | P0 | `YamlAgentRepository` | implements protocol |
| B11 | P0 | `YamlWorkflowRepository` | |
| B12 | P0 | `YamlRoleRepository` / `YamlPromptRepository` | |
| B13 | P1 | `FilesystemArtifactRepository` | workspace-safe paths |
| B14 | P1 | `FilesystemWorkflowStateRepository` | resume support |

## Services

| ID | Pri | Item | Notes |
| :--- | :--- | :--- | :--- |
| B20 | P0 | `WorkflowExecutionService` | start/advance/get_state |
| B21 | P0 | `AgentCoordinationService` | dispatch via factory |
| B22 | P1 | `ArtifactManagementService` | register/list |
| B23 | P1 | `ReviewGateService` | evaluate + iterate policy |
| B24 | P2 | Run cancellation | cooperative cancel flag |

## Agent adapters

| ID | Pri | Item | Notes |
| :--- | :--- | :--- | :--- |
| B30 | P0 | `NoOpAgentAdapter` | dry-run / tests |
| B31 | P0 | `AgentFactory` registry | name → class |
| B32 | P1 | Generic `SubprocessAgentAdapter` | parameterized argv |
| B33 | P1 | OpenCode adapter | Coder role |
| B34 | P1 | Poolside adapter | Implementation/refactor |
| B35 | P1 | Mimo adapter | Reviewer |
| B36 | P3 | entry-points plugin discovery | setuptools/importlib |

## CLI & UX

| ID | Pri | Item | Notes |
| :--- | :--- | :--- | :--- |
| B40 | P0 | Wire `run` to execution service | replace NotImplementedError |
| B41 | P0 | Wire `status` | |
| B42 | P1 | Wire `list-agents` | |
| B43 | P1 | Rich progress for steps | optional |
| B44 | P2 | `resume` command | from state dir |

## Quality

| ID | Pri | Item | Notes |
| :--- | :--- | :--- | :--- |
| B50 | P0 | Domain unit tests | models/enums invariants if any |
| B51 | P0 | Service tests with fakes | |
| B52 | P1 | Repository integration tests | tmp_path |
| B53 | P1 | CLI smoke tests | Typer CliRunner |
| B54 | P1 | pyright strict on package | monorepo include |
| B55 | P2 | Path traversal tests | adapters + artifacts |

## Documentation (living)

| ID | Pri | Item | Notes |
| :--- | :--- | :--- | :--- |
| B60 | P1 | Adapter authoring guide | after first real adapter |
| B61 | P2 | Sequence diagrams for run loop | plantuml optional |
| B62 | P2 | Example end-to-end tutorial | |

---

## Suggested first implementation slice (vertical)

1. B30 + B31 (noop + factory)
2. B01–B04, B10–B12 (config load + validate)
3. B20–B21, B40 (engine dry-run + CLI run)
4. Review with Mimo role guidelines before adapters B33–B35
