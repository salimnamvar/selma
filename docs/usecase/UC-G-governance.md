# UC-G — Governance Authoring

| ID | Use case | Actor | Capability | Stories |
| :--- | :--- | :--- | :--- | :--- |
| UC-G-01 | Create directive | Official | `directive.create` | US-CP-001 |
| UC-G-02 | Modify directive (revision) | Official | `directive.modify` | US-CP-003 |
| UC-G-03 | Retire directive | Official | `directive.retire` | US-DL-001 |
| UC-G-04 | Fork directive | Official | `directive.fork` | US-ID-001 |
| UC-G-05 | Merge directives | Official | `directive.merge` | US-ID-001 |
| UC-G-06 | Split directive | Official | `directive.fork` | US-ID-001 |
| UC-G-07 | Restore revision | Official | `directive.restore` | US-DL-001 |
| UC-G-08 | View directive / history | Official / Rep | read | US-DS-001, US-ID-001 |

**Success guarantees:** lineage_id stable on revision; compile triggered on publish/identity ops; metadata non-executable.

**Refs:** `contracts/directive/*`, `state-machine/selma_directive_lifecycle.puml`, design use cases Governance.
