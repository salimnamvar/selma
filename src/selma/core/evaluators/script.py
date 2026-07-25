"""Script evaluator for Selma."""

import json
import subprocess

from selma.core.evaluators.base import EvaluatorBase

class ScriptEvaluator(EvaluatorBase):
    """Evaluates rules by running external scripts."""

    def evaluate(self, config: dict, data: dict | list) -> bool:
        """Evaluate by running a script.

        Args:
            config: Must contain 'path' to the script.
            data: Data to pass via stdin.

        Returns:
            True if script indicates a violation.
        """
        script_path = config.get("path", "")

        if not script_path:
            return False

        try:
            result = subprocess.run(  # noqa: S603
                [script_path],
                input=json.dumps(data),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode != 0:
                return False

            output = json.loads(result.stdout)
            return output.get("violation", False)

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return False
