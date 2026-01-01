"""
Cloze identifier - Identify cloze candidates in statements (Step 3).

Analyzes statements and identifies 2-5 testable terms per statement.
"""

import logging
import re
from pathlib import Path
from typing import List

from .llm_client import ClaudeClient
from .models import Statement

logger = logging.getLogger(__name__)


class ClozeIdentifier:
    """Identify cloze candidates in statements (Step 3)"""

    def __init__(self, client: ClaudeClient, prompt_template_path: Path):
        self.client = client
        self.prompt_template = self._load_prompt(prompt_template_path)

    def _load_prompt(self, path: Path) -> str:
        """Load prompt template from file"""
        with open(path, "r") as f:
            return f.read()

    def identify_cloze_candidates(self, statements: List[Statement]) -> List[Statement]:
        """
        Add cloze_candidates to each statement using LLM.

        Args:
            statements: List of Statement objects to process

        Returns:
            Updated list of Statement objects with cloze_candidates populated
        """
        if not statements:
            return statements

        # Build prompt with all statements
        statements_text = "\n".join(
            [f"{i+1}. {stmt.statement}" for i, stmt in enumerate(statements)]
        )

        prompt = self.prompt_template.format(statements=statements_text)

        # Call LLM
        logger.debug(f"Calling LLM for cloze identification ({len(statements)} statements)")
        response = self.client.generate(prompt)

        # Parse JSON response
        try:
            parsed = self.client.parse_json_response(response)

            if "cloze_mapping" not in parsed:
                raise ValueError("Response missing 'cloze_mapping' key")

            # Map cloze candidates back to statements
            for i, stmt in enumerate(statements):
                statement_key = str(i + 1)  # 1-indexed in prompt
                if statement_key in parsed["cloze_mapping"]:
                    raw_candidates = parsed["cloze_mapping"][statement_key]
                    # Strip units from numerical values
                    stmt.cloze_candidates = self._strip_units_from_candidates(
                        raw_candidates, stmt.statement
                    )

            total_candidates = sum(len(stmt.cloze_candidates) for stmt in statements)
            logger.info(
                f"Identified {total_candidates} cloze candidates across {len(statements)} statements"
            )

            return statements

        except Exception as e:
            logger.error(f"Failed to parse cloze identification response: {e}")
            raise

    def _strip_units_from_candidates(
        self, candidates: List[str], statement: str
    ) -> List[str]:
        """
        Strip units from numerical cloze candidates while preserving context.

        Examples:
            "1 mg/dL (0.25 mmol/L)" → "1"
            "60 mL/min/1.73 m2" → "60"
            "250 mg/24 h" → "250"
            "Type 2 diabetes" → "Type 2 diabetes" (unchanged)
            "parathyroidectomy" → "parathyroidectomy" (unchanged)

        Args:
            candidates: List of cloze candidate strings
            statement: The full statement (used for validation)

        Returns:
            List of processed cloze candidates with units stripped where appropriate
        """
        processed = []

        for candidate in candidates:
            # Pattern: number followed by space and units
            # Matches: "1 mg/dL", "60 mL/min/1.73 m2", "250 mg/24 h"
            # Doesn't match: "Type 2", "25-hydroxyvitamin D"
            pattern = r"^(\d+(?:\.\d+)?)\s+([a-zA-Z/%().\d\s]+)$"
            match = re.match(pattern, candidate)

            if match:
                number = match.group(1)
                units = match.group(2)

                # Validate that the full candidate appears in the statement
                # This prevents stripping "Type 2" from "Type 2 diabetes"
                if candidate in statement:
                    # Check if units look like medical units (contain /, mg, mL, etc.)
                    # This prevents "Type 2" from being stripped
                    unit_indicators = ["mg", "mL", "dL", "mmol", "ng", "/", "m2", "h"]
                    if any(indicator in units for indicator in unit_indicators):
                        logger.debug(
                            f"Stripped units: '{candidate}' → '{number}' (units: {units})"
                        )
                        processed.append(number)
                    else:
                        # Not actually units (e.g., "Type 2")
                        processed.append(candidate)
                else:
                    # Candidate not in statement - keep original
                    processed.append(candidate)
            else:
                # Not a number with units - keep original
                processed.append(candidate)

        return processed
