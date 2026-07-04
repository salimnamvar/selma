"""Naming policy — CRUD verb rules and CSR layer verb expectations."""

from __future__ import annotations

from typing import List, Optional

from usecase_diagram.domain.entities.contract import ContractBundle


class NamingPolicy:
    """Encapsulates verb-related validation rules from contracts.

    Attributes:
        _bundle (ContractBundle): Contract bundle with verb data.
    """

    def __init__(self, a_bundle: ContractBundle) -> None:
        """Initialize with a contract bundle.

        Args:
            a_bundle (ContractBundle): Contract bundle with verb data.
        """
        self._bundle: ContractBundle = a_bundle

    def is_banned(self, a_verb: str) -> bool:
        """Check if a verb is banned.

        Args:
            a_verb (str): Verb to check.

        Returns:
            bool: True if the verb is banned.
        """
        result: bool = a_verb.upper() in self._bundle.banned_verbs()
        return result

    def is_allowed(self, a_verb: str, a_category: Optional[str] = None) -> bool:
        """Check if a verb is allowed.

        Args:
            a_verb (str): Verb to check.
            a_category (Optional[str]): Category to filter by.

        Returns:
            bool: True if the verb is allowed.
        """
        result: bool = a_verb.upper() in self._bundle.allowed_verbs(a_category)
        return result

    def is_api_rest(self, a_verb: str) -> bool:
        """Check if a verb is an API REST verb.

        Args:
            a_verb (str): Verb to check.

        Returns:
            bool: True if the verb is an API REST verb.
        """
        result: bool = a_verb.upper() in self._bundle.api_rest_verbs()
        return result

    def csr_verb_fit(self, a_verb: str, a_layer: str) -> bool:
        """Check if a verb is appropriate for a CSR layer.

        Args:
            a_verb (str): Verb to check.
            a_layer (str): CSR layer name.

        Returns:
            bool: True if the verb fits the layer.
        """
        layer_verbs: List[str] = self._bundle.verbs.get(a_layer.lower(), [])
        result: bool = True
        if layer_verbs:
            result = a_verb.upper() in [v.upper() for v in layer_verbs]
        return result

    def extract_verb(self, a_title: str) -> Optional[str]:
        """Extract the verb part from a use case title like 'CLI-01: INSERT User'.

        Args:
            a_title (str): Use case title string.

        Returns:
            Optional[str]: Extracted verb or None.
        """
        result: Optional[str] = None
        if ":" in a_title:
            after_colon: str = a_title.split(":", 1)[1].strip()
            parts: List[str] = after_colon.split(None, 1)
            if parts:
                result = parts[0].upper()
        return result
