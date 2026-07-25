"""CLI entry point for Selma."""

import argparse
import sys

from selma import __version__

def main() -> None:
    """Main entry point for Selma CLI."""
    parser = argparse.ArgumentParser(
        prog="selma",
        description="Selma - Schema-driven AST Linter",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Selma v{__version__}",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to lint",
    )

    args = parser.parse_args()

    if not args.files:
        sys.exit(0)


if __name__ == "__main__":
    main()
