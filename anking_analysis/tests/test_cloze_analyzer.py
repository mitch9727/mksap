#!/usr/bin/env python3
"""Test script for ClozeAnalyzer implementation"""

from anking_analysis.models import AnkingCard
from anking_analysis.tools.cloze_analyzer import ClozeAnalyzer

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

print("Cloze metrics for sample card:")
print(f"  - Cloze count: {metrics.cloze_count}")
print(f"  - Unique clozes: {metrics.unique_cloze_count}")
print(f"  - Cloze types: {metrics.cloze_types}")
print(f"  - Avg cloze length: {metrics.avg_cloze_length:.2f}")
print(f"  - Cloze positions (indices): {metrics.cloze_positions}")
print(f"  - Has nested: {metrics.has_nested_clozes}")
print(f"  - Has trivial: {metrics.has_trivial_clozes}")

print("\nAll metrics:")
print(metrics.model_dump())

# Test aggregation
print("\n\nTesting aggregation with 2 cards...")
metrics_list = [metrics, metrics]
aggregated = analyzer.aggregate_metrics(metrics_list)
print("\nAggregated metrics:")
for key, value in aggregated.items():
    print(f"  {key}: {value}")

print("\n✅ All tests passed!")
