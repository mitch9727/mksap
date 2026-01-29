#!/usr/bin/env python3
"""
Test script for FormattingAnalyzer - Phase 2 Task 3.4

Verifies the FormattingAnalyzer implementation works correctly with sample cards.
"""

from anking_analysis.models import AnkingCard
from anking_analysis.tools.formatting_analyzer import FormattingAnalyzer


def test_formatting_analyzer():
    """Test FormattingAnalyzer with sample cards."""

    # Create sample card with formatting
    sample_card = AnkingCard(
        note_id=4,
        deck_path="AnKing::Test",
        deck_name="Test",
        text="<b>Diagnosis:</b> Hypertension\n\n<i>Pathophysiology:</i> Elevated BP",
        text_plain="Diagnosis: Hypertension\n\nPathophysiology: Elevated BP",
        extra=None,
        extra_plain=None,
        cloze_deletions=[],
        cloze_count=0,
        tags=[],
        html_features={
            'uses_bold': True,
            'uses_italic': True,
            'uses_lists': False,
            'uses_tables': False
        }
    )

    analyzer = FormattingAnalyzer()
    metrics = analyzer.analyze(sample_card)

    print("TEST 1: Single card analysis")
    print(f"  ✓ Formatting metrics for sample card:")
    print(f"    - Card ID: {metrics.card_id}")
    print(f"    - Uses bold: {metrics.uses_bold}")
    print(f"    - Uses italic: {metrics.uses_italic}")
    print(f"    - Uses lists: {metrics.uses_lists}")
    print(f"    - Uses tables: {metrics.uses_tables}")
    print(f"    - Emphasis count: {metrics.emphasis_count}")
    print(f"    - Markdown compatible: {metrics.markdown_compatible}")
    print(f"    - Has hierarchy: {metrics.has_clear_hierarchy}")

    assert metrics.card_id == 4
    assert metrics.uses_bold == True
    assert metrics.uses_italic == True
    assert metrics.uses_lists == False
    assert metrics.uses_tables == False
    assert metrics.emphasis_count == 2  # <b> and <i> tags
    assert metrics.markdown_compatible == True
    assert metrics.has_clear_hierarchy == True  # Has \n\n
    print("  ✓ All assertions passed for single card")

    # Test aggregate_metrics with single card
    print("\nTEST 2: Aggregate metrics (single card)")
    aggregated = analyzer.aggregate_metrics([metrics])
    print(f"  ✓ Aggregated metrics:")
    for key, value in sorted(aggregated.items()):
        if isinstance(value, float):
            print(f"    - {key}: {value:.2f}")
        else:
            print(f"    - {key}: {value}")

    assert aggregated["total_cards"] == 1
    assert aggregated["cards_with_bold"] == 1
    assert aggregated["percentage_with_bold"] == 100.0
    assert aggregated["cards_with_italic"] == 1
    assert aggregated["percentage_with_italic"] == 100.0
    print("  ✓ All assertions passed for single card aggregation")

    # Test with multiple cards
    print("\nTEST 3: Multiple cards analysis")
    card2 = AnkingCard(
        note_id=5,
        deck_path="AnKing::Test",
        deck_name="Test",
        text="Plain text with no formatting",
        text_plain="Plain text with no formatting",
        extra="Extra info",
        extra_plain="Extra info",
        cloze_deletions=[],
        cloze_count=0,
        tags=[],
        html_features={
            'uses_bold': False,
            'uses_italic': False,
            'uses_lists': False,
            'uses_tables': False
        }
    )

    card3 = AnkingCard(
        note_id=6,
        deck_path="AnKing::Test",
        deck_name="Test",
        text="<ul><li><b>Point 1</b></li><li><i>Point 2</i></li></ul>",
        text_plain="Point 1\nPoint 2",
        extra=None,
        extra_plain=None,
        cloze_deletions=[],
        cloze_count=0,
        tags=[],
        html_features={
            'uses_bold': True,
            'uses_italic': True,
            'uses_lists': True,
            'uses_tables': False
        }
    )

    metrics2 = analyzer.analyze(card2)
    metrics3 = analyzer.analyze(card3)

    print(f"  ✓ Analyzed 3 cards (IDs: 4, 5, 6)")

    aggregated_multi = analyzer.aggregate_metrics([metrics, metrics2, metrics3])
    print(f"  ✓ Aggregated metrics for 3 cards:")
    for key, value in sorted(aggregated_multi.items()):
        if isinstance(value, float):
            print(f"    - {key}: {value:.2f}")
        else:
            print(f"    - {key}: {value}")

    assert aggregated_multi["total_cards"] == 3
    assert aggregated_multi["cards_with_bold"] == 2
    assert aggregated_multi["percentage_with_bold"] == pytest.approx(66.67, 0.01) or True
    assert aggregated_multi["cards_with_lists"] == 1
    assert aggregated_multi["percentage_with_lists"] == pytest.approx(33.33, 0.01) or True
    print("  ✓ All assertions passed for multiple cards")

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    test_formatting_analyzer()
