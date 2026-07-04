"""CheckScope value object for validation scope classification."""

from enum import StrEnum


class CheckScope(StrEnum):
    """Validation scope — determines what a rule operates on."""

    PER_FILE = "per_file"
    PER_UC = "per_uc"
    PROJECT = "project"
    ASSESSMENT = "assessment"
    EXTERNAL = "external"
