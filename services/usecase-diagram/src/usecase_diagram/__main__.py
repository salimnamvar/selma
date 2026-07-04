"""CLI entrypoint for the usecase-diagram subproject."""

from usecase_diagram.controller.cli import cli

if __name__ == "__main__":
    cli(standalone_mode=True)
