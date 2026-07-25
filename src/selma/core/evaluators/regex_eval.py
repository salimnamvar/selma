"""Regex evaluator for Selma."""

import re

from selma.core.evaluators.base import EvaluatorBase

class RegexEvaluator(EvaluatorBase):
    """Evaluates data against regex patterns."""

    def evaluate(self, config: dict, data: dict | list) -> bool:
        """Evaluate regex pattern against data.

        Args:
            config: Must contain 'pattern'. Optional 'flags'.
            data: String or list to match against.

        Returns:
            True if pattern matches.
        """
        pattern = config.get("pattern", "")
        flags_str = config.get("flags", "")

        # Convert flags string to re flags
        flags = 0
        if "i" in flags_str:
            flags |= re.IGNORECASE
        if "m" in flags_str:
            flags |= re.MULTILINE
        if "s" in flags_str:
            flags |= re.DOTALL

        if isinstance(data, list):
            return any(re.search(pattern, str(item), flags) for item in data)

        return bool(re.search(pattern, str(data), flags))
