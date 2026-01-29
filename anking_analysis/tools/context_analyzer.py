"""
Context Analyzer for AnKing Analysis Pipeline - Phase 2 Task 3.3

Analyzes clinical context preservation: whether extra field is present,
how well context is embedded, and what types of clinical context are provided.
"""

from typing import Dict, List

from anking_analysis.models import AnkingCard, CardContextMetrics


class ContextAnalyzer:
    """
    Analyzes the context preservation of AnKing flashcard statements.

    Measures:
    - Whether extra field is present and populated
    - How well context is embedded in the main text
    - Types of context provided (pathophysiology, differential, clinical pearls, etc.)
    - Whether understanding the front requires reading the extra field
    """

    def analyze(self, card: AnkingCard) -> CardContextMetrics:
        """
        Analyze the context preservation of a single card.

        Args:
            card: AnkingCard to analyze

        Returns:
            CardContextMetrics with context analysis results
        """
        # 1. Check Extra field usage
        has_extra = card.extra is not None and len(card.extra.strip()) > 0
        extra_length = len(card.extra_plain) if card.extra_plain else 0

        # 2. Classify context types
        context_types = []
        if has_extra:
            extra_lower = card.extra_plain.lower()
            if any(
                kw in extra_lower
                for kw in ["mechanism", "pathophysiology", "cause", "caused by"]
            ):
                context_types.append("pathophysiology")
            if any(
                kw in extra_lower
                for kw in ["differential", "also consider", "other causes", "ddx"]
            ):
                context_types.append("differential")
            if any(
                kw in extra_lower
                for kw in ["pearl", "tip", "remember", "note", "clinical pearl"]
            ):
                context_types.append("clinical_pearls")

        # 3. Assess standalone quality
        # Simple heuristic: if card text is very short without Extra, likely requires it
        requires_extra = has_extra and len(card.text_plain) < 50

        # Check if context is embedded in main text
        context_keywords = [
            "because",
            "due to",
            "caused by",
            "characterized by",
            "resulting from",
        ]
        context_embedded = any(kw in card.text_plain.lower() for kw in context_keywords)

        return CardContextMetrics(
            card_id=card.note_id,
            has_extra_field=has_extra,
            extra_field_length=extra_length,
            requires_extra=requires_extra,
            context_embedded=context_embedded,
            context_types=context_types,
        )

    def aggregate_metrics(self, metrics_list: List[CardContextMetrics]) -> Dict:
        """
        Aggregate context metrics across multiple cards.

        Args:
            metrics_list: List of CardContextMetrics to aggregate

        Returns:
            Dictionary with aggregated metrics including percentages and distributions
        """
        if not metrics_list:
            return {}

        total = len(metrics_list)

        # Aggregate context types
        all_types = {}
        for m in metrics_list:
            for ctype in m.context_types:
                all_types[ctype] = all_types.get(ctype, 0) + 1

        # Calculate extra field lengths (excluding cards without extra)
        extra_lengths = [m.extra_field_length for m in metrics_list if m.has_extra_field]

        return {
            "cards_with_extra": sum(1 for m in metrics_list if m.has_extra_field),
            "percentage_with_extra": (
                sum(1 for m in metrics_list if m.has_extra_field) / total
            )
            * 100,
            "avg_extra_length": (
                sum(extra_lengths) / len(extra_lengths) if extra_lengths else 0
            ),
            "min_extra_length": min(extra_lengths) if extra_lengths else 0,
            "max_extra_length": max(extra_lengths) if extra_lengths else 0,
            "cards_requiring_extra": sum(1 for m in metrics_list if m.requires_extra),
            "percentage_requiring_extra": (
                sum(1 for m in metrics_list if m.requires_extra) / total
            )
            * 100,
            "cards_with_embedded_context": sum(
                1 for m in metrics_list if m.context_embedded
            ),
            "percentage_with_embedded_context": (
                sum(1 for m in metrics_list if m.context_embedded) / total
            )
            * 100,
            "context_type_distribution": all_types,
            "total_cards": total,
        }
