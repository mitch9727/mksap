"""
Specialized NER Model Comparison Tool

Compares specialized NER models (bc5cdr, bionlp13cg) against the
core en_core_sci_sm model to evaluate if specialized entity recognition
provides benefits for medical statement extraction.

NOTE: These are NER-only models that require custom pipeline integration
for full functionality (sentence segmentation, negation detection, etc).

Usage:
    ./scripts/python tests/tools/specialized_ner_comparison.py <question_id>

Example:
    ./scripts/python tests/tools/specialized_ner_comparison.py cvcor25002
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class NERStats:
    """Statistics for a NER model run"""
    model_name: str
    model_path: str
    model_type: str  # "core" or "ner_only"
    sentences: int
    entities: int
    entity_types: Dict[str, int]
    processing_time: float
    has_full_pipeline: bool


def load_question_data(question_id: str) -> Tuple[str, str, List[str]]:
    """Load critique and keypoints for a question"""
    project_root = Path(__file__).parent.parent.parent.parent
    mksap_data = project_root / "mksap_data"

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


def test_model(model_path: str, critique: str, model_name: str = None) -> NERStats:
    """Test a model on the critique text"""
    import time
    import spacy
    import os

    if model_name is None:
        model_name = Path(model_path).name

    logger.info(f"\n{'='*70}")
    logger.info(f"Testing: {model_name}")
    logger.info(f"Path: {model_path}")
    logger.info(f"{'='*70}")

    try:
        # Load model
        start_time = time.time()
        nlp = spacy.load(model_path)
        load_time = time.time() - start_time

        # Determine model type
        has_parser = "parser" in nlp.pipe_names
        has_ner = "ner" in nlp.pipe_names
        model_type = "core" if has_parser else "ner_only"

        logger.info(f"Pipeline components: {nlp.pipe_names}")
        logger.info(f"Model type: {model_type} (parser: {has_parser}, ner: {has_ner})")

        # If NER-only, add sentencizer
        if model_type == "ner_only" and "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
            logger.info("Added sentencizer for NER-only model")

        # Process text
        start_time = time.time()
        doc = nlp(critique)
        processing_time = time.time() - start_time

        # Extract statistics
        sentences = list(doc.sents)
        entities = doc.ents
        entity_type_counts = {}
        for entity in entities:
            entity_type = entity.label_
            entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1

        stats = NERStats(
            model_name=model_name,
            model_path=model_path,
            model_type=model_type,
            sentences=len(sentences),
            entities=len(entities),
            entity_types=entity_type_counts,
            processing_time=processing_time,
            has_full_pipeline=has_parser,
        )

        # Log results
        logger.info(f"Sentences: {stats.sentences}")
        logger.info(f"Entities: {stats.entities}")
        logger.info(f"Processing Time: {stats.processing_time:.3f}s")
        logger.info(f"Entity Types: {sorted(stats.entity_types.items())}")
        logger.info(f"Full Pipeline: {'Yes' if has_parser else 'No (NER-only)'}")

        return stats

    except Exception as e:
        logger.error(f"Error testing {model_name}: {e}")
        raise


def compare_models(stats_list: List[NERStats]) -> None:
    """Compare results across models"""
    logger.info(f"\n{'='*70}")
    logger.info("COMPARISON SUMMARY")
    logger.info(f"{'='*70}")

    # Overview table
    logger.info("\n📊 NER MODEL COMPARISON")
    logger.info("-" * 70)
    logger.info(f"{'Model':<30} {'Type':<12} {'Entities':<12} {'Time (s)':<10}")
    logger.info("-" * 70)
    for stats in stats_list:
        logger.info(
            f"{stats.model_name:<30} {stats.model_type:<12} {stats.entities:<12} {stats.processing_time:<10.3f}"
        )

    # Entity type distribution
    logger.info("\n🏷️ ENTITY TYPE DISTRIBUTION")
    logger.info("-" * 70)

    all_types = set()
    for stats in stats_list:
        all_types.update(stats.entity_types.keys())

    for entity_type in sorted(all_types):
        logger.info(f"\n{entity_type}:")
        for stats in stats_list:
            count = stats.entity_types.get(entity_type, 0)
            bar = "█" * (count // 5) if count > 0 else "─"
            logger.info(f"  {stats.model_name:<28}: {count:>3} {bar}")

    # Key insights
    logger.info("\n💡 KEY INSIGHTS")
    logger.info("-" * 70)

    core_models = [s for s in stats_list if s.model_type == "core"]
    ner_only = [s for s in stats_list if s.model_type == "ner_only"]

    if core_models and ner_only:
        core_entities = core_models[0].entities
        logger.info(f"\nCore Model (en_core_sci_sm): {core_entities} entities")

        for ner_model in ner_only:
            delta = ner_model.entities - core_entities
            pct = (delta / core_entities * 100) if core_entities else 0
            sign = "+" if delta > 0 else ""
            logger.info(f"{ner_model.model_name}: {ner_model.entities} entities ({sign}{delta}, {pct:+.1f}%)")

    # Architecture comparison
    logger.info("\n🏗️ ARCHITECTURE ANALYSIS")
    logger.info("-" * 70)
    for stats in stats_list:
        features = []
        if stats.has_full_pipeline:
            features.append("Full pipeline")
        else:
            features.append("NER-only")
        logger.info(f"{stats.model_name}: {', '.join(features)}")


def main():
    """Main comparison function"""
    if len(sys.argv) < 2:
        logger.error("Usage: python specialized_ner_comparison.py <question_id>")
        sys.exit(1)

    question_id = sys.argv[1]

    # Load question
    logger.info(f"Loading question: {question_id}")
    critique, educational_objective, key_points = load_question_data(question_id)
    logger.info(f"Critique: {len(critique)} chars")
    logger.info(f"Key points: {len(key_points)} items")

    # Define models to test
    base_path = Path("/Users/Mitchell/coding/projects/MKSAP/statement_generator/models")
    models_to_test = [
        # Core model (baseline)
        (base_path / "en_core_sci_sm-0.5.4" / "en_core_sci_sm" / "en_core_sci_sm-0.5.4",
         "en_core_sci_sm (Core - 13MB)"),

        # Specialized NER models
        (base_path / "en_ner_bc5cdr_md-0.5.4" / "en_ner_bc5cdr_md" / "en_ner_bc5cdr_md-0.5.4",
         "en_ner_bc5cdr_md (Drug/Disease NER - 114MB)"),
        (base_path / "en_ner_bionlp13cg_md-0.5.4" / "en_ner_bionlp13cg_md" / "en_ner_bionlp13cg_md-0.5.4",
         "en_ner_bionlp13cg_md (BioNLP NER - 114MB)"),
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
        compare_models(results)
    else:
        logger.error("No models tested successfully")
        sys.exit(1)

    logger.info("\n" + "="*70)
    logger.info("✓ Comparison complete")
    logger.info("="*70)


if __name__ == "__main__":
    main()
