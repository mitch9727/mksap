"""
Pipeline orchestrator - Coordinates 4-step statement generation workflow.

Manages the flow: critique extraction → key points extraction → cloze identification → text normalization
"""

import logging
from pathlib import Path

from .cloze_identifier import ClozeIdentifier
from .critique_processor import CritiqueProcessor
from .file_io import QuestionFileIO
from .keypoints_processor import KeyPointsProcessor
from .llm_client import ClaudeClient
from .models import ProcessingResult, TrueStatements
from .text_normalizer import TextNormalizer

logger = logging.getLogger(__name__)


class StatementPipeline:
    """Orchestrate 3-step statement generation workflow"""

    def __init__(
        self, client: ClaudeClient, file_io: QuestionFileIO, prompts_path: Path
    ):
        self.client = client
        self.file_io = file_io

        # Initialize processors
        self.critique_processor = CritiqueProcessor(
            client, prompts_path / "critique_extraction.md"
        )
        self.keypoints_processor = KeyPointsProcessor(
            client, prompts_path / "keypoints_extraction.md"
        )
        self.cloze_identifier = ClozeIdentifier(
            client, prompts_path / "cloze_identification.md"
        )
        self.text_normalizer = TextNormalizer()

    def process_question(self, question_file: Path) -> ProcessingResult:
        """
        Process single question through 4-step pipeline.

        Args:
            question_file: Path to question JSON file

        Returns:
            ProcessingResult with success/failure info

        Flow:
            1. Read question
            2. Extract statements from critique
            3. Extract statements from key_points
            4. Identify cloze candidates for all statements
            5. Normalize mathematical notation (less than → <, etc.)
            6. Split back into categories
            7. Augment and save JSON
        """
        try:
            # Read question
            data = self.file_io.read_question(question_file)
            question_id = data["question_id"]

            logger.info(f"Processing {question_id}")

            # Step 1: Extract from critique
            logger.debug("Step 1: Extracting statements from critique")
            critique_statements = self.critique_processor.extract_statements(
                data["critique"], data.get("educational_objective", "")
            )

            # Step 2: Extract from key_points
            logger.debug("Step 2: Extracting statements from key_points")
            keypoint_statements = self.keypoints_processor.extract_statements(
                data.get("key_points", [])
            )

            # Step 3: Identify cloze candidates for all statements
            logger.debug("Step 3: Identifying cloze candidates")
            all_statements = critique_statements + keypoint_statements
            all_statements = self.cloze_identifier.identify_cloze_candidates(
                all_statements
            )

            # Step 4: Normalize mathematical notation
            logger.debug("Step 4: Normalizing mathematical notation")
            all_statements = self.text_normalizer.normalize_statements(all_statements)

            # Split back into categories
            critique_final = all_statements[: len(critique_statements)]
            keypoint_final = all_statements[len(critique_statements) :]

            # Build TrueStatements
            true_statements = TrueStatements(
                from_critique=critique_final, from_key_points=keypoint_final
            )

            # Augment and save
            augmented_data = self.file_io.augment_with_statements(data, true_statements)
            self.file_io.write_question(question_file, augmented_data)

            total_statements = len(critique_final) + len(keypoint_final)
            logger.info(f"✓ {question_id}: {total_statements} statements extracted")

            return ProcessingResult(
                question_id=question_id,
                success=True,
                statements_extracted=total_statements,
                api_calls=3,  # critique, keypoints, cloze
            )

        except Exception as e:
            logger.error(f"Failed to process {question_file}: {e}", exc_info=True)
            return ProcessingResult(
                question_id=question_file.stem,
                success=False,
                statements_extracted=0,
                error=str(e),
            )
