"""Roles for the capability matrix (§3.2 / §3.2.1)."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """Authenticated actor role bound at identity verification."""

    REGULATORY_OFFICIAL = "regulatory_official"
    COMPLIANCE_REPRESENTATIVE = "compliance_representative"
    SYSTEM = "system"
