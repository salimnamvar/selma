# Selma

Domain-agnostic rule governance platform that compiles human-authored directives into executable rules, inspects targets, and manages findings through a full lifecycle with audit trail.

## What Selma Does

- Compiles directives into immutable, content-addressed rule snapshots (CG-IR)
- Inspects submitted targets against compiled rules
- Manages findings through a 10-state lifecycle with segregation of duties
- Enforces capability-based access control across all operations
- Maintains append-only audit trails for compliance

Selma does not: access governance contracts at runtime, modify external remediation systems, or store mutable compiled artifacts.

## Development

```bash
conda create -n selma python=3.11 -y && conda activate selma
pip install -e ".[dev]"
python scripts/validate_contracts.py
pytest
```

## Docs

| Path | Description |
| :--- | :--- |
| [docs/Regulation/](docs/Regulation/) | Specification, schema, governance doctrine |
| [docs/User-Story/](docs/User-Story/) | 35 user stories across 7 epics |
| [docs/C4-Design/](docs/C4-Design/) | Context, container, and component diagrams |
| [docs/MINDMAP/](docs/MINDMAP/) | Project phases and artifact inventory |

## License

Apache-2.0 — see [LICENSE](LICENSE).
