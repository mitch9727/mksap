"""
Pipeline orchestrator - Coordinates 4-step statement generation workflow.

Manages the flow: critique extraction → key points extraction → cloze identification → text normalization
"""

import logging
from pathlib import Path

from .processing.cloze.identifier import ClozeIdentifier
from .processing.statements.extractors.critique import CritiqueProcessor
from .infrastructure.io.file_handler import QuestionFileIO
from .processing.statements.extractors.keypoints import KeyPointsProcessor
from .infrastructure.llm.client import ClaudeClient
from .infrastructure.models.data_models import ProcessingResult, Statement, TableStatement, TableStatements, TrueStatements
from .processing.tables.extractor import TableProcessor
from .processing.normalization.text_normalizer import TextNormalizer

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
        self.table_processor = TableProcessor(
            client, prompts_path / "table_extraction.md"
        )
        self.cloze_identifier = ClozeIdentifier(
            client, prompts_path / "cloze_identification.md"
        )
        self.text_normalizer = TextNormalizer()

    def process_question(self, question_file: Path) -> ProcessingResult:
        """
        Process single question through 5-step pipeline.

        Args:
            question_file: Path to question JSON file

        Returns:
            ProcessingResult with success/failure info

        Flow:
            1. Read question
            2. Extract statements from critique
            3. Extract statements from key_points
            4. Extract statements from tables (NEW)
            5. Identify cloze candidates for all statements
            6. Normalize mathematical notation (less than → <, etc.)
            7. Split back into categories
            8. Augment and save JSON
        """
        try:
            # Read question
            data = self.file_io.read_question(question_file)
            question_id = data["question_id"]
            question_dir = question_file.parent

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

            # Step 3: Extract from tables (NEW)
            logger.debug("Step 3: Extracting statements from tables")
            table_statements_list = self.table_processor.extract_statements(question_dir)

            # Step 4: Identify cloze candidates (updated to include tables)
            logger.debug("Step 4: Identifying cloze candidates")

            # Convert TableStatement → Statement for cloze processing
            table_statements_plain = [
                Statement(
                    statement=ts.statement,
                    extra_field=ts.extra_field,
                    cloze_candidates=[]
                )
                for ts in table_statements_list
            ]

            all_statements = critique_statements + keypoint_statements + table_statements_plain
            all_statements = self.cloze_identifier.identify_cloze_candidates(
                all_statements
            )

            # Step 5: Normalize mathematical notation
            logger.debug("Step 5: Normalizing mathematical notation")
            all_statements = self.text_normalizer.normalize_statements(all_statements)

            # Split back into categories
            critique_final = all_statements[: len(critique_statements)]
            keypoint_final = all_statements[
                len(critique_statements):len(critique_statements) + len(keypoint_statements)
            ]
            table_final_plain = all_statements[len(critique_statements) + len(keypoint_statements):]

            # Reconstruct TableStatement objects with cloze candidates and table_source
            table_final = [
                TableStatement(
                    statement=stmt.statement,
                    extra_field=stmt.extra_field,
                    cloze_candidates=stmt.cloze_candidates,
                    table_source=table_statements_list[i].table_source
                )
                for i, stmt in enumerate(table_final_plain)
            ]

            # Build separate containers
            true_statements = TrueStatements(
                from_critique=critique_final, from_key_points=keypoint_final
            )

            table_statements = TableStatements(
                statements=table_final,
                tables_processed=len(set(ts.table_source for ts in table_final)) if table_final else 0,
                tables_skipped=self.table_processor.last_skipped_count
            )

            # Augment and save
            augmented_data = self.file_io.augment_with_statements(data, true_statements)
            augmented_data["table_statements"] = table_statements.model_dump()
            self.file_io.write_question(question_file, augmented_data)

            total_statements = len(critique_final) + len(keypoint_final) + len(table_final)
            api_calls = 3 + table_statements.tables_processed  # critique, keypoints, cloze, tables

            logger.info(
                f"✓ {question_id}: {total_statements} statements extracted "
                f"({len(table_final)} from tables, {table_statements.tables_skipped} lab-values skipped)"
            )

            return ProcessingResult(
                question_id=question_id,
                success=True,
                statements_extracted=total_statements,
                api_calls=api_calls,
            )

        except Exception as e:
            logger.error(f"Failed to process {question_file}: {e}", exc_info=True)
            return ProcessingResult(
                question_id=question_file.stem,
                success=False,
                statements_extracted=0,
                error=str(e),
            )
