"""
Cloze Analyzer for AnKing Analysis Pipeline - Phase 2 Task 3.2

Analyzes cloze deletion patterns: count, types, positions.

Uses scispaCy NLP model for entity classification and cloze type detection.
"""

import re
from typing import Dict, List, Optional

from anking_analysis.models import AnkingCard, CardClozeMetrics
from statement_generator.src.validation.nlp_utils import get_nlp


class ClozeAnalyzer:
    """
    Analyzes the cloze deletion patterns in AnKing flashcard statements.

    Measures:
    - Total cloze count and unique cloze count
    - Cloze types (diagnosis, medication, mechanism, number, other) using NER
    - Cloze positions (beginning, middle, end)
    - Quality issues (nested clozes, trivial clozes)
    - Average cloze length
    """

    def __init__(self):
        """Initialize with cached scispaCy NLP model for entity classification."""
        self.nlp = get_nlp()

    def analyze(self, card: AnkingCard) -> CardClozeMetrics:
        """
        Analyze the cloze deletion patterns of a single card.

        Args:
            card: AnkingCard to analyze

        Returns:
            CardClozeMetrics with cloze pattern analysis results
        """
        # 1. Count clozes
        cloze_count = card.cloze_count
        unique_cloze_count = len(set(card.cloze_deletions))

        # 2. Classify cloze types using NER
        cloze_types_list = []
        for cloze_text in card.cloze_deletions:
            cloze_type = self.classify_cloze_type(cloze_text)
            cloze_types_list.append(cloze_type)

        # 3. Analyze positions
        cloze_positions = self.detect_positions(card.text_plain, card.cloze_deletions)

        # 4. Detect quality issues
        has_trivial = any(len(c.strip()) <= 3 for c in card.cloze_deletions)
        has_nested = self.detect_nested_clozes(card.text)

        # 5. Calculate average cloze length
        avg_cloze_length = (
            sum(len(c) for c in card.cloze_deletions) / cloze_count
            if cloze_count > 0
            else 0
        )

        return CardClozeMetrics(
            card_id=card.note_id,
            cloze_count=cloze_count,
            unique_cloze_count=unique_cloze_count,
            cloze_types=cloze_types_list,
            avg_cloze_length=avg_cloze_length,
            cloze_positions=self._positions_to_indices(cloze_positions),
            has_nested_clozes=has_nested,
            has_trivial_clozes=has_trivial,
        )

    def classify_cloze_type(self, cloze_text: str) -> str:
        """
        Classify cloze deletion type using NER and heuristics.

        Args:
            cloze_text: The cloze deletion text to classify

        Returns:
            Type label: 'diagnosis', 'medication', 'mechanism', 'number', or 'other'
        """
        # Check for numbers/units first
        if any(char.isdigit() for char in cloze_text):
            return "number"

        # Use NER if available
        if self.nlp is not None:
            doc = self.nlp(cloze_text)
            if doc.ents:
                ent_type = doc.ents[0].label_
                # Map scispaCy entity types to domain types
                type_mapping = {
                    "DISEASE": "diagnosis",
                    "DISORDER": "diagnosis",
                    "CHEMICAL": "medication",
                    "DRUG": "medication",
                    "GENE": "mechanism",
                    "PROTEIN": "mechanism",
                }
                return type_mapping.get(ent_type, "other")

        # Default
        return "other"

    def detect_positions(self, text: str, clozes: List[str]) -> List[str]:
        """
        Detect if clozes are at beginning, middle, or end of text.

        Args:
            text: Plain text to search
            clozes: List of cloze deletion texts

        Returns:
            List of position labels: 'beginning', 'middle', or 'end'
        """
        positions = []
        text_lower = text.lower()

        for cloze in clozes:
            cloze_lower = cloze.lower()

            # Check if at beginning (within first 10% or first occurrence)
            if text_lower.startswith(cloze_lower[:min(10, len(cloze_lower))]):
                positions.append("beginning")
            # Check if at end (within last 10% or last occurrence)
            elif text_lower.endswith(cloze_lower[-min(10, len(cloze_lower)) :]):
                positions.append("end")
            else:
                positions.append("middle")

        return positions

    def detect_nested_clozes(self, text: str) -> bool:
        """
        Detect if clozes are nested or overlapping.

        Nested clozes occur when one cloze deletion is contained within another
        or when their Anki markup spans overlap.

        Args:
            text: HTML text with cloze markup

        Returns:
            True if nested/overlapping clozes detected, False otherwise
        """
        # Regex for Anki cloze markup: {{c1::text}}, {{c2::text}}, etc.
        cloze_pattern = r"\{\{c\d+::([^}]+)\}\}"
        matches = list(re.finditer(cloze_pattern, text))

        # Check for overlapping ranges in the markup
        for i in range(len(matches)):
            for j in range(i + 1, len(matches)):
                m1_start, m1_end = matches[i].span()
                m2_start, m2_end = matches[j].span()

                # Check if ranges overlap
                if (m1_start < m2_start < m1_end) or (m2_start < m1_start < m2_end):
                    return True

        return False

    def _positions_to_indices(self, positions: List[str]) -> List[int]:
        """
        Convert position labels to indices for storage in model.

        Args:
            positions: List of position labels ('beginning', 'middle', 'end')

        Returns:
            List of indices (0 = beginning, 1 = middle, 2 = end)
        """
        position_map = {"beginning": 0, "middle": 1, "end": 2}
        return [position_map.get(p, 1) for p in positions]

    def aggregate_metrics(
        self, metrics_list: List[CardClozeMetrics]
    ) -> Dict:
        """
        Aggregate cloze metrics across multiple cards.

        Args:
            metrics_list: List of CardClozeMetrics to aggregate

        Returns:
            Dictionary with aggregated metrics including averages, distributions, and counts
        """
        if not metrics_list:
            return {}

        import statistics

        cloze_counts = [m.cloze_count for m in metrics_list]
        avg_lengths = [m.avg_cloze_length for m in metrics_list]

        # Aggregate type counts
        all_types = {}
        for m in metrics_list:
            for ctype in m.cloze_types:
                all_types[ctype] = all_types.get(ctype, 0) + 1

        # Calculate position distribution
        position_counts = {"beginning": 0, "middle": 0, "end": 0}
        position_labels = ["beginning", "middle", "end"]
        for m in metrics_list:
            for pos_idx in m.cloze_positions:
                if 0 <= pos_idx < len(position_labels):
                    position_counts[position_labels[pos_idx]] += 1

        return {
            "avg_cloze_count": sum(cloze_counts) / len(cloze_counts),
            "median_cloze_count": statistics.median(cloze_counts),
            "min_cloze_count": min(cloze_counts),
            "max_cloze_count": max(cloze_counts),
            "cards_with_cloze": sum(1 for c in cloze_counts if c > 0),
            "cards_without_cloze": sum(1 for c in cloze_counts if c == 0),
            "avg_cloze_length": sum(avg_lengths) / len(avg_lengths),
            "median_cloze_length": statistics.median(avg_lengths),
            "cloze_type_distribution": all_types,
            "position_distribution": position_counts,
            "cards_with_trivial_clozes": sum(1 for m in metrics_list if m.has_trivial_clozes),
            "cards_with_nested_clozes": sum(1 for m in metrics_list if m.has_nested_clozes),
            "percentage_with_trivial_clozes": (
                sum(1 for m in metrics_list if m.has_trivial_clozes) / len(metrics_list)
            )
            * 100,
            "total_cards": len(metrics_list),
        }
