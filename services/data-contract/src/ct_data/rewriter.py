"""ODCS rewriter (returns (fixed) text)."""
from __future__ import annotations

from .ir import ODCSDoc


def rewrite_odcs(doc: ODCSDoc) -> str:
    return doc.source or ""
