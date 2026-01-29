#!/usr/bin/env python3
"""Quick verification that ClozeAnalyzer is properly implemented and importable"""

import sys

def verify_imports():
    """Verify all imports work correctly"""
    print("Verifying imports...")
    try:
        from anking_analysis.models import AnkingCard, CardClozeMetrics
        print("  ✓ Models imported successfully")

        from anking_analysis.tools.cloze_analyzer import ClozeAnalyzer
        print("  ✓ ClozeAnalyzer imported successfully")

        from anking_analysis.tools import ClozeAnalyzer as ClozeAnalyzer2
        print("  ✓ ClozeAnalyzer available from tools package")

        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def verify_class_methods():
    """Verify ClozeAnalyzer has all required methods"""
    print("\nVerifying class methods...")
    from anking_analysis.tools.cloze_analyzer import ClozeAnalyzer

    required_methods = [
        '__init__',
        'analyze',
        'classify_cloze_type',
        'detect_positions',
        'detect_nested_clozes',
        'aggregate_metrics'
    ]

    for method_name in required_methods:
        if hasattr(ClozeAnalyzer, method_name):
            print(f"  ✓ Method '{method_name}' exists")
        else:
            print(f"  ✗ Method '{method_name}' missing")
            return False

    return True


def verify_basic_functionality():
    """Verify basic functionality with sample card"""
    print("\nVerifying basic functionality...")
    try:
        from anking_analysis.models import AnkingCard
        from anking_analysis.tools.cloze_analyzer import ClozeAnalyzer

        # Create sample card
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
        print("  ✓ Sample card created")

        # Create analyzer
        analyzer = ClozeAnalyzer()
        print("  ✓ ClozeAnalyzer instantiated")

        # Analyze card
        metrics = analyzer.analyze(sample_card)
        print("  ✓ Card analyzed successfully")

        # Verify metrics
        assert metrics.cloze_count == 2, "Cloze count should be 2"
        print("  ✓ Cloze count correct: 2")

        assert metrics.unique_cloze_count == 2, "Unique cloze count should be 2"
        print("  ✓ Unique cloze count correct: 2")

        assert len(metrics.cloze_types) == 2, "Should have 2 cloze types"
        print(f"  ✓ Cloze types detected: {metrics.cloze_types}")

        assert metrics.avg_cloze_length > 0, "Average cloze length should be positive"
        print(f"  ✓ Average cloze length: {metrics.avg_cloze_length:.2f}")

        assert metrics.has_nested_clozes is False, "Should not detect nested clozes"
        print("  ✓ Nested cloze detection working")

        assert metrics.has_trivial_clozes is False, "Should not detect trivial clozes"
        print("  ✓ Trivial cloze detection working")

        # Test aggregation
        metrics_list = [metrics]
        aggregated = analyzer.aggregate_metrics(metrics_list)
        assert 'avg_cloze_count' in aggregated, "Aggregated metrics should have avg_cloze_count"
        print(f"  ✓ Metrics aggregation working ({len(aggregated)} fields)")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("ClozeAnalyzer Implementation Verification")
    print("=" * 60)

    results = []

    results.append(("Imports", verify_imports()))
    results.append(("Methods", verify_class_methods()))
    results.append(("Functionality", verify_basic_functionality()))

    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:9} {test_name}")
        all_passed = all_passed and passed

    print("=" * 60)

    if all_passed:
        print("✅✅✅ ALL VERIFICATIONS PASSED ✅✅✅")
        return 0
    else:
        print("❌❌❌ SOME VERIFICATIONS FAILED ❌❌❌")
        return 1


if __name__ == "__main__":
    sys.exit(main())
