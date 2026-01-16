"""
Pipeline orchestrator - Coordinates 4-step statement generation workflow.

Manages the flow: critique extraction → key points extraction → cloze identification → text normalization

Hybrid Mode (USE_HYBRID_PIPELINE=true):
  Adds NLP preprocessing stage using scispaCy to extract entities, detect negations,
  and analyze atomicity before LLM calls. In Phase 1, this only logs artifacts
  without changing output behavior.
"""

import logging
from pathlib import Path
from typing import Optional

from ..processing.cloze.identifier import ClozeIdentifier
from ..processing.statements.extractors.critique import CritiqueProcessor
from ..infrastructure.io.file_handler import QuestionFileIO
from ..processing.statements.extractors.keypoints import KeyPointsProcessor
from ..infrastructure.llm.client import ClaudeClient
from ..infrastructure.config.settings import NLPConfig
from ..infrastructure.models.data_models import ProcessingResult, Statement, TableStatement, TableStatements, TrueStatements
from ..processing.tables.extractor import TableProcessor
from ..processing.normalization.text_normalizer import TextNormalizer

logger = logging.getLogger(__name__)


class StatementPipeline:
    """Orchestrate statement generation workflow.

    Supports two modes:
    - Legacy mode (default): Direct LLM extraction
    - Hybrid mode (USE_HYBRID_PIPELINE=true): NLP preprocessing + LLM extraction
    """

    def __init__(
        self,
        client: ClaudeClient,
        file_io: QuestionFileIO,
        prompts_path: Path,
        nlp_config: Optional[NLPConfig] = None,
    ):
        self.client = client
        self.file_io = file_io

        # Load NLP config (determines hybrid vs legacy mode)
        self.nlp_config = nlp_config or NLPConfig.from_env()
        self.use_hybrid = self.nlp_config.use_hybrid_pipeline

        # Initialize NLP preprocessor if hybrid mode enabled
        self._nlp_preprocessor = None
        if self.use_hybrid:
            try:
                from ..processing.nlp.preprocessor import NLPPreprocessor
                self._nlp_preprocessor = NLPPreprocessor(self.nlp_config)
                logger.info("Hybrid pipeline enabled - NLP preprocessing active")
            except Exception as e:
                logger.warning(f"Failed to initialize NLP preprocessor: {e}. Falling back to legacy mode.")
                self.use_hybrid = False

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

            # Hybrid mode: NLP preprocessing to guide LLM extraction
            critique_nlp_context = None
            keypoints_nlp_context = None
            if self.use_hybrid and self._nlp_preprocessor:
                critique_nlp_context, keypoints_nlp_context = self._run_nlp_preprocessing(
                    question_id, data
                )

            # Step 1: Extract from critique (with optional NLP guidance)
            logger.debug("Step 1: Extracting statements from critique")
            critique_statements = self.critique_processor.extract_statements(
                data["critique"],
                data.get("educational_objective", ""),
                nlp_context=critique_nlp_context,
            )

            # Step 2: Extract from key_points (with optional NLP guidance)
            logger.debug("Step 2: Extracting statements from key_points")
            keypoint_statements = self.keypoints_processor.extract_statements(
                data.get("key_points", []),
                nlp_context=keypoints_nlp_context,
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

    def _run_nlp_preprocessing(
        self, question_id: str, data: dict
    ) -> tuple[Optional["EnrichedPromptContext"], Optional["EnrichedPromptContext"]]:
        """Run NLP preprocessing on question data for hybrid mode.

        Processes critique and key_points through scispaCy pipeline to extract:
        - Entities (diseases, medications, procedures, etc.)
        - Negation detection
        - Atomicity analysis (should_split vs multi_cloze_ok)

        Returns enriched prompt contexts for injection into LLM prompts.

        Args:
            question_id: Question identifier for logging
            data: Question data dict containing critique, key_points, etc.

        Returns:
            Tuple of (critique_context, keypoints_context), either may be None
        """
        from ..infrastructure.models.fact_candidates import EnrichedPromptContext

        logger.debug(f"[Hybrid] Running NLP preprocessing for {question_id}")

        critique_context: Optional[EnrichedPromptContext] = None
        keypoints_context: Optional[EnrichedPromptContext] = None

        try:
            # Process critique
            critique_text = data.get("critique", "")
            if critique_text:
                critique_context = self._nlp_preprocessor.process_and_enrich(
                    critique_text, "critique"
                )
                negated_count = len([
                    e for e in critique_context.nlp_artifacts.entities if e.is_negated
                ])
                logger.debug(
                    f"[Hybrid] Critique NLP: {len(critique_context.nlp_artifacts.sentences)} sentences, "
                    f"{len(critique_context.nlp_artifacts.entities)} entities, "
                    f"{negated_count} negated"
                )

            # Process key_points (join into single text for NLP)
            key_points = data.get("key_points", [])
            if key_points:
                keypoints_text = " ".join(key_points)
                keypoints_context = self._nlp_preprocessor.process_and_enrich(
                    keypoints_text, "keypoints"
                )
                negated_count = len([
                    e for e in keypoints_context.nlp_artifacts.entities if e.is_negated
                ])
                logger.debug(
                    f"[Hybrid] Keypoints NLP: {len(keypoints_context.nlp_artifacts.sentences)} sentences, "
                    f"{len(keypoints_context.nlp_artifacts.entities)} entities, "
                    f"{negated_count} negated"
                )

            logger.debug(f"[Hybrid] NLP preprocessing complete for {question_id}")

        except Exception as e:
            # NLP errors should not fail the pipeline - fall back to legacy mode
            logger.warning(f"[Hybrid] NLP preprocessing failed for {question_id}: {e}")
            critique_context = None
            keypoints_context = None

        return critique_context, keypoints_context
