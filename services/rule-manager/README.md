# Rule Manager Service

Validates and manages rules against the universal rule governance contracts.

## Responsibilities

- Validate policy documents against `policy_doctrine.yaml`
- Validate rules against `rule_schema.json`
- Verify bidirectional traceability between policy and rules
- Enforce contamination guards

## Usage

```bash
cd services/rule-manager
pip install -r requirements.txt

# Validate an example directory
python validate.py <example_dir>

# Validate specific policy and rules files
python validate.py <policy.md> <rules.yaml>
```

## Tests

```bash
cd services/rule-manager
pytest test_validate.py -v
```

## Contract Reference

The contracts this service validates against are defined in `contracts/`:
- `contracts/policy_doctrine.yaml` — The policy contract
- `contracts/rule_schema.json` — The rule schema contract
- `contracts/SPECIFICATION.md` — Full specification
