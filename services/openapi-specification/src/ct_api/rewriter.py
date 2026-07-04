from __future__ import annotations
from .ir import OASDoc

def rewrite_oas(doc: OASDoc) -> str:
    return doc.source or ""
