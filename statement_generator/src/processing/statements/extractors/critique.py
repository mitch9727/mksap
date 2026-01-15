"""
Critique processor - Extract statements from question critique (Step 1).

Reads critique field and generates testable medical fact statements.
"""

import logging
from pathlib import Path
from typing import List

from .infrastructure.llm.client import ClaudeClient
from .infrastructure.models.data_models import Statement

logger = logging.getLogger(__name__)


class CritiqueProcessor:
    """Extract statements from question critique (Step 1)"""

    def __init__(self, client: ClaudeClient, prompt_template_path: Path):
        self.client = client
        self.prompt_template = self._load_prompt(prompt_template_path)

    def _load_prompt(self, path: Path) -> str:
        """Load prompt template from file"""
        with open(path, "r") as f:
            return f.read()

    def extract_statements(self, critique: str, educational_objective: str) -> List[Statement]:
        """
        Extract statements from critique using LLM.

        Args:
            critique: Question critique text
            educational_objective: Learning goal for the question

        Returns:
            List of Statement objects (cloze_candidates empty at this stage)
        """
        # Build prompt
        prompt = self.prompt_template.format(
            critique=critique, educational_objective=educational_objective
        )

        # Call LLM
        logger.debug(f"Calling LLM for critique extraction (critique length: {len(critique)})")
        response = self.client.generate(prompt)

        # Parse JSON response
        try:
            parsed = self.client.parse_json_response(response)

            # Validate structure
            if "statements" not in parsed:
                raise ValueError("Response missing 'statements' key")

            # Convert to Statement objects (without cloze_candidates - added in Step 3)
            statements = []
            for stmt_data in parsed["statements"]:
                statements.append(
                    Statement(
                        statement=stmt_data["statement"],
                        extra_field=stmt_data.get("extra_field"),  # Allow None
                        cloze_candidates=[],  # Populated in Step 3
                    )
                )

            logger.info(f"Extracted {len(statements)} statements from critique")
            return statements

        except Exception as e:
            logger.error(f"Failed to parse critique extraction response: {e}")
            raise
