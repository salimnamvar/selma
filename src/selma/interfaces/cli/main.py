"""CLI interface — command-line entry point.

Minimal composition root. All logic in use cases.
"""

from __future__ import annotations

import argparse
import sys

from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result


def main() -> int:
    """CLI entry point.

    Parses arguments, wires dependencies, runs lint, outputs results.
    """
    b_continue = True
    result = 0
    parser = argparse.ArgumentParser(
        prog="selma",
        description="Selma — Schema-driven AST linter enforcing Safe Coding Doctrine",
    )
    parser.add_argument("--version", action="version", version="Selma v0.1.0")
    parser.add_argument("paths", nargs="*", help="Files or directories to lint")
    parser.add_argument("-f", "--format", choices=["default", "json", "gcc", "guidance"], default="default")
    parser.add_argument("--guide", action="store_true", help="Include guidance in output")
    parser.add_argument("--skip-tools", action="store_true", help="Skip external tools")
    parser.add_argument("--skip-ast", action="store_true", help="Skip AST rules")
    parser.add_argument("--only", help="Run only one check")
    parser.add_argument("--codes", nargs="*", help="Only run rules with these codes")
    parser.add_argument("--exclude-codes", nargs="*", help="Exclude rules with these codes")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if b_continue and not args.paths:
        b_continue = False
        parser.print_help()
        result = 0

    if b_continue:
        print(f"Selma Linter v0.1.0")
        print(f"Paths: {args.paths}")
        print(f"Format: {args.format}")
        print("Pipeline will be fully wired in Phase 2 (schema-driven rules).")
        result = 0
    return result
