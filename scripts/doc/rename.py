"""Domain rename tool.

Applies field, class, section, and path renames across the project from a JSON
mapping file. Supports multi-source current names (YAML vs Python), scoped
dangerous patterns, match modes, and whole-word replacements in code and docs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ── Data ─────────────────────────────────────────────────────────────


_MATCH_WORD: str = "word"
_MATCH_KEY: str = "key"
_MATCH_REGEX: str = "regex"
_VALID_MODES: Set[str] = {_MATCH_WORD, _MATCH_KEY, _MATCH_REGEX}

_REQUIRED_KEYS: Tuple[str, ...] = (
    "scan_dirs",
    "scan_files",
    "skip_files",
    "skip_dirs",
    "extensions",
    "dangerous_patterns",
)

_CONTENT_CATEGORIES: Tuple[str, ...] = ("fields", "classes", "sections")


@dataclass
class RenameRule:
    """A single rename pattern.

    Attributes:
        _pattern (re.Pattern[str]): Compiled match pattern.
        _target (str): Replacement string.
        _original (str): Source name for reporting.
        _mode (str): Match mode: "word", "key", or "regex".
        _scope (Optional[List[str]]): Relative path prefixes; None means all files.
        _replacement (str): Replacement template for regex mode.
    """

    _pattern: re.Pattern[str]
    _target: str
    _original: str
    _mode: str = field(default=_MATCH_WORD)
    _scope: Optional[List[str]] = field(default=None)
    _replacement: str = field(default="")

    def apply(self, a_text: str) -> Tuple[str, int]:
        """Apply this rule to text.

        Args:
            a_text (str): Input text.

        Returns:
            Tuple[str, int]: (result_text, replacement_count).
        """
        result: Tuple[str, int]
        if self._mode == _MATCH_KEY:
            result = self._pattern.subn(
                lambda match: f"{match.group(1)}{self._target}{match.group(2)}",
                a_text,
            )
        elif self._mode == _MATCH_REGEX:
            result = self._pattern.subn(self._replacement, a_text)
        else:
            result = self._pattern.subn(self._target, a_text)
        return result

    def matches_scope(self, a_rel_path: str) -> bool:
        """Return True if a relative path is in scope for this rule.

        Args:
            a_rel_path (str): Path relative to project root (posix).

        Returns:
            bool: True when the rule applies to this path.
        """
        result: bool = True
        if self._scope is not None:
            result = False
            for prefix in self._scope:
                normalized: str = prefix.replace("\\", "/").rstrip("/")
                if a_rel_path == normalized or a_rel_path.startswith(normalized + "/"):
                    result = True
                    break
        return result


@dataclass
class PathRename:
    """A filesystem path rename.

    Attributes:
        _source (Path): Absolute source path.
        _target (Path): Absolute target path.
        _original (str): Source path relative to project root.
        _destination (str): Target path relative to project root.
    """

    _source: Path
    _target: Path
    _original: str
    _destination: str


@dataclass
class RenameConfig:
    """Configuration loaded from the JSON mapping file.

    Attributes:
        _project_root (Path): Project root used to resolve relative paths.
        _scan_dirs (List[Path]): Directories to scan.
        _scan_files (List[Path]): Extra top-level files to scan.
        _skip_files (Set[str]): Filenames never modified.
        _skip_dirs (Set[str]): Directory names to skip during walk.
        _extensions (Set[str]): File extensions to process.
        _dangerous_patterns (Set[str]): Patterns that require scope.
        _preserve_import_module_paths (bool): Keep Python from-module paths intact.
        _rules (List[RenameRule]): Content replacement rules.
        _paths (List[PathRename]): Filesystem path renames.
        _skipped_dangerous (List[str]): Dangerous patterns skipped for missing scope.
    """

    _project_root: Path
    _scan_dirs: List[Path]
    _scan_files: List[Path]
    _skip_files: Set[str]
    _skip_dirs: Set[str]
    _extensions: Set[str]
    _dangerous_patterns: Set[str]
    _preserve_import_module_paths: bool
    _rules: List[RenameRule] = field(default_factory=list)
    _paths: List[PathRename] = field(default_factory=list)
    _skipped_dangerous: List[str] = field(default_factory=list)


# ── Config loading ───────────────────────────────────────────────────


def _require_keys(a_data: Dict[str, Any], a_keys: Tuple[str, ...]) -> None:
    """Raise ValueError if required mapping keys are missing.

    Args:
        a_data (Dict[str, Any]): Parsed JSON object.
        a_keys (Tuple[str, ...]): Required top-level keys.

    Raises:
        ValueError: When any required key is absent.
    """
    missing: List[str] = [key for key in a_keys if key not in a_data]
    if missing:
        raise ValueError(f"mapping file missing required keys: {', '.join(missing)}")


def _resolve_project_root(
    a_mapping_path: Path,
    a_data: Dict[str, Any],
    a_project_root: Optional[Path],
) -> Path:
    """Resolve project root from CLI, mapping file, or mapping location.

    Args:
        a_mapping_path (Path): Path to the JSON mapping file.
        a_data (Dict[str, Any]): Parsed mapping JSON.
        a_project_root (Optional[Path]): Explicit CLI project root.

    Returns:
        Path: Absolute project root.
    """
    result: Path
    if a_project_root is not None:
        result = a_project_root.resolve()
    elif "project_root" in a_data:
        candidate: Path = Path(a_data["project_root"])
        if candidate.is_absolute():
            result = candidate.resolve()
        else:
            result = (a_mapping_path.parent / candidate).resolve()
    else:
        result = a_mapping_path.resolve().parent.parent.parent
    return result


def _compile_pattern(
    a_current: str,
    a_mode: str,
    a_pattern: Optional[str] = None,
) -> re.Pattern[str]:
    """Compile a rename pattern for the given match mode.

    Args:
        a_current (str): Source identifier (used for word/key modes).
        a_mode (str): "word", "key", or "regex".
        a_pattern (Optional[str]): Explicit regex for regex mode.

    Returns:
        re.Pattern[str]: Compiled pattern.

    Raises:
        ValueError: If mode is unknown or regex mode lacks a pattern.
    """
    result: re.Pattern[str]
    if a_mode == _MATCH_KEY:
        result = re.compile(r"(?m)^([ \t]*)" + re.escape(a_current) + r"(\s*:)")
    elif a_mode == _MATCH_WORD:
        result = re.compile(r"\b" + re.escape(a_current) + r"\b")
    elif a_mode == _MATCH_REGEX:
        if not a_pattern:
            raise ValueError(f"regex mode requires 'pattern' for '{a_current}'")
        result = re.compile(a_pattern)
    else:
        raise ValueError(f"unknown match mode: {a_mode}")
    return result


def _build_rules(
    a_data: Dict[str, Any],
    a_dangerous: Set[str],
) -> Tuple[List[RenameRule], List[str]]:
    """Build content rename rules from mapping categories.

    Args:
        a_data (Dict[str, Any]): Parsed mapping JSON.
        a_dangerous (Set[str]): Patterns that require a scope.

    Returns:
        Tuple[List[RenameRule], List[str]]: Rules and skipped dangerous names.

    Raises:
        ValueError: If an entry uses an invalid mode or is incomplete.
    """
    rules: List[RenameRule] = []
    skipped: List[str] = []
    seen: Set[Tuple[str, str, str, Optional[Tuple[str, ...]], str]] = set()

    for category in _CONTENT_CATEGORIES:
        for entry in a_data.get(category, []):
            target: str = entry["target"]
            scope: Optional[List[str]] = entry.get("scope")
            mode: str = entry.get("mode", _MATCH_WORD)
            explicit_pattern: Optional[str] = entry.get("pattern")
            replacement: str = entry.get("replacement", target)
            if mode not in _VALID_MODES:
                raise ValueError(f"invalid mode '{mode}' for target '{target}'")
            scope_key: Optional[Tuple[str, ...]] = tuple(scope) if scope is not None else None
            currents: List[str] = entry.get("current", [target])
            for current in currents:
                dedupe_key: Tuple[str, str, str, Optional[Tuple[str, ...]], str] = (
                    current,
                    target,
                    mode,
                    scope_key,
                    explicit_pattern or "",
                )
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                if current in a_dangerous and scope is None and mode != _MATCH_REGEX:
                    skipped.append(current)
                    continue
                if current == target and mode != _MATCH_REGEX:
                    continue
                rules.append(
                    RenameRule(
                        _pattern=_compile_pattern(current, mode, explicit_pattern),
                        _target=target,
                        _original=current,
                        _mode=mode,
                        _scope=scope,
                        _replacement=replacement,
                    )
                )

    rules.sort(key=lambda rule: len(rule._original), reverse=True)
    return rules, skipped


def _build_paths(a_data: Dict[str, Any], a_project_root: Path) -> List[PathRename]:
    """Build filesystem path renames from the mapping file.

    Args:
        a_data (Dict[str, Any]): Parsed mapping JSON.
        a_project_root (Path): Absolute project root.

    Returns:
        List[PathRename]: Path rename entries.
    """
    paths: List[PathRename] = []
    for entry in a_data.get("paths", []):
        target_rel: str = entry["target"].replace("\\", "/")
        for current in entry["current"]:
            source_rel: str = current.replace("\\", "/")
            if source_rel == target_rel:
                continue
            paths.append(
                PathRename(
                    _source=a_project_root / source_rel,
                    _target=a_project_root / target_rel,
                    _original=source_rel,
                    _destination=target_rel,
                )
            )
    return paths


def load_config(
    a_mapping_path: Path,
    a_project_root: Optional[Path] = None,
) -> RenameConfig:
    """Load rename configuration from a JSON mapping file.

    Args:
        a_mapping_path (Path): Path to renames.json.
        a_project_root (Optional[Path]): Optional CLI override for project root.

    Returns:
        RenameConfig: Loaded configuration.

    Raises:
        FileNotFoundError: If the mapping file does not exist.
        json.JSONDecodeError: If the mapping file is not valid JSON.
        ValueError: If required keys are missing or modes are invalid.
        OSError: If the mapping file cannot be read.
    """
    with a_mapping_path.open(encoding="utf-8") as handle:
        data: Dict[str, Any] = json.load(handle)

    _require_keys(data, _REQUIRED_KEYS)

    project_root: Path = _resolve_project_root(a_mapping_path, data, a_project_root)
    dangerous: Set[str] = set(data["dangerous_patterns"])
    rules, skipped = _build_rules(data, dangerous)
    paths: List[PathRename] = _build_paths(data, project_root)

    config: RenameConfig = RenameConfig(
        _project_root=project_root,
        _scan_dirs=[project_root / item for item in data["scan_dirs"]],
        _scan_files=[project_root / item for item in data["scan_files"]],
        _skip_files=set(data["skip_files"]),
        _skip_dirs=set(data["skip_dirs"]),
        _extensions=set(data["extensions"]),
        _dangerous_patterns=dangerous,
        _preserve_import_module_paths=bool(data.get("preserve_import_module_paths", False)),
        _rules=rules,
        _paths=paths,
        _skipped_dangerous=skipped,
    )
    return config


# ── Engine ───────────────────────────────────────────────────────────


class RenameEngine:
    """Applies rename rules across project files.

    Attributes:
        _config (RenameConfig): Configuration and rename rules.
    """

    def __init__(self, a_config: RenameConfig) -> None:
        """Initialise the engine.

        Args:
            a_config (RenameConfig): Configuration and rename rules.
        """
        self._config: RenameConfig = a_config

    def apply(self, a_dry_run: bool = False, a_verbose: bool = False) -> Tuple[int, int, int]:
        """Apply content and path renames.

        Args:
            a_dry_run (bool): Preview only when True.
            a_verbose (bool): Print per-rule counts when True.

        Returns:
            Tuple[int, int, int]: (files_changed, content_replacements, paths_renamed).
        """
        if self._config._skipped_dangerous:
            print("Skipped dangerous global renames (handle manually or add scope):")
            for name in self._config._skipped_dangerous:
                print(f"  - {name}")
            print()

        files: List[Path] = self._collect_files()
        print(f"Loaded {len(self._config._rules)} content patterns.")
        print(f"Loaded {len(self._config._paths)} path renames.")
        print(f"Scanning {len(files)} files...\n")

        total_changed: int = 0
        total_replacements: int = 0

        for filepath in files:
            changed, count = self._process_file(filepath, a_dry_run, a_verbose)
            if changed:
                total_changed += 1
                total_replacements += count

        paths_renamed: int = self._rename_paths(a_dry_run, a_verbose)

        print(f"\n{'=' * 50}")
        print(f"Files changed:      {total_changed}")
        print(f"Replacements:       {total_replacements}")
        print(f"Paths renamed:      {paths_renamed}")
        if a_dry_run:
            print("\n[DRY RUN] No files modified.")

        return total_changed, total_replacements, paths_renamed

    def _collect_files(self) -> List[Path]:
        """Collect unique files under scan dirs and scan files.

        Returns:
            List[Path]: Sorted absolute file paths.
        """
        files: List[Path] = []

        for scan_dir in self._config._scan_dirs:
            if not scan_dir.exists():
                continue
            for path in scan_dir.rglob("*"):
                if path.is_file() and not self._should_skip(path):
                    files.append(path)

        for scan_file in self._config._scan_files:
            if scan_file.exists() and not self._should_skip(scan_file):
                files.append(scan_file)

        return sorted(set(files))

    def _should_skip(self, a_path: Path) -> bool:
        """Return True when a path must not be processed.

        Args:
            a_path (Path): Candidate file path.

        Returns:
            bool: True if skipped.
        """
        result: bool = False
        if a_path.name in self._config._skip_files:
            result = True
        elif any(part in self._config._skip_dirs for part in a_path.parts):
            result = True
        elif a_path.suffix not in self._config._extensions:
            result = True
        return result

    def _relative(self, a_path: Path) -> str:
        """Return path relative to project root as posix string.

        Args:
            a_path (Path): Absolute path.

        Returns:
            str: Relative posix path, or absolute posix if outside root.
        """
        result: str
        try:
            result = a_path.relative_to(self._config._project_root).as_posix()
        except ValueError:
            result = a_path.as_posix()
        return result

    def _process_file(
        self,
        a_filepath: Path,
        a_dry_run: bool,
        a_verbose: bool,
    ) -> Tuple[bool, int]:
        """Apply content renames to one file.

        Args:
            a_filepath (Path): File to process.
            a_dry_run (bool): Preview only when True.
            a_verbose (bool): Print per-rule counts when True.

        Returns:
            Tuple[bool, int]: (was_changed, replacement_count).
        """
        try:
            content: str = a_filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError, OSError):
            return False, 0

        rel: str = self._relative(a_filepath)
        new_content: str = content
        change_lines: List[str] = []
        total: int = 0

        for rule in self._config._rules:
            if not rule.matches_scope(rel):
                continue
            updated, count = self._apply_rule(new_content, rule, a_filepath.suffix)
            if count > 0:
                change_lines.append(f"  {rule._original} -> {rule._target} [{rule._mode}]: {count}")
                new_content = updated
                total += count

        if total == 0:
            return False, 0

        print(f"{'[DRY] ' if a_dry_run else ''}{rel}")
        if a_verbose:
            for line in change_lines:
                print(line)
        else:
            print(f"  {total} replacement(s)")

        if not a_dry_run:
            a_filepath.write_text(new_content, encoding="utf-8")

        return True, total

    def _apply_rule(
        self,
        a_content: str,
        a_rule: RenameRule,
        a_suffix: str,
    ) -> Tuple[str, int]:
        """Apply one rule to file content.

        Args:
            a_content (str): Current file content.
            a_rule (RenameRule): Rule to apply.
            a_suffix (str): File suffix (e.g. ".py").

        Returns:
            Tuple[str, int]: (updated_content, replacement_count).
        """
        result: Tuple[str, int]
        if (
            a_suffix == ".py"
            and self._config._preserve_import_module_paths
            and a_rule._mode == _MATCH_WORD
        ):
            result = self._apply_rule_python(a_content, a_rule)
        else:
            result = a_rule.apply(a_content)
        return result

    def _apply_rule_python(self, a_content: str, a_rule: RenameRule) -> Tuple[str, int]:
        """Apply a rule to Python source, preserving from-module paths.

        Args:
            a_content (str): Python source text.
            a_rule (RenameRule): Rule to apply.

        Returns:
            Tuple[str, int]: (updated_content, replacement_count).
        """
        lines: List[str] = a_content.split("\n")
        new_lines: List[str] = []
        total: int = 0

        for line in lines:
            stripped: str = line.lstrip()
            if stripped.startswith("from ") and " import " in stripped:
                updated, count = self._apply_import_line(line, a_rule)
            else:
                updated, count = a_rule.apply(line)
            new_lines.append(updated)
            total += count

        return "\n".join(new_lines), total

    def _apply_import_line(self, a_line: str, a_rule: RenameRule) -> Tuple[str, int]:
        """Rename imported symbols on a from-import line only.

        Args:
            a_line (str): Source line.
            a_rule (RenameRule): Rule to apply.

        Returns:
            Tuple[str, int]: (updated_line, replacement_count).
        """
        marker: str = " import "
        idx: int = a_line.find(marker)
        if idx < 0:
            return a_rule.apply(a_line)

        head: str = a_line[: idx + len(marker)]
        tail: str = a_line[idx + len(marker) :]
        new_tail, count = a_rule.apply(tail)
        return head + new_tail, count

    def _rename_paths(self, a_dry_run: bool, a_verbose: bool) -> int:
        """Rename files listed in the paths category.

        Args:
            a_dry_run (bool): Preview only when True.
            a_verbose (bool): Print each path rename when True.

        Returns:
            int: Number of path renames applied or previewed.
        """
        renamed: int = 0
        for path_rule in self._config._paths:
            if not path_rule._source.exists():
                if a_verbose:
                    print(f"[skip path] missing: {path_rule._original}")
                continue
            if path_rule._target.exists():
                print(
                    f"Warning: target exists, skip path rename: {path_rule._destination}",
                    file=sys.stderr,
                )
                continue

            print(
                f"{'[DRY] ' if a_dry_run else ''}"
                f"path: {path_rule._original} -> {path_rule._destination}"
            )
            if not a_dry_run:
                path_rule._target.parent.mkdir(parents=True, exist_ok=True)
                path_rule._source.rename(path_rule._target)
            renamed += 1
        return renamed


# ── CLI ──────────────────────────────────────────────────────────────


def parse_args(a_argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        a_argv (Optional[List[str]]): Argument list. Uses sys.argv when None.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Apply domain renames across the project from a JSON mapping file.",
    )
    parser.add_argument(
        "mapping",
        type=Path,
        help="Path to the JSON mapping file (e.g. scripts/doc/renames.json).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root. Overrides mapping project_root when set.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed replacement info.",
    )
    return parser.parse_args(a_argv)


def main(
    a_mapping: Optional[Path] = None,
    a_project_root: Optional[Path] = None,
    a_dry_run: Optional[bool] = None,
    a_verbose: Optional[bool] = None,
    a_argv: Optional[List[str]] = None,
) -> None:
    """Apply domain renames across the project.

    Args:
        a_mapping (Optional[Path]): Mapping file path. Overrides CLI when set.
        a_project_root (Optional[Path]): Project root. Overrides CLI when set.
        a_dry_run (Optional[bool]): Dry-run flag. Overrides CLI when set.
        a_verbose (Optional[bool]): Verbose flag. Overrides CLI when set.
        a_argv (Optional[List[str]]): CLI arguments. Uses sys.argv when None.
    """
    args: argparse.Namespace = parse_args(a_argv)

    mapping_path: Path = a_mapping if a_mapping is not None else args.mapping
    project_root: Optional[Path] = a_project_root if a_project_root is not None else args.project_root
    dry_run: bool = a_dry_run if a_dry_run is not None else args.dry_run
    verbose: bool = a_verbose if a_verbose is not None else args.verbose

    if not mapping_path.exists():
        print(f"Error: mapping file not found: {mapping_path}", file=sys.stderr)
        sys.exit(1)

    try:
        config: RenameConfig = load_config(mapping_path, a_project_root=project_root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error loading mapping: {exc}", file=sys.stderr)
        sys.exit(1)

    if not config._rules and not config._paths:
        print("No safe renames to apply.")
        sys.exit(0)

    engine: RenameEngine = RenameEngine(config)
    engine.apply(a_dry_run=dry_run, a_verbose=verbose)


if __name__ == "__main__":
    main()
