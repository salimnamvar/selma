# Selma — {Section Title}

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `1.1.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

{One-paragraph purpose: what this section shows and what it must not invent.}
{State exclusive ownership: Answers / Owns 100% / Does not own / Join key — do not restate sibling views' design principles.}

## Role in authority order

| Rank | Source | This section |
| ---: | :--- | :--- |
| 1 | Spec contracts | {reads / implements / visualizes …} |
| 2 | Schema | {if applicable} |
| 3 | C4 | {must use peer IDs only} |
| … | This section | {behavioral / structural view} |

## Catalog

| ID / File | C4 owners | Spec authority |
| :--- | :--- | :--- |
| … | `…_application` | `contracts/…` |

## Conventions

- IDs from `c4_registry.yaml` only
- Diagram headers per [`diagram_header.schema.md`](../standards/diagram_header.schema.md)
- Non-peers labeled explicitly

## Rendering / lint

```bash
# PlantUML or Redocly as applicable
```

## Related

- C4: [`../c4-model/README.md`](../c4-model/README.md)
- Contracts: [`../spec/README.md`](../spec/README.md)
