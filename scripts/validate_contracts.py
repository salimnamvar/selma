#!/usr/bin/env python3
"""
Cross-layer contract validators for the Selma Regulation document suite.

Validates:
1. Policy Runtime Prohibition — runtime source must not reference policy_doctrine.yaml
2. Version synchronization across spec, schema, policy, and user stories
3. Required normative cross-references present after audit clarifications
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationError:
    path: str
    message: str
    severity: str = "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.path}: {self.message}"


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)

    def add(self, path: str, message: str, severity: str = "error") -> None:
        self.errors.append(ValidationError(path, message, severity))

    @property
    def is_valid(self) -> bool:
        return not any(e.severity == "error" for e in self.errors)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "warning")

    def summary(self) -> str:
        lines = [
            f"Contract validation complete: {self.error_count} error(s), {self.warning_count} warning(s)"
        ]
        if self.errors:
            lines.append("")
            lines.extend(str(error) for error in self.errors)
        return "\n".join(lines)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def regulation_dir(root: Path) -> Path:
    return root / "docs" / "Regulation"


def runtime_source_dirs(root: Path) -> list[Path]:
    candidates = [root / "src"]
    return [path for path in candidates if path.is_dir()]


POLICY_REFERENCE_PATTERNS = (
    re.compile(r"policy_doctrine\.yaml"),
    re.compile(r"policy_doctrine"),
    re.compile(r"docs/Regulation/policy_doctrine"),
)


def validate_policy_runtime_prohibition(root: Path) -> ValidationResult:
    """Ensure runtime source paths do not import or reference policy_doctrine.yaml."""
    result = ValidationResult()
    runtime_dirs = runtime_source_dirs(root)

    if not runtime_dirs:
        result.add(
            "runtime.prohibition",
            "No runtime source directories found under src/; skipping runtime scan",
            severity="warning",
        )
        return result

    allowed_suffixes = {".py", ".go", ".rs", ".java", ".ts", ".js", ".yaml", ".yml", ".json", ".toml"}

    for runtime_dir in runtime_dirs:
        for path in runtime_dir.rglob("*"):
            if not path.is_file() or path.suffix not in allowed_suffixes:
                continue
            if "test" in path.name or path.name.startswith("."):
                continue

            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            for pattern in POLICY_REFERENCE_PATTERNS:
                if pattern.search(content):
                    result.add(
                        f"runtime.prohibition.{path.relative_to(root)}",
                        f"Runtime source references policy doctrine ({pattern.pattern})",
                    )
                    break

    return result


def _extract_version(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1)
    return None


def validate_version_synchronization(root: Path) -> ValidationResult:
    """Ensure MAJOR versions match across the three-layer contract suite."""
    result = ValidationResult()
    reg = regulation_dir(root)

    spec_path = reg / "SPECIFICATION.md"
    schema_path = reg / "rule_schema.json"
    policy_path = reg / "policy_doctrine.yaml"
    stories_path = root / "docs" / "User-Story" / "User_Stories.md"

    missing = [p for p in (spec_path, schema_path, policy_path, stories_path) if not p.exists()]
    if missing:
        for path in missing:
            result.add("version.sync", f"Missing contract document: {path}")
        return result

    spec_version = _extract_version(spec_path.read_text(encoding="utf-8"), [r"\*\*Version:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)"])
    schema_version = _extract_version(
        schema_path.read_text(encoding="utf-8"),
        [r'"x-spec-version":\s*"([0-9]+\.[0-9]+\.[0-9]+)"', r'"title":\s*"[^"]*\s([0-9]+\.[0-9]+\.[0-9]+)"'],
    )
    policy_version = _extract_version(
        policy_path.read_text(encoding="utf-8"),
        [r'^\s*version:\s*"([0-9]+\.[0-9]+\.[0-9]+)"', r'^\s*spec_version:\s*"([0-9]+\.[0-9]+\.[0-9]+)"'],
    )
    stories_version = _extract_version(
        stories_path.read_text(encoding="utf-8"),
        [r"\*\*Version:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)"],
    )

    versions = {
        "SPECIFICATION.md": spec_version,
        "rule_schema.json": schema_version,
        "policy_doctrine.yaml": policy_version,
        "User_Stories.md": stories_version,
    }

    for doc, version in versions.items():
        if version is None:
            result.add(f"version.sync.{doc}", "Could not extract semantic version")

    present = {doc: v for doc, v in versions.items() if v is not None}
    if len(present) < 2:
        return result

    majors = {doc: v.split(".")[0] for doc, v in present.items()}
    unique_majors = set(majors.values())
    if len(unique_majors) > 1:
        result.add(
            "version.sync.major",
            f"MAJOR version mismatch across documents: {majors}",
        )

    return result


def validate_audit_clarifications(root: Path) -> ValidationResult:
    """Verify normative audit clarifications are present in SPECIFICATION.md."""
    result = ValidationResult()
    spec_path = regulation_dir(root) / "SPECIFICATION.md"
    if not spec_path.exists():
        result.add("audit.clarifications", f"Missing {spec_path}")
        return result

    content = spec_path.read_text(encoding="utf-8")
    required_fragments = {
        "defer_to active-lineage resolution": "post-fork ambiguity",
        "creator provenance inheritance": "creator_provenance",
        "cross-lineage presentation correlation": "Cross-lineage presentation correlation",
        "NeedsReview + Fail guidance": "NeedsReview + Fail overlap",
        "policy runtime CI enforcement": "validate_contracts.py",
    }

    for name, fragment in required_fragments.items():
        if fragment not in content:
            result.add(f"audit.clarifications.{name}", f"Missing normative fragment: {fragment!r}")

    stories_path = root / "docs" / "User-Story" / "User_Stories.md"
    if stories_path.exists():
        stories = stories_path.read_text(encoding="utf-8")
        if "Segregation of Duties Constraint" not in stories:
            result.add(
                "audit.clarifications.capability_matrix",
                "User_Stories.md missing Segregation of Duties Constraint column",
            )

    return result


def validate_all(root: Path | None = None) -> ValidationResult:
    root = root or repo_root()
    aggregate = ValidationResult()
    for partial in (
        validate_policy_runtime_prohibition(root),
        validate_version_synchronization(root),
        validate_audit_clarifications(root),
    ):
        aggregate.errors.extend(partial.errors)
    return aggregate


def main() -> int:
    result = validate_all()
    print(result.summary())
    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())