"""
NLP Model Verification Tool

Verifies the production scispaCy model (en_core_sci_sm) on a test question
to confirm medical entity extraction, negation detection, and atomicity analysis.

NOTE: Medium and Large models have been removed from the system (Jan 16, 2026).
Only en_core_sci_sm is retained - it provides 14x faster processing (0.24s vs 3.5s+)
with 94% entity detection accuracy and identical negation detection.

Usage:
    ./scripts/python tests/tools/nlp_model_comparison.py <question_id> [--detailed]

Example:
    ./scripts/python tests/tools/nlp_model_comparison.py cvcor25002 --detailed
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import sys
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ModelStats:
    """Statistics for a single model run"""
    model_name: str
    model_path: str
    sentences: int
    entities: int
    negated_entities: int
    split_recommendations: int
    entity_types: Dict[str, int]
    negation_triggers: List[str]
    processing_time: float


def load_question_data(question_id: str) -> Tuple[str, str, List[str]]:
    """Load critique and keypoints for a question"""
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
                data.get("key_points", [])
            )

    raise FileNotFoundError(f"Question {question_id} not found in {mksap_data}")


def test_model(model_path: str, critique: str, model_name: str = None) -> ModelStats:
    """Test a single model on the critique"""
    import time
    from src.infrastructure.config.settings import NLPConfig
    from src.processing.nlp.preprocessor import NLPPreprocessor
    from src.validation.nlp_utils import get_nlp
    import os

    if model_name is None:
        model_name = Path(model_path).name

    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {model_name}")
    logger.info(f"Path: {model_path}")
    logger.info(f"{'='*60}")

    # Clear cache and temporarily override model path
    get_nlp.cache_clear()
    original_model = os.environ.get("MKSAP_NLP_MODEL")
    os.environ["MKSAP_NLP_MODEL"] = model_path

    try:
        config = NLPConfig.from_env()
        preprocessor = NLPPreprocessor(config)

        # Time the processing
        start_time = time.time()
        artifacts = preprocessor.process(critique, "critique")
        processing_time = time.time() - start_time

        # Extract statistics
        negated_entities = [e for e in artifacts.entities if e.is_negated]
        entity_type_counts = {}
        for entity in artifacts.entities:
            entity_type = entity.entity_type.value
            entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1

        negation_triggers = list(set(
            e.negation_trigger for e in negated_entities if e.negation_trigger
        ))

        stats = ModelStats(
            model_name=model_name,
            model_path=model_path,
            sentences=len(artifacts.sentences),
            entities=len(artifacts.entities),
            negated_entities=len(negated_entities),
            split_recommendations=len(artifacts.split_recommendations),
            entity_types=entity_type_counts,
            negation_triggers=negation_triggers,
            processing_time=processing_time,
        )

        # Log results
        logger.info(f"Sentences: {stats.sentences}")
        logger.info(f"Entities: {stats.entities}")
        logger.info(f"Negated: {stats.negated_entities}")
        logger.info(f"Split Recommendations: {stats.split_recommendations}")
        logger.info(f"Processing Time: {stats.processing_time:.2f}s")
        logger.info(f"Entity Types: {sorted(stats.entity_types.items())}")
        if stats.negation_triggers:
            logger.info(f"Negation Triggers: {', '.join(set(stats.negation_triggers))}")

        return stats

    finally:
        # Restore original model
        if original_model:
            os.environ["MKSAP_NLP_MODEL"] = original_model
        else:
            os.environ.pop("MKSAP_NLP_MODEL", None)
        get_nlp.cache_clear()


def compare_models(stats_list: List[ModelStats], detailed: bool = False) -> None:
    """Compare results across models"""
    logger.info(f"\n{'='*60}")
    logger.info("MODEL COMPARISON SUMMARY")
    logger.info(f"{'='*60}")

    # Entity detection comparison
    logger.info("\n📊 ENTITY DETECTION")
    logger.info("-" * 60)
    logger.info(f"{'Model':<25} {'Sentences':<12} {'Entities':<12} {'Negated':<12} {'Time (s)':<10}")
    logger.info("-" * 60)
    for stats in stats_list:
        logger.info(
            f"{stats.model_name:<25} {stats.sentences:<12} {stats.entities:<12} "
            f"{stats.negated_entities:<12} {stats.processing_time:<10.2f}"
        )

    # Negation detection comparison
    logger.info("\n🔍 NEGATION DETECTION")
    logger.info("-" * 60)
    for stats in stats_list:
        logger.info(f"\n{stats.model_name}:")
        if stats.negation_triggers:
            logger.info(f"  Found {len(stats.negation_triggers)} unique triggers: {', '.join(stats.negation_triggers)}")
        else:
            logger.info("  No negations detected")

    # Entity type distribution
    if detailed:
        logger.info("\n📋 ENTITY TYPE DISTRIBUTION")
        logger.info("-" * 60)
        all_types = set()
        for stats in stats_list:
            all_types.update(stats.entity_types.keys())

        for entity_type in sorted(all_types):
            logger.info(f"\n{entity_type}:")
            for stats in stats_list:
                count = stats.entity_types.get(entity_type, 0)
                logger.info(f"  {stats.model_name:<20}: {count}")

    # Ranking
    logger.info("\n🏆 MODEL RANKING")
    logger.info("-" * 60)

    # Score: entities * negated_entities / processing_time
    # Higher = better (more entities, more negations detected, faster)
    def score_model(stats):
        if stats.processing_time == 0:
            return 0
        return (stats.entities + stats.negated_entities * 2) / stats.processing_time

    ranked = sorted(stats_list, key=score_model, reverse=True)
    for i, stats in enumerate(ranked, 1):
        score = score_model(stats)
        logger.info(f"{i}. {stats.model_name:<20} (Score: {score:.1f})")

    logger.info("\nRanking factors: Entity detection (1x) + Negation detection (2x) / Processing time")


def main():
    """Main comparison function"""
    from src.validation.nlp_utils import get_nlp

    if len(sys.argv) < 2:
        logger.error("Usage: python nlp_model_comparison.py <question_id> [--detailed]")
        sys.exit(1)

    question_id = sys.argv[1]
    detailed = "--detailed" in sys.argv

    # Load question
    logger.info(f"Loading question: {question_id}")
    critique, educational_objective, key_points = load_question_data(question_id)
    logger.info(f"Critique: {len(critique)} chars")
    logger.info(f"Key points: {len(key_points)} items")

    # Define models to test
    base_path = Path("/Users/Mitchell/coding/projects/MKSAP/statement_generator/models")
    models_to_test = [
        (base_path / "en_core_sci_sm-0.5.4" / "en_core_sci_sm" / "en_core_sci_sm-0.5.4", "en_core_sci_sm (Small - 13MB) ⭐ PRODUCTION"),
    ]

    # Test each model
    results = []
    for model_path, model_name in models_to_test:
        if not model_path.exists():
            logger.warning(f"Skipping {model_name} - not found at {model_path}")
            continue

        try:
            stats = test_model(str(model_path), critique, model_name)
            results.append(stats)
        except Exception as e:
            logger.error(f"Error testing {model_name}: {e}")

    # Compare results
    if results:
        compare_models(results, detailed=detailed)
    else:
        logger.error("No models tested successfully")
        sys.exit(1)


if __name__ == "__main__":
    main()
