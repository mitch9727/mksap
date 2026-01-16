"""
Hybrid vs Legacy Mode Comparison

Compares hybrid pipeline (NLP-guided) vs legacy pipeline (LLM-only)
on the same question to evaluate improvement in:
- Negation preservation
- Entity completeness
- Statement quality
- Processing time

Usage:
    ./scripts/python tests/tools/hybrid_vs_legacy_comparison.py <question_id>

Example:
    ./scripts/python tests/tools/hybrid_vs_legacy_comparison.py cvcor25002
"""

import json
import logging
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class PipelineStats:
    """Statistics for a pipeline run"""
    mode: str  # "legacy" or "hybrid"
    processing_time: float
    statements_extracted: int
    nlp_entities: int = 0
    nlp_negations: int = 0
    statement_negations: int = 0
    missing_entities: int = 0
    unit_mismatches: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def load_question_data(question_id: str) -> Tuple[str, str, List[str], str]:
    """Load question data"""
    # Look for mksap_data in parent directory (project root)
    project_root = Path(__file__).parent.parent.parent.parent
    mksap_data = project_root / "mksap_data"

    # Find question file
    for system_dir in mksap_data.iterdir():
        if not system_dir.is_dir():
            continue
        question_file = system_dir / question_id / f"{question_id}.json"
        if question_file.exists():
            with open(question_file) as f:
                data = json.load(f)
            return (
                data.get("critique", ""),
                data.get("educational_objective", ""),
                data.get("key_points", []),
                str(question_file.parent),
            )

    raise FileNotFoundError(f"Question {question_id} not found in {mksap_data}")


def test_legacy_mode(critique: str, educational_objective: str, key_points: List[str]) -> PipelineStats:
    """Test legacy (LLM-only) mode - NLP disabled"""
    import time

    logger.info("\n" + "="*60)
    logger.info("Testing LEGACY MODE (NLP disabled)")
    logger.info("="*60)

    # Disable NLP
    os.environ["MKSAP_USE_NLP"] = "false"

    try:
        from src.validation.nlp_utils import get_nlp
        get_nlp.cache_clear()

        start_time = time.time()

        logger.warning("Note: Legacy mode would call LLM (requires API credentials)")
        logger.info("This test only measures NLP component overhead")

        processing_time = time.time() - start_time

        stats = PipelineStats(
            mode="legacy",
            processing_time=0.0,  # Can't measure LLM time without credentials
            statements_extracted=0,
            nlp_entities=0,
            nlp_negations=0,
        )

        logger.info(f"Legacy mode: NLP disabled")
        return stats

    finally:
        os.environ.pop("MKSAP_USE_NLP", None)
        get_nlp.cache_clear()


def test_hybrid_mode(critique: str, educational_objective: str, key_points: List[str]) -> PipelineStats:
    """Test hybrid (NLP-guided) mode"""
    import time
    from src.processing.nlp.preprocessor import NLPPreprocessor
    from src.infrastructure.config.settings import NLPConfig
    from src.validation.nlp_utils import get_nlp

    logger.info("\n" + "="*60)
    logger.info("Testing HYBRID MODE (NLP-guided)")
    logger.info("="*60)

    # Enable hybrid mode
    os.environ["USE_HYBRID_PIPELINE"] = "true"
    get_nlp.cache_clear()

    try:
        config = NLPConfig.from_env()
        preprocessor = NLPPreprocessor(config)

        start_time = time.time()

        # Process critique and keypoints
        critique_context = preprocessor.process_and_enrich(critique, "critique")
        keypoints_text = " ".join(key_points) if key_points else ""
        keypoints_context = None
        if keypoints_text:
            keypoints_context = preprocessor.process_and_enrich(keypoints_text, "keypoints")

        processing_time = time.time() - start_time

        # Aggregate stats
        total_entities = len(critique_context.nlp_artifacts.entities)
        if keypoints_context:
            total_entities += len(keypoints_context.nlp_artifacts.entities)

        total_negations = len([
            e for e in critique_context.nlp_artifacts.entities if e.is_negated
        ])
        if keypoints_context:
            total_negations += len([
                e for e in keypoints_context.nlp_artifacts.entities if e.is_negated
            ])

        stats = PipelineStats(
            mode="hybrid",
            processing_time=processing_time,
            statements_extracted=len(critique_context.fact_candidates) + (
                len(keypoints_context.fact_candidates) if keypoints_context else 0
            ),
            nlp_entities=total_entities,
            nlp_negations=total_negations,
        )

        logger.info(f"Entities detected: {stats.nlp_entities}")
        logger.info(f"Negations detected: {stats.nlp_negations}")
        logger.info(f"Fact candidates: {stats.statements_extracted}")
        logger.info(f"Processing time: {stats.processing_time:.2f}s")

        # Show NLP guidance
        logger.info("\n📊 Entity Summary (Critique):")
        logger.info(f"  {critique_context.entity_summary}")
        if critique_context.negation_summary:
            logger.info("\n⚠️  Negation Summary (Critique):")
            logger.info(f"  {critique_context.negation_summary}")

        return stats

    finally:
        os.environ.pop("USE_HYBRID_PIPELINE", None)
        get_nlp.cache_clear()


def compare_modes(legacy_stats: PipelineStats, hybrid_stats: PipelineStats) -> None:
    """Compare pipeline modes"""
    logger.info("\n" + "="*60)
    logger.info("COMPARISON SUMMARY")
    logger.info("="*60)

    if legacy_stats.processing_time == 0:
        logger.warning("Legacy mode test unavailable - requires LLM credentials")
        logger.info("\n📊 Hybrid Mode Results:")
        logger.info(f"  Entities detected: {hybrid_stats.nlp_entities}")
        logger.info(f"  Negations detected: {hybrid_stats.nlp_negations}")
        logger.info(f"  Fact candidates: {hybrid_stats.statements_extracted}")
        logger.info(f"  Processing time: {hybrid_stats.processing_time:.2f}s")
        return

    logger.info("\n⏱️  PROCESSING TIME")
    logger.info("-" * 60)
    logger.info(f"Legacy mode: {legacy_stats.processing_time:.2f}s")
    logger.info(f"Hybrid mode: {hybrid_stats.processing_time:.2f}s")

    if hybrid_stats.processing_time < legacy_stats.processing_time:
        improvement = (legacy_stats.processing_time - hybrid_stats.processing_time) / legacy_stats.processing_time * 100
        logger.info(f"✓ Hybrid is {improvement:.1f}% faster")
    else:
        overhead = (hybrid_stats.processing_time - legacy_stats.processing_time) / legacy_stats.processing_time * 100
        logger.info(f"✗ Hybrid has {overhead:.1f}% overhead (NLP analysis time)")

    logger.info("\n📊 ENTITY & NEGATION DETECTION (Hybrid only)")
    logger.info("-" * 60)
    logger.info(f"Entities found: {hybrid_stats.nlp_entities}")
    logger.info(f"Negations detected: {hybrid_stats.nlp_negations}")
    if hybrid_stats.nlp_entities > 0:
        negation_rate = hybrid_stats.nlp_negations / hybrid_stats.nlp_entities * 100
        logger.info(f"Negation rate: {negation_rate:.1f}%")


def main():
    """Main comparison function"""
    if len(sys.argv) < 2:
        logger.error("Usage: python hybrid_vs_legacy_comparison.py <question_id>")
        sys.exit(1)

    question_id = sys.argv[1]

    logger.info(f"Loading question: {question_id}")
    critique, educational_objective, key_points, question_dir = load_question_data(question_id)
    logger.info(f"Critique: {len(critique)} chars")
    logger.info(f"Key points: {len(key_points)} items")

    # Test modes
    legacy_stats = test_legacy_mode(critique, educational_objective, key_points)
    hybrid_stats = test_hybrid_mode(critique, educational_objective, key_points)

    # Compare
    compare_modes(legacy_stats, hybrid_stats)

    logger.info("\n" + "="*60)
    logger.info("✓ Comparison complete")
    logger.info("="*60)


if __name__ == "__main__":
    main()
