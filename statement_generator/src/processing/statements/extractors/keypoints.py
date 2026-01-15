"""
Key points processor - Extract statements from key_points array (Step 2).

Refines pre-formatted key points into testable statements.
"""

import logging
from pathlib import Path
from typing import List

from .infrastructure.llm.client import ClaudeClient
from .infrastructure.models.data_models import Statement

logger = logging.getLogger(__name__)


class KeyPointsProcessor:
    """Extract statements from key_points array (Step 2)"""

    def __init__(self, client: ClaudeClient, prompt_template_path: Path):
        self.client = client
        self.prompt_template = self._load_prompt(prompt_template_path)

    def _load_prompt(self, path: Path) -> str:
        """Load prompt template from file"""
        with open(path, "r") as f:
            return f.read()

    def extract_statements(self, key_points: List[str]) -> List[Statement]:
        """
        Extract statements from key_points using LLM.

        Args:
            key_points: List of pre-formatted key point strings

        Returns:
            List of Statement objects (cloze_candidates empty at this stage)
        """
        if not key_points:
            logger.debug("No key_points to process")
            return []

        # Build prompt
        key_points_text = "\n".join([f"{i+1}. {kp}" for i, kp in enumerate(key_points)])
        prompt = self.prompt_template.format(key_points=key_points_text)

        # Call LLM
        logger.debug(f"Calling LLM for key_points extraction ({len(key_points)} points)")
        response = self.client.generate(prompt)

        # Parse JSON response
        try:
            parsed = self.client.parse_json_response(response)

            if "statements" not in parsed:
                raise ValueError("Response missing 'statements' key")

            statements = []
            for stmt_data in parsed["statements"]:
                statements.append(
                    Statement(
                        statement=stmt_data["statement"],
                        extra_field=stmt_data.get("extra_field"),  # Allow None
                        cloze_candidates=[],  # Populated in Step 3
                    )
                )

            logger.info(f"Extracted {len(statements)} statements from key_points")
            return statements

        except Exception as e:
            logger.error(f"Failed to parse key_points extraction response: {e}")
            raise
