"""
Structure Analyzer for AnKing Analysis Pipeline - Phase 2 Task 3.1

Analyzes statement structure: length, complexity, atomicity, and compound indicators.

Uses scispaCy NLP model for sentence segmentation and complexity analysis.
"""

from typing import Dict, List
import statistics

from anking_analysis.models import AnkingCard, CardStructureMetrics
from statement_generator.src.validation.nlp_utils import get_nlp


class StructureAnalyzer:
    """
    Analyzes the structural properties of AnKing flashcard statements.

    Measures:
    - Text length and word count
    - Sentence count and average sentence length
    - Presence of lists and formatting
    - Atomicity score (0-1, where 1 = single concept)
    - Compound indicators suggesting multi-concept statements
    """

    def __init__(self):
        """Initialize with cached scispaCy NLP model."""
        self.nlp = get_nlp()

    def analyze(self, card: AnkingCard) -> CardStructureMetrics:
        """
        Analyze the structure of a single card.

        Args:
            card: AnkingCard to analyze

        Returns:
            CardStructureMetrics with structure analysis results
        """
        # 1. Count sentences using scispaCy
        doc = self.nlp(card.text_plain)
        sentences = list(doc.sents)

        # 2. Calculate basic metrics
        text_length = len(card.text_plain)
        word_count = len(card.text_plain.split())
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

        # 3. Detect compound indicators
        compound_indicators = []
        if ";" in card.text_plain:
            compound_indicators.append("semicolon")
        if card.text_plain.count(" and ") > 1:
            compound_indicators.append("multiple_and")
        if card.text_plain.count(",") > 2:
            compound_indicators.append("many_commas")

        # 4. Calculate atomicity score (0-1, where 1 = single concept)
        # Heuristic: more compound indicators = lower atomicity
        atomicity_score = max(0, 1.0 - (len(compound_indicators) * 0.3))

        return CardStructureMetrics(
            card_id=card.note_id,
            text_length=text_length,
            text_word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            has_lists="<ul>" in card.text or "<ol>" in card.text,
            has_formatting=card.html_features.get("uses_bold", False)
            or card.html_features.get("uses_italic", False),
            atomicity_score=atomicity_score,
            compound_indicators=compound_indicators,
        )

    def aggregate_metrics(self, metrics_list: List[CardStructureMetrics]) -> Dict:
        """
        Aggregate structure metrics across multiple cards.

        Args:
            metrics_list: List of CardStructureMetrics to aggregate

        Returns:
            Dictionary with aggregated metrics including averages, medians, and counts
        """
        if not metrics_list:
            return {}

        lengths = [m.text_length for m in metrics_list]
        word_counts = [m.text_word_count for m in metrics_list]
        atomicity_scores = [m.atomicity_score for m in metrics_list]
        sentence_counts = [m.sentence_count for m in metrics_list]
        avg_sentence_lengths = [m.avg_sentence_length for m in metrics_list]

        return {
            "avg_text_length": sum(lengths) / len(lengths),
            "median_text_length": statistics.median(lengths),
            "min_text_length": min(lengths),
            "max_text_length": max(lengths),
            "avg_word_count": sum(word_counts) / len(word_counts),
            "median_word_count": statistics.median(word_counts),
            "min_word_count": min(word_counts),
            "max_word_count": max(word_counts),
            "avg_sentence_count": sum(sentence_counts) / len(sentence_counts),
            "median_sentence_count": statistics.median(sentence_counts),
            "avg_sentence_length": sum(avg_sentence_lengths) / len(avg_sentence_lengths),
            "median_sentence_length": statistics.median(avg_sentence_lengths),
            "avg_atomicity_score": sum(atomicity_scores) / len(atomicity_scores),
            "median_atomicity_score": statistics.median(atomicity_scores),
            "cards_with_formatting": sum(1 for m in metrics_list if m.has_formatting),
            "cards_with_lists": sum(1 for m in metrics_list if m.has_lists),
            "percentage_with_formatting": (
                sum(1 for m in metrics_list if m.has_formatting) / len(metrics_list)
            )
            * 100,
            "percentage_with_lists": (
                sum(1 for m in metrics_list if m.has_lists) / len(metrics_list)
            )
            * 100,
            "total_cards": len(metrics_list),
        }
