"""
AnKing Analysis Pipeline - Main Execution Script

Orchestrates the complete workflow:
1. Extract AnKing flashcards from Anki database
2. Analyze cards across 4 dimensions
3. Compare against MKSAP Phase 3 baseline
4. Generate comprehensive markdown reports
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

from anking_analysis.models import AnkingCard
from anking_analysis.tools import (
    AnkiExtractor,
    StructureAnalyzer,
    ClozeAnalyzer,
    ContextAnalyzer,
    FormattingAnalyzer,
    BaselineComparator,
    ReportGenerator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
ANKING_DATA_DIR = PROJECT_ROOT / "anking_analysis" / "data"
ANKING_RAW_DATA = ANKING_DATA_DIR / "raw" / "anking_cards.json"
ANKING_METRICS_FILE = ANKING_DATA_DIR / "processed" / "anking_metrics.json"
MKSAP_DATA_DIR = PROJECT_ROOT / "mksap_data"
REPORTS_DIR = PROJECT_ROOT / "anking_analysis" / "reports"

# Anki database path
ANKI_DB_PATH = Path.home() / "Library" / "Application Support" / "Anki2" / "Mitch" / "collection.anki2"


def create_directories():
    """Create necessary output directories."""
    ANKING_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (ANKING_DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (ANKING_DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Output directories created")


def extract_anking_cards(n_per_deck: int = 25) -> List[AnkingCard]:
    """
    Extract AnKing flashcards from Anki database.

    Args:
        n_per_deck: Number of cards to sample from each deck

    Returns:
        List of AnkingCard objects
    """
    logger.info(f"Connecting to Anki database at {ANKI_DB_PATH}")

    if not ANKI_DB_PATH.exists():
        raise FileNotFoundError(f"Anki database not found at {ANKI_DB_PATH}")

    with AnkiExtractor(ANKI_DB_PATH) as extractor:
        logger.info("Listing available decks...")
        decks = extractor.list_decks()
        logger.info(f"Found {len(decks)} decks with 25+ cards")

        for deck in decks:
            logger.info(f"  - {deck['name']} ({deck['card_count']} cards)")

        logger.info(f"Extracting {n_per_deck} cards per deck...")
        cards = extractor.extract_all_samples(n_per_deck=n_per_deck)
        logger.info(f"Extracted {len(cards)} total cards")

        return cards


def save_extracted_cards(cards: List[AnkingCard]) -> None:
    """Save extracted cards to JSON file."""
    ANKING_RAW_DATA.parent.mkdir(parents=True, exist_ok=True)

    cards_dict = [card.model_dump() for card in cards]
    with open(ANKING_RAW_DATA, 'w') as f:
        json.dump(cards_dict, f, indent=2)

    logger.info(f"Saved {len(cards)} cards to {ANKING_RAW_DATA}")


def analyze_cards(cards: List[AnkingCard]) -> Dict:
    """
    Analyze extracted AnKing cards using all 4 analyzers.

    Args:
        cards: List of AnkingCard objects to analyze

    Returns:
        Dictionary with aggregated metrics from all 4 analyzers
    """
    logger.info("Running Structure Analysis...")
    structure_analyzer = StructureAnalyzer()
    structure_metrics = [structure_analyzer.analyze(card) for card in cards]
    structure_agg = structure_analyzer.aggregate_metrics(structure_metrics)
    logger.info(f"  Structure: avg_text_length={structure_agg.get('avg_text_length', 0):.1f}")

    logger.info("Running Cloze Analysis...")
    cloze_analyzer = ClozeAnalyzer()
    cloze_metrics = [cloze_analyzer.analyze(card) for card in cards]
    cloze_agg = cloze_analyzer.aggregate_metrics(cloze_metrics)
    logger.info(f"  Cloze: avg_cloze_count={cloze_agg.get('avg_cloze_count', 0):.1f}")

    logger.info("Running Context Analysis...")
    context_analyzer = ContextAnalyzer()
    context_metrics = [context_analyzer.analyze(card) for card in cards]
    context_agg = context_analyzer.aggregate_metrics(context_metrics)
    logger.info(f"  Context: cards_with_extra={context_agg.get('cards_with_extra', 0)}")

    logger.info("Running Formatting Analysis...")
    formatting_analyzer = FormattingAnalyzer()
    formatting_metrics = [formatting_analyzer.analyze(card) for card in cards]
    formatting_agg = formatting_analyzer.aggregate_metrics(formatting_metrics)
    logger.info(f"  Formatting: cards_with_bold={formatting_agg.get('cards_with_bold', 0)}")

    return {
        'structure': structure_agg,
        'cloze': cloze_agg,
        'context': context_agg,
        'formatting': formatting_agg,
    }


def save_metrics(metrics: Dict) -> None:
    """Save analysis metrics to JSON file."""
    ANKING_METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(ANKING_METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Saved metrics to {ANKING_METRICS_FILE}")


def compare_with_baseline(anking_metrics: Dict) -> Dict:
    """
    Compare AnKing metrics against MKSAP Phase 3 baseline.

    Args:
        anking_metrics: Aggregated metrics from AnKing analysis

    Returns:
        Comparison results with deltas
    """
    logger.info("Loading MKSAP Phase 3 baseline...")
    comparator = BaselineComparator(MKSAP_DATA_DIR)

    logger.info("Analyzing MKSAP baseline...")
    mksap_metrics = comparator.analyze_mksap_baseline()

    logger.info("Comparing AnKing vs MKSAP...")
    comparison = comparator.compare(anking_metrics, mksap_metrics)

    return comparison, mksap_metrics


def generate_reports(
    cards: List[AnkingCard],
    anking_metrics: Dict,
    mksap_metrics: Dict,
    comparison: Dict,
) -> None:
    """
    Generate all three markdown reports.

    Args:
        cards: List of AnkingCard objects
        anking_metrics: AnKing aggregated metrics
        mksap_metrics: MKSAP aggregated metrics
        comparison: Comparison results
    """
    logger.info("Generating markdown reports...")
    generator = ReportGenerator(REPORTS_DIR)
    generator.generate_all_reports(
        anking_cards=cards,
        anking_metrics=anking_metrics,
        mksap_metrics=mksap_metrics,
        comparison=comparison,
    )

    logger.info(f"Reports generated in {REPORTS_DIR}")
    logger.info(f"  - ANKING_ANALYSIS.md")
    logger.info(f"  - MKSAP_VS_ANKING.md")
    logger.info(f"  - IMPROVEMENTS.md")


def main():
    """Main pipeline execution."""
    try:
        logger.info("=" * 80)
        logger.info("AnKing Analysis Pipeline - Starting")
        logger.info("=" * 80)

        # Setup
        create_directories()

        # Phase 1: Extract
        logger.info("\n[PHASE 1] EXTRACTION")
        logger.info("-" * 80)
        cards = extract_anking_cards(n_per_deck=25)
        save_extracted_cards(cards)

        # Phase 2: Analyze
        logger.info("\n[PHASE 2] ANALYSIS")
        logger.info("-" * 80)
        anking_metrics = analyze_cards(cards)
        save_metrics(anking_metrics)

        # Phase 3: Compare
        logger.info("\n[PHASE 3] COMPARISON")
        logger.info("-" * 80)
        comparison, mksap_metrics = compare_with_baseline(anking_metrics)

        # Phase 4: Report
        logger.info("\n[PHASE 4] REPORTING")
        logger.info("-" * 80)
        generate_reports(cards, anking_metrics, mksap_metrics, comparison)

        logger.info("\n" + "=" * 80)
        logger.info("AnKing Analysis Pipeline - COMPLETE ✓")
        logger.info("=" * 80)
        logger.info(f"\nResults available in:")
        logger.info(f"  Data: {ANKING_DATA_DIR}")
        logger.info(f"  Reports: {REPORTS_DIR}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
