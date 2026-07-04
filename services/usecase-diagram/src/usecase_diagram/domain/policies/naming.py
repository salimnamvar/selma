"""Naming policy — CRUD verb rules and CSR layer verb expectations."""

from __future__ import annotations

from usecase_diagram.domain.entities.contract import ContractBundle


class NamingPolicy:
    """Encapsulates verb-related validation rules from contracts."""

    def __init__(self, bundle: ContractBundle) -> None:
        self._bundle = bundle

    def is_banned(self, verb: str) -> bool:
        return verb.upper() in self._bundle.banned_verbs()

    def is_allowed(self, verb: str, category: str | None = None) -> bool:
        return verb.upper() in self._bundle.allowed_verbs(category)

    def is_api_rest(self, verb: str) -> bool:
        return verb.upper() in self._bundle.api_rest_verbs()

    def csr_verb_fit(self, verb: str, layer: str) -> bool:
        """Check if a verb is appropriate for a CSR layer."""
        layer_verbs = self._bundle.verbs.get(layer.lower(), [])
        if layer_verbs:
            return verb.upper() in [v.upper() for v in layer_verbs]
        return True

    def extract_verb(self, title: str) -> str | None:
        """Extract the verb part from a use case title like 'CLI-01: INSERT User'."""
        if ":" in title:
            after_colon = title.split(":", 1)[1].strip()
            parts = after_colon.split(None, 1)
            if parts:
                return parts[0].upper()
        return None
