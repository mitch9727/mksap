"""
Formatting Analyzer for AnKing Analysis Pipeline - Phase 2 Task 3.4

Analyzes formatting and readability characteristics of flashcards.

Measures use of HTML formatting (bold, italic, lists, tables), markdown compatibility,
and visual hierarchy in card text.
"""

from typing import Dict, List

from anking_analysis.models import AnkingCard, CardFormattingMetrics


class FormattingAnalyzer:
    """
    Analyzes the formatting and readability properties of AnKing flashcard statements.

    Measures:
    - Use of bold, italic, lists, and tables
    - Markdown compatibility (absence of complex HTML)
    - Emphasis count (total bold/italic instances)
    - Presence of clear visual hierarchy
    """

    def analyze(self, card: AnkingCard) -> CardFormattingMetrics:
        """
        Analyze the formatting of a single card.

        Args:
            card: AnkingCard to analyze

        Returns:
            CardFormattingMetrics with formatting analysis results
        """
        # 1. Extract formatting features from html_features dict
        uses_bold = card.html_features.get("uses_bold", False)
        uses_italic = card.html_features.get("uses_italic", False)
        uses_lists = card.html_features.get("uses_lists", False)
        uses_tables = card.html_features.get("uses_tables", False)

        # 2. Count emphasis instances (bold and italic tags)
        emphasis_count = card.text.count("<b>") + card.text.count("<strong>")
        emphasis_count += card.text.count("<i>") + card.text.count("<em>")

        # 3. Check markdown compatibility (no complex HTML)
        complex_html = ["<table>", "<div>", "<span style=", "<style>"]
        markdown_compatible = not any(tag in card.text for tag in complex_html)

        # 4. Assess hierarchy (lists, sections, multiple paragraphs, or separators)
        has_clear_hierarchy = (
            uses_lists or "\n\n" in card.text_plain or "---" in card.text
        )

        return CardFormattingMetrics(
            card_id=card.note_id,
            uses_bold=uses_bold,
            uses_italic=uses_italic,
            uses_lists=uses_lists,
            uses_tables=uses_tables,
            markdown_compatible=markdown_compatible,
            emphasis_count=emphasis_count,
            has_clear_hierarchy=has_clear_hierarchy,
        )

    def aggregate_metrics(
        self, metrics_list: List[CardFormattingMetrics]
    ) -> Dict:
        """
        Aggregate formatting metrics across multiple cards.

        Args:
            metrics_list: List of CardFormattingMetrics to aggregate

        Returns:
            Dictionary with aggregated metrics including counts and percentages
        """
        if not metrics_list:
            return {}

        total = len(metrics_list)

        return {
            "total_cards": total,
            "cards_with_bold": sum(1 for m in metrics_list if m.uses_bold),
            "percentage_with_bold": (
                sum(1 for m in metrics_list if m.uses_bold) / total
            ) * 100,
            "cards_with_italic": sum(1 for m in metrics_list if m.uses_italic),
            "percentage_with_italic": (
                sum(1 for m in metrics_list if m.uses_italic) / total
            ) * 100,
            "cards_with_lists": sum(1 for m in metrics_list if m.uses_lists),
            "percentage_with_lists": (
                sum(1 for m in metrics_list if m.uses_lists) / total
            ) * 100,
            "cards_with_tables": sum(1 for m in metrics_list if m.uses_tables),
            "percentage_with_tables": (
                sum(1 for m in metrics_list if m.uses_tables) / total
            ) * 100,
            "markdown_compatible_cards": sum(
                1 for m in metrics_list if m.markdown_compatible
            ),
            "percentage_markdown_compatible": (
                sum(1 for m in metrics_list if m.markdown_compatible) / total
            ) * 100,
            "cards_with_hierarchy": sum(
                1 for m in metrics_list if m.has_clear_hierarchy
            ),
            "percentage_with_hierarchy": (
                sum(1 for m in metrics_list if m.has_clear_hierarchy) / total
            ) * 100,
            "avg_emphasis_count": sum(m.emphasis_count for m in metrics_list)
            / total,
            "max_emphasis_count": max(m.emphasis_count for m in metrics_list),
            "min_emphasis_count": min(m.emphasis_count for m in metrics_list),
        }
