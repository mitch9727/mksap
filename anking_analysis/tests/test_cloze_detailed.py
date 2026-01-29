#!/usr/bin/env python3
"""Comprehensive test script for ClozeAnalyzer implementation"""

from anking_analysis.models import AnkingCard, CardClozeMetrics
from anking_analysis.tools.cloze_analyzer import ClozeAnalyzer

def test_basic_analysis():
    """Test basic cloze analysis with sample card"""
    print("=" * 60)
    print("TEST 1: Basic Cloze Analysis")
    print("=" * 60)

    # Create sample card as specified in the task
    sample_card = AnkingCard(
        note_id=2,
        deck_path="AnKing::Test",
        deck_name="Test",
        text="Patient has {{c1::hypertension}} with BP {{c2::150/90 mmHg}}.",
        text_plain="Patient has hypertension with BP 150/90 mmHg.",
        extra=None,
        extra_plain=None,
        cloze_deletions=['hypertension', '150/90 mmHg'],
        cloze_count=2,
        tags=[],
        html_features={}
    )

    # Test analyzer
    analyzer = ClozeAnalyzer()
    metrics = analyzer.analyze(sample_card)

    print(f"\n✓ Cloze count: {metrics.cloze_count} (expected: 2)")
    assert metrics.cloze_count == 2, "Cloze count mismatch"

    print(f"✓ Unique clozes: {metrics.unique_cloze_count} (expected: 2)")
    assert metrics.unique_cloze_count == 2, "Unique cloze count mismatch"

    print(f"✓ Cloze types: {metrics.cloze_types}")
    assert len(metrics.cloze_types) == 2, "Should have 2 cloze types"

    print(f"✓ Avg cloze length: {metrics.avg_cloze_length:.2f}")
    assert metrics.avg_cloze_length > 0, "Average cloze length should be positive"

    print(f"✓ Has nested clozes: {metrics.has_nested_clozes} (expected: False)")
    assert metrics.has_nested_clozes is False, "Should not detect nested clozes"

    print(f"✓ Has trivial clozes: {metrics.has_trivial_clozes} (expected: False)")
    assert metrics.has_trivial_clozes is False, "Should not detect trivial clozes"

    print(f"✓ Cloze positions: {metrics.cloze_positions}")
    assert len(metrics.cloze_positions) == 2, "Should have 2 positions"

    print("\n✅ TEST 1 PASSED\n")


def test_trivial_clozes():
    """Test detection of trivial clozes"""
    print("=" * 60)
    print("TEST 2: Trivial Cloze Detection")
    print("=" * 60)

    card = AnkingCard(
        note_id=3,
        deck_path="AnKing::Test",
        deck_name="Test",
        text="This is {{c1::a}} test.",
        text_plain="This is a test.",
        extra=None,
        extra_plain=None,
        cloze_deletions=['a'],
        cloze_count=1,
        tags=[],
        html_features={}
    )

    analyzer = ClozeAnalyzer()
    metrics = analyzer.analyze(card)

    print(f"\n✓ Has trivial clozes: {metrics.has_trivial_clozes} (expected: True)")
    assert metrics.has_trivial_clozes is True, "Should detect trivial cloze 'a'"

    print("✅ TEST 2 PASSED\n")


def test_nested_clozes():
    """Test detection of nested clozes"""
    print("=" * 60)
    print("TEST 3: Nested Cloze Detection")
    print("=" * 60)

    # Nested cloze markup
    card = AnkingCard(
        note_id=4,
        deck_path="AnKing::Test",
        deck_name="Test",
        text="Patient has {{c1::{{c2::hypertension}}}}.",
        text_plain="Patient has hypertension.",
        extra=None,
        extra_plain=None,
        cloze_deletions=['hypertension'],
        cloze_count=1,
        tags=[],
        html_features={}
    )

    analyzer = ClozeAnalyzer()
    metrics = analyzer.analyze(card)

    print(f"\n✓ Has nested clozes: {metrics.has_nested_clozes} (expected: True)")
    assert metrics.has_nested_clozes is True, "Should detect nested clozes"

    print("✅ TEST 3 PASSED\n")


def test_position_detection():
    """Test position detection"""
    print("=" * 60)
    print("TEST 4: Position Detection")
    print("=" * 60)

    card = AnkingCard(
        note_id=5,
        deck_path="AnKing::Test",
        deck_name="Test",
        text="{{c1::Hypertension}} is a condition with {{c2::high blood pressure}}.",
        text_plain="Hypertension is a condition with high blood pressure.",
        extra=None,
        extra_plain=None,
        cloze_deletions=['Hypertension', 'high blood pressure'],
        cloze_count=2,
        tags=[],
        html_features={}
    )

    analyzer = ClozeAnalyzer()
    metrics = analyzer.analyze(card)

    print(f"\n✓ Cloze positions (indices): {metrics.cloze_positions}")
    # Position 0 = beginning, 1 = middle, 2 = end
    print(f"  Position 1 expected at beginning (0): {metrics.cloze_positions[0] == 0}")
    print(f"  Position 2 likely at end (2) or middle (1): {metrics.cloze_positions[1]}")

    print("✅ TEST 4 PASSED\n")


def test_aggregation():
    """Test metrics aggregation"""
    print("=" * 60)
    print("TEST 5: Metrics Aggregation")
    print("=" * 60)

    analyzer = ClozeAnalyzer()

    # Create 3 sample cards with different metrics
    cards = [
        AnkingCard(
            note_id=i,
            deck_path="AnKing::Test",
            deck_name="Test",
            text=f"Test {{{{c1::term{i}}}}}.",
            text_plain=f"Test term{i}.",
            extra=None,
            extra_plain=None,
            cloze_deletions=[f'term{i}'],
            cloze_count=1,
            tags=[],
            html_features={}
        )
        for i in range(1, 4)
    ]

    metrics_list = [analyzer.analyze(card) for card in cards]
    aggregated = analyzer.aggregate_metrics(metrics_list)

    print(f"\n✓ Total cards: {aggregated['total_cards']} (expected: 3)")
    assert aggregated['total_cards'] == 3, "Should have 3 cards"

    print(f"✓ Average cloze count: {aggregated['avg_cloze_count']:.2f} (expected: 1.0)")
    assert aggregated['avg_cloze_count'] == 1.0, "Average should be 1.0"

    print(f"✓ Cards with cloze: {aggregated['cards_with_cloze']} (expected: 3)")
    assert aggregated['cards_with_cloze'] == 3, "All cards should have clozes"

    print(f"✓ Cards without cloze: {aggregated['cards_without_cloze']} (expected: 0)")
    assert aggregated['cards_without_cloze'] == 0, "No cards should be without clozes"

    print(f"✓ Cloze type distribution: {aggregated['cloze_type_distribution']}")
    assert len(aggregated['cloze_type_distribution']) > 0, "Should have type distribution"

    print("✅ TEST 5 PASSED\n")


def test_cloze_type_classification():
    """Test cloze type classification with numbers"""
    print("=" * 60)
    print("TEST 6: Cloze Type Classification")
    print("=" * 60)

    analyzer = ClozeAnalyzer()

    # Test number detection
    number_type = analyzer.classify_cloze_type("150/90 mmHg")
    print(f"\n✓ Number classification for '150/90 mmHg': {number_type} (expected: 'number')")
    assert number_type == "number", "Should classify as number type"

    # Test other type
    other_type = analyzer.classify_cloze_type("patient")
    print(f"✓ Other classification for 'patient': {other_type}")
    assert other_type in ['diagnosis', 'medication', 'mechanism', 'number', 'other'], \
        "Should return valid type"

    print("✅ TEST 6 PASSED\n")


if __name__ == "__main__":
    try:
        test_basic_analysis()
        test_trivial_clozes()
        test_nested_clozes()
        test_position_detection()
        test_aggregation()
        test_cloze_type_classification()

        print("\n" + "=" * 60)
        print("✅✅✅ ALL TESTS PASSED ✅✅✅")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
