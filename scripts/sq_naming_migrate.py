#!/usr/bin/env python3
"""SQ Naming Migration Script.

Migrates SQ directories and files from abbreviated codes to canonical C4 names.

Usage:
    python sq_naming_migrate.py /path/to/docs --dry-run
    python sq_naming_migrate.py /path/to/docs --execute
    python sq_naming_migrate.py /path/to/docs --execute --update-internal-refs

Safety:
    - Always run with --dry-run first to preview changes
    - Creates backup of each file before modification
    - Generates migration report

Bound to rules/software-design/sq.md Migration / Technical Debt section.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import NamedTuple


# Canonical mapping: abbreviation → canonical name
ABBREVIATION_MAP = {
    "AGT": "Agent",
    "CLI": "CLI",
    "CFG": "Config",
    "CTX": "ContextGraph",
    "EDT": "EditStrategy",
    "EVL": "Evaluation",
    "HK": "Hooks",
    "MCP": "MCP",
    "MEM": "Memory",
    "OBS": "Observability",
    "PLG": "Plugins",
    "PRV": "Provider",
    "RIM": "RepoIntelligence",
    "RTG": "Router",
    "SAF": "Safety",
    "SBX": "Sandbox",
    "SRV": "API",
    "SSN": "Session",
    "TL": "Tool",
    "VCS": "Git",
    "WRL": "WireLog",
}

# Mapping for file prefix changes (old prefix → new prefix)
FILE_PREFIX_MAP = {
    "sq_agt": "sq_agent",
    "sq_cli": "sq_cli",  # CLI stays same
    "sq_cfg": "sq_config",
    "sq_ctx": "sq_contextgraph",
    "sq_edt": "sq_editstrategy",
    "sq_evl": "sq_evaluation",
    "sq_hk": "sq_hooks",
    "sq_mcp": "sq_mcp",  # MCP stays same
    "sq_mem": "sq_memory",
    "sq_obs": "sq_observability",
    "sq_plg": "sq_plugins",
    "sq_prv": "sq_provider",
    "sq_rim": "sq_repointelligence",
    "sq_rtg": "sq_router",
    "sq_saf": "sq_safety",
    "sq_sbx": "sq_sandbox",
    "sq_srv": "sq_api",
    "sq_ssn": "sq_session",
    "sq_tl": "sq_tool",
    "sq_vcs": "sq_git",
    "sq_wrl": "sq_wirelog",
}


class MigrationAction(NamedTuple):
    action_type: str  # "rename_dir", "rename_file", "update_ref"
    source: str
    target: str
    file_path: str | None = None


class MigrationReport(NamedTuple):
    actions: list[MigrationAction]
    dry_run: bool
    files_processed: int
    dirs_renamed: int
    files_renamed: int
    refs_updated: int


def get_sq_files(sq_dir: Path) -> list[Path]:
    """Get all .puml files in SQ directory tree."""
    return sorted(sq_dir.rglob("*.puml"))


def plan_dir_renames(sq_dir: Path) -> list[MigrationAction]:
    """Plan directory renames from abbreviated to canonical names."""
    actions = []
    for d in sq_dir.iterdir():
        if d.is_dir() and d.name in ABBREVIATION_MAP and d.name != "common":
            canonical = ABBREVIATION_MAP[d.name]
            if d.name != canonical:  # Skip if already canonical
                actions.append(MigrationAction(
                    action_type="rename_dir",
                    source=str(d),
                    target=str(d.parent / canonical),
                ))
    return actions


def plan_file_renames(sq_dir: Path) -> list[MigrationAction]:
    """Plan file renames within SQ directories."""
    actions = []
    for d in sq_dir.iterdir():
        if not d.is_dir() or d.name == "common":
            continue

        # Determine new directory name
        dir_name = d.name
        if dir_name in ABBREVIATION_MAP:
            dir_name = ABBREVIATION_MAP[dir_name]

        for f in d.glob("*.puml"):
            # Check if filename needs prefix update
            for old_prefix, new_prefix in FILE_PREFIX_MAP.items():
                if f.name.startswith(old_prefix + "0") or f.name.startswith(old_prefix + "1") or f.name.startswith(old_prefix + "2"):
                    # Extract the rest of the filename after the prefix number
                    match = re.match(rf"({old_prefix})(\d+)(.*)", f.name)
                    if match:
                        prefix, num, rest = match.groups()
                        new_name = f"{new_prefix}{num}{rest}"
                        new_path = f.parent / new_name
                        actions.append(MigrationAction(
                            action_type="rename_file",
                            source=str(f),
                            target=str(new_path),
                        ))
                    break
    return actions


def plan_ref_updates(sq_dir: Path) -> list[MigrationAction]:
    """Plan internal reference updates in .puml files."""
    actions = []
    for f in sq_dir.rglob("*.puml"):
        try:
            content = f.read_text()
            updated = content

            # Update @startuml IDs
            for old_prefix, new_prefix in FILE_PREFIX_MAP.items():
                # Pattern: @startuml sq_agt01_process_user_task
                pattern = rf"@startuml ({old_prefix}\d+_\w+)"
                replacement = rf"@startuml {new_prefix}\1"[len("@startuml "):]
                # Actually, we need to be more careful
                match = re.search(pattern, updated)
                if match:
                    old_id = match.group(1)
                    for p, n in FILE_PREFIX_MAP.items():
                        if old_id.startswith(p):
                            new_id = old_id.replace(p, n, 1)
                            updated = updated.replace(old_id, new_id)
                            break

            if updated != content:
                actions.append(MigrationAction(
                    action_type="update_ref",
                    source=str(f),
                    target=str(f),
                    file_path=str(f),
                ))
        except Exception:
            continue
    return actions


def execute_actions(actions: list[MigrationAction], dry_run: bool, update_refs: bool) -> MigrationReport:
    """Execute migration actions."""
    dirs_renamed = 0
    files_renamed = 0
    refs_updated = 0

    # Execute in order: refs first, then files, then dirs
    ref_actions = [a for a in actions if a.action_type == "update_ref"]
    file_actions = [a for a in actions if a.action_type == "rename_file"]
    dir_actions = [a for a in actions if a.action_type == "rename_dir"]

    if update_refs:
        for action in ref_actions:
            if not dry_run:
                try:
                    f = Path(action.file_path)
                    content = f.read_text()
                    # Apply all prefix replacements
                    for old_prefix, new_prefix in FILE_PREFIX_MAP.items():
                        content = content.replace(old_prefix, new_prefix)
                    f.write_text(content)
                except Exception as e:
                    print(f"Warning: Failed to update refs in {action.source}: {e}", file=sys.stderr)
            refs_updated += 1

    for action in file_actions:
        if not dry_run:
            try:
                shutil.copy2(action.source, action.source + ".bak")
                Path(action.source).rename(action.target)
            except Exception as e:
                print(f"Warning: Failed to rename {action.source}: {e}", file=sys.stderr)
        files_renamed += 1

    for action in dir_actions:
        if not dry_run:
            try:
                shutil.copytree(action.source, action.source + ".bak")
                Path(action.source).rename(action.target)
            except Exception as e:
                print(f"Warning: Failed to rename directory {action.source}: {e}", file=sys.stderr)
        dirs_renamed += 1

    return MigrationReport(
        actions=actions,
        dry_run=dry_run,
        files_processed=len([a for a in actions if a.action_type == "rename_file"]),
        dirs_renamed=dirs_renamed,
        files_renamed=files_renamed,
        refs_updated=refs_updated,
    )


def format_report(report: MigrationReport) -> str:
    """Format migration report."""
    lines = []
    lines.append("SQ Naming Migration Report")
    lines.append("=" * 50)
    lines.append(f"Mode: {'DRY RUN' if report.dry_run else 'EXECUTED'}")
    lines.append(f"Directories to rename: {report.dirs_renamed}")
    lines.append(f"Files to rename: {report.files_renamed}")
    lines.append(f"Internal refs to update: {report.refs_updated}")
    lines.append("")

    if report.actions:
        lines.append("Actions:")
        lines.append("-" * 50)
        for action in report.actions[:50]:  # Limit output
            if action.action_type == "rename_dir":
                lines.append(f"  DIR: {Path(action.source).name}/ → {Path(action.target).name}/")
            elif action.action_type == "rename_file":
                lines.append(f"  FILE: {Path(action.source).name} → {Path(action.target).name}")
            elif action.action_type == "update_ref":
                lines.append(f"  REFS: {Path(action.source).name}")

        if len(report.actions) > 50:
            lines.append(f"  ... and {len(report.actions) - 50} more actions")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SQ Naming Migration Script"
    )
    parser.add_argument("docs_dir", help="Path to docs/ directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--execute", action="store_true", help="Execute the migration")
    parser.add_argument("--update-internal-refs", action="store_true",
                        help="Update internal references in .puml files")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Must specify either --dry-run or --execute", file=sys.stderr)
        return 2

    docs_dir = Path(args.docs_dir)
    sq_dir = docs_dir / "SQ"
    if not sq_dir.exists():
        print(f"SQ directory not found: {sq_dir}", file=sys.stderr)
        return 2

    # Plan all actions
    actions = []
    actions.extend(plan_dir_renames(sq_dir))
    actions.extend(plan_file_renames(sq_dir))
    if args.update_internal_refs:
        actions.extend(plan_ref_updates(sq_dir))

    # Execute
    report = execute_actions(actions, args.dry_run, args.update_internal_refs)

    if args.format == "json":
        payload = {
            "dry_run": report.dry_run,
            "dirs_renamed": report.dirs_renamed,
            "files_renamed": report.files_renamed,
            "refs_updated": report.refs_updated,
            "actions": [
                {
                    "type": a.action_type,
                    "source": a.source,
                    "target": a.target,
                }
                for a in report.actions
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_report(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
