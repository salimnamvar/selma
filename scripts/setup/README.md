# Setup

Environment provisioning for software-design.

## Quick start

```bash
bash scripts/setup/setup_env.sh
```

Reads `pyproject.toml` automatically.

## What it does

1. Ensures Miniconda is available (installs if missing and allowed).
2. Creates/updates the conda environment (name derived from project name → `software-design`).
3. `pip install -e ".[dev]"`.
4. Generates `.vscode/` settings for the correct interpreter + terminal profile.
5. Verifies the environment.

## Flags

```bash
bash scripts/setup/setup_env.sh --dry-run
bash scripts/setup/setup_env.sh --steps conda,env,python,vscode,verify
bash scripts/setup/setup_env.sh --steps cicd   # also runs quality gates
```

## Machine overrides

```bash
cp scripts/setup/environment.local.sh.example scripts/setup/environment.local.sh
# edit then run setup again
```

`environment.local.sh` is git-ignored.

## Files

- `setup_env.sh` — orchestrator
- `environment.local.sh.example`
- `lib/*.sh` — implementations (common, pyproject, conda, python, vscode, verify, cicd)
