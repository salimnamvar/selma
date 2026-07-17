# Selma

Domain-agnostic rule governance platform that compiles human-authored directives into executable rules, inspects targets, and manages findings through a full lifecycle with audit trail.

Selma does not: access governance contracts at runtime, modify external remediation systems, or store mutable compiled artifacts.

## Development

Prerequisites: [conda](https://docs.conda.io/) and Python 3.11.

```bash
conda create -n selma python=3.11 -y && conda activate selma
pip install -e ".[dev]"
pytest
```

## Docs

| Path | Description |
| :--- | :--- |
| [docs/spec/](docs/spec/) | Specification, schema, governance doctrine, user stories |
| [docs/c4-model/](docs/c4-model/) | Context, container, and component diagrams |
| [docs/state-machine/](docs/state-machine/) | Canonical FSMs (Finding §3.1 + extracted pipelines), checklist, ADRs |
| [docs/mindmap/](docs/mindmap/) | Project phases and artifact inventory |

## License

Apache-2.0 — see [LICENSE](LICENSE).
