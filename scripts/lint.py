"""Lint script for pre-commit hook. Runs ruff and AST rules."""

import subprocess
import sys


def main() -> int:
    """Run all lint checks."""
    errors = []

    # Run ruff check
    result = subprocess.run(
        ["python", "-m", "ruff", "check", "src/", "tests/"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append(result.stdout)
        errors.append(result.stderr)

    # Run ruff format check
    result = subprocess.run(
        ["python", "-m", "ruff", "format", "--check", "src/", "tests/"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append(result.stdout)
        errors.append(result.stderr)

    # Run pyright
    result = subprocess.run(
        ["python", "-m", "pyright", "src/"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append(result.stdout)
        errors.append(result.stderr)

    # Run SELMA AST rules
    result = subprocess.run(
        ["python", "-m", "selma", "src/selma/", "--skip-tools"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append(result.stdout)
        errors.append(result.stderr)

    if errors:
        for output in errors:
            if output.strip():
                print(output, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
