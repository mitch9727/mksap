"""
Critique processor - Extract statements from question critique (Step 1).

Reads critique field and generates testable medical fact statements.

Hybrid Mode:
  When NLP artifacts are provided, injects entity/negation/atomicity
  guidance into the prompt to improve LLM extraction accuracy.
"""

import logging
from pathlib import Path
from typing import List, Optional

from ....infrastructure.llm.client import ClaudeClient
from ....infrastructure.models.data_models import Statement
from ....infrastructure.models.fact_candidates import EnrichedPromptContext

logger = logging.getLogger(__name__)


class CritiqueProcessor:
    """Extract statements from question critique (Step 1).

    Supports two modes:
    - Legacy mode: Direct LLM extraction without NLP guidance
    - Hybrid mode: NLP-guided extraction with entity/negation/atomicity hints
    """

    def __init__(self, client: ClaudeClient, prompt_template_path: Path):
        self.client = client
        self.prompt_template = self._load_prompt(prompt_template_path)

    def _load_prompt(self, path: Path) -> str:
        """Load prompt template from file"""
        with open(path, "r") as f:
            return f.read()

    def extract_statements(
        self,
        critique: str,
        educational_objective: str,
        nlp_context: Optional[EnrichedPromptContext] = None,
    ) -> List[Statement]:
        """
        Extract statements from critique using LLM.

        Args:
            critique: Question critique text
            educational_objective: Learning goal for the question
            nlp_context: Optional NLP analysis for hybrid mode guidance

        Returns:
            List of Statement objects (cloze_candidates empty at this stage)
        """
        # Build NLP guidance section if context provided
        nlp_guidance = ""
        if nlp_context:
            nlp_guidance = self._format_nlp_guidance(nlp_context)
            logger.debug(f"Injecting NLP guidance ({len(nlp_guidance)} chars)")

        # Build prompt with optional NLP guidance
        prompt = self.prompt_template.format(
            critique=critique,
            educational_objective=educational_objective,
            nlp_guidance=nlp_guidance,
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

    def _format_nlp_guidance(self, context: EnrichedPromptContext) -> str:
        """Format NLP analysis into prompt guidance section.

        Generates structured guidance including:
        - Entity summary (what medical concepts were detected)
        - Negation warnings (which entities are negated - MUST preserve)
        - Atomicity recommendations (which sentences should split)

        Args:
            context: EnrichedPromptContext from NLP preprocessing

        Returns:
            Formatted string to inject into prompt template
        """
        sections = []

        # Entity summary
        if context.entity_summary:
            sections.append(f"**Detected Entities**: {context.entity_summary}")

        # Negation warnings (CRITICAL for accuracy)
        if context.negation_summary:
            sections.append(
                f"**CRITICAL - Negations Detected**: {context.negation_summary}\n"
                "You MUST preserve these negations exactly. Do NOT convert negated findings to positive statements."
            )

        # Atomicity recommendations
        if context.atomicity_summary:
            sections.append(f"**Atomicity Analysis**: {context.atomicity_summary}")

        # Detailed split recommendations
        split_recs = [fc for fc in context.fact_candidates if fc.split_recommendation]
        if split_recs:
            split_details = []
            for fc in split_recs:
                rec = fc.split_recommendation
                split_details.append(
                    f"- Sentence {rec.sentence_index + 1}: {rec.reason}"
                )
            sections.append(
                "**Split Recommendations**:\n" + "\n".join(split_details)
            )

        # Key entities to preserve (medications, diseases with context)
        key_entities = self._get_key_entities(context)
        if key_entities:
            sections.append(
                "**Key Medical Terms** (preserve exactly as written):\n" +
                "\n".join(f"- {e}" for e in key_entities)
            )

        if not sections:
            return ""

        return (
            "\n\n---\n"
            "## NLP ANALYSIS (Use this to guide extraction)\n\n" +
            "\n\n".join(sections) +
            "\n---\n"
        )

    def _get_key_entities(self, context: EnrichedPromptContext) -> List[str]:
        """Extract key entities that should be preserved exactly.

        Prioritizes:
        - Negated entities (critical to preserve negation)
        - Medications with modifiers
        - Diseases
        - Lab values with thresholds
        """
        from ....infrastructure.models.nlp_artifacts import EntityType

        key_entities = []
        seen = set()

        for entity in context.nlp_artifacts.entities:
            # Skip if already seen
            if entity.text.lower() in seen:
                continue
            seen.add(entity.text.lower())

            # Prioritize negated entities
            if entity.is_negated:
                trigger = entity.negation_trigger or "negated"
                key_entities.append(f"{entity.text} ({trigger})")
                continue

            # Include medications, diseases, quantities
            if entity.entity_type in (
                EntityType.MEDICATION,
                EntityType.DISEASE,
                EntityType.QUANTITY,
                EntityType.LAB_VALUE,
            ):
                if entity.modifiers:
                    mods = ", ".join(entity.modifiers)
                    key_entities.append(f"{entity.text} ({mods})")
                else:
                    key_entities.append(entity.text)

        return key_entities[:15]  # Limit to avoid prompt bloat
