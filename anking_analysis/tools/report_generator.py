"""
Report Generator for AnKing Analysis Pipeline

Generates three markdown reports with findings and recommendations:
1. ANKING_ANALYSIS.md - Analysis of AnKing flashcard structure, cloze patterns, context, formatting
2. MKSAP_VS_ANKING.md - Comparison between AnKing and MKSAP statement_generator output
3. IMPROVEMENTS.md - Prioritized recommendations for statement_generator improvement
"""

from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from anking_analysis.models import AnkingCard, Recommendation


class ReportGenerator:
    """
    Generates comprehensive markdown reports from AnKing analysis results.

    Creates three reports:
    - Analysis report: Summary of AnKing card characteristics
    - Comparison report: AnKing vs MKSAP metrics comparison
    - Recommendations report: Prioritized improvements for statement_generator
    """

    def __init__(self, output_dir: Path):
        """
        Initialize report generator with output directory.

        Args:
            output_dir: Path where reports will be written
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_reports(
        self,
        anking_cards: List[AnkingCard],
        anking_metrics: Dict,
        mksap_metrics: Dict,
        comparison: Dict,
    ):
        """
        Generate all three reports.

        Args:
            anking_cards: List of extracted AnKing cards
            anking_metrics: Aggregated metrics from AnKing analysis
            mksap_metrics: Aggregated metrics from MKSAP analysis
            comparison: Comparison results between AnKing and MKSAP
        """
        self.generate_analysis_report(anking_cards, anking_metrics)
        self.generate_comparison_report(comparison)
        self.generate_recommendations_report(comparison)

    def generate_analysis_report(
        self, anking_cards: List[AnkingCard], anking_metrics: Dict
    ):
        """
        Generate AnKing analysis report.

        Creates detailed report on AnKing flashcard structure, cloze patterns,
        context preservation, and formatting characteristics.

        Args:
            anking_cards: List of extracted AnKing cards
            anking_metrics: Aggregated metrics from analysis
        """
        timestamp = datetime.now().isoformat()
        decks = set(c.deck_name for c in anking_cards)

        structure = anking_metrics.get("structure", {})
        cloze = anking_metrics.get("cloze", {})
        context = anking_metrics.get("context", {})
        formatting = anking_metrics.get("formatting", {})

        report = f"""# AnKing Flashcard Analysis Report

**Generated:** {timestamp}

## Executive Summary

- **Total Cards Analyzed:** {len(anking_cards)}
- **Unique Decks:** {len(decks)}
- **Date:** {timestamp}

## Statement Structure

### Key Metrics

- **Average Text Length:** {structure.get('avg_text_length', 'N/A'):.1f} characters
- **Average Word Count:** {structure.get('avg_word_count', 'N/A'):.1f} words
- **Average Atomicity Score:** {structure.get('avg_atomicity_score', 'N/A'):.2f} (0-1 scale)
- **Cards with Formatting:** {structure.get('cards_with_formatting', 0)} ({structure.get('percentage_with_formatting', 0):.1f}%)
- **Cards with Lists:** {structure.get('cards_with_lists', 0)}

## Cloze Deletion Patterns

### Key Metrics

- **Average Cloze Count:** {cloze.get('avg_cloze_count', 'N/A'):.2f} per card
- **Median Cloze Count:** {cloze.get('median_cloze_count', 'N/A')}
- **Cards with Cloze Deletions:** {cloze.get('cards_with_cloze', 0)}/{len(anking_cards)}
- **Cards without Cloze:** {cloze.get('cards_without_cloze', 0)}

### Cloze Type Distribution

{self._format_dict_as_list(cloze.get('cloze_type_distribution', {}))}

## Clinical Context Preservation

### Key Metrics

- **Cards with Extra Field:** {context.get('cards_with_extra', 0)} ({context.get('percentage_with_extra', 0):.1f}%)
- **Average Extra Field Length:** {context.get('avg_extra_length', 0):.0f} characters

### Context Types

{self._format_dict_as_list(context.get('context_type_distribution', {}))}

## Formatting and Readability

### Key Metrics

- **Bold Usage:** {formatting.get('cards_with_bold', 0)} cards ({formatting.get('percentage_with_bold', 0):.1f}%)
- **Italic Usage:** {formatting.get('cards_with_italic', 0)} cards ({formatting.get('percentage_with_italic', 0):.1f}%)
- **Lists Usage:** {formatting.get('cards_with_lists', 0)} cards ({formatting.get('percentage_with_lists', 0):.1f}%)
- **Markdown Compatible:** {formatting.get('markdown_compatible_cards', 0)} cards ({formatting.get('percentage_markdown_compatible', 0):.1f}%)

## Decks Sampled

{self._format_deck_list([c.deck_name for c in anking_cards])}
"""

        output_file = self.output_dir / "ANKING_ANALYSIS.md"
        with open(output_file, "w") as f:
            f.write(report)

        print(f"Generated: {output_file}")

    def generate_comparison_report(self, comparison: Dict):
        """
        Generate AnKing vs MKSAP comparison report.

        Creates comparison report with side-by-side metrics and significance testing.

        Args:
            comparison: Comparison results dictionary with structure, cloze, and context diffs
        """
        timestamp = datetime.now().isoformat()

        report = f"""# AnKing vs MKSAP Comparison Report

**Generated:** {timestamp}

## Statement Structure Comparison

| Metric | AnKing | MKSAP | Delta | Significant |
|--------|--------|-------|-------|-------------|
"""

        if "structure" in comparison:
            for key, values in comparison["structure"].items():
                if isinstance(values, dict) and "delta_pct" in values:
                    anking = values.get("anking", "N/A")
                    mksap = values.get("mksap", "N/A")
                    delta = values.get("delta_pct", "N/A")
                    sig = "✓" if values.get("significant", False) else ""
                    report += f"| {key} | {anking} | {mksap} | {delta}% | {sig} |\n"

        report += """
## Cloze Pattern Comparison

| Metric | AnKing | MKSAP | Delta | Significant |
|--------|--------|-------|-------|-------------|
"""

        if "cloze" in comparison:
            for key, values in comparison["cloze"].items():
                if isinstance(values, dict) and "delta_pct" in values:
                    anking = values.get("anking", "N/A")
                    mksap = values.get("mksap", "N/A")
                    delta = values.get("delta_pct", "N/A")
                    sig = "✓" if values.get("significant", False) else ""
                    report += f"| {key} | {anking} | {mksap} | {delta}% | {sig} |\n"

        report += """
## Context Comparison

| Metric | AnKing | MKSAP | Delta | Significant |
|--------|--------|-------|-------|-------------|
"""

        if "context" in comparison:
            for key, values in comparison["context"].items():
                if isinstance(values, dict) and "delta_pct" in values:
                    anking = values.get("anking", "N/A")
                    mksap = values.get("mksap", "N/A")
                    delta = values.get("delta_pct", "N/A")
                    sig = "✓" if values.get("significant", False) else ""
                    report += f"| {key} | {anking} | {mksap} | {delta}% | {sig} |\n"

        output_file = self.output_dir / "MKSAP_VS_ANKING.md"
        with open(output_file, "w") as f:
            f.write(report)

        print(f"Generated: {output_file}")

    def generate_recommendations_report(self, comparison: Dict):
        """
        Generate recommendations report with prioritized improvements.

        Creates actionable recommendations based on comparison analysis,
        sorted by priority level with code examples and effort estimates.

        Args:
            comparison: Comparison results dictionary
        """
        recommendations = self._generate_recommendations(comparison)

        # Sort by priority
        high = [r for r in recommendations if r.priority == "high"]
        medium = [r for r in recommendations if r.priority == "medium"]
        low = [r for r in recommendations if r.priority == "low"]

        report = """# Statement Generator Improvement Recommendations

## High Priority Recommendations

"""

        for i, rec in enumerate(high, 1):
            rec_preview = rec.recommendation[:60] + "..." if len(rec.recommendation) > 60 else rec.recommendation
            report += f"""### {i}. {rec.category.title()}: {rec_preview}

**Finding:** {rec.finding}

**Current MKSAP Behavior:** {rec.mksap_current}

**Recommendation:** {rec.recommendation}

**Files to Modify:**
"""
            for f in rec.target_files:
                report += f"- `{f}`\n"

            report += f"""
**Expected Impact:** {rec.expected_impact}

**Effort:** {rec.effort_estimate}

"""

            if rec.code_snippet:
                report += f"""**Code Example:**
```python
{rec.code_snippet}
```

"""

        report += "\n## Medium Priority Recommendations\n\n"
        for i, rec in enumerate(medium, 1):
            report += f"- {rec.recommendation}\n"

        report += "\n## Low Priority Recommendations\n\n"
        for i, rec in enumerate(low, 1):
            report += f"- {rec.recommendation}\n"

        output_file = self.output_dir / "IMPROVEMENTS.md"
        with open(output_file, "w") as f:
            f.write(report)

        print(f"Generated: {output_file}")

    def _generate_recommendations(self, comparison: Dict) -> List[Recommendation]:
        """
        Generate prioritized recommendations based on comparison analysis.

        Args:
            comparison: Comparison results dictionary

        Returns:
            List of Recommendation objects sorted by priority
        """
        recommendations = []

        # High priority: significant differences detected
        if "structure" in comparison:
            struct = comparison["structure"]
            if struct.get("avg_word_count", {}).get("significant", False):
                mksap_avg = struct.get("avg_word_count", {}).get("mksap", 0)
                anking_avg = struct.get("avg_word_count", {}).get("anking", 0)

                if mksap_avg > anking_avg * 1.2:
                    recommendations.append(
                        Recommendation(
                            priority="high",
                            category="structure",
                            finding=f"AnKing statements are more concise ({anking_avg:.1f} words vs {mksap_avg:.1f})",
                            mksap_current="MKSAP statements are verbose",
                            recommendation="Add brevity guidelines to LLM prompts and validation",
                            target_files=[
                                "statement_generator/prompts/critique.txt",
                                "statement_generator/src/processing/statements/extractors/critique.py",
                            ],
                            code_snippet='# Add to prompt: "Keep statements under 20 words when possible"',
                            expected_impact="More readable statements, easier to study",
                            effort_estimate="small",
                        )
                    )

        if "cloze" in comparison:
            cloze = comparison["cloze"]
            if cloze.get("avg_cloze_count", {}).get("significant", False):
                recommendations.append(
                    Recommendation(
                        priority="high",
                        category="cloze",
                        finding="AnKing uses optimal 2-5 cloze deletions per card",
                        mksap_current="MKSAP has suboptimal cloze distribution",
                        recommendation="Improve cloze candidate selection algorithm to prioritize key learning points",
                        target_files=[
                            "statement_generator/src/processing/cloze/validators/cloze_checks.py",
                            "statement_generator/src/processing/cloze/extractors/cloze_extractor.py",
                        ],
                        code_snippet="# Prioritize cloze selection: diagnosis > mechanism > medication > number",
                        expected_impact="Better flashcard quality and higher retention",
                        effort_estimate="medium",
                    )
                )

        if "context" in comparison:
            ctx = comparison["context"]
            if ctx.get("percentage_with_extra", {}).get("significant", False):
                recommendations.append(
                    Recommendation(
                        priority="high",
                        category="context",
                        finding="AnKing preserves more clinical context in extra field",
                        mksap_current="MKSAP may omit important clinical context",
                        recommendation="Enhance context extraction to capture diagnostic criteria and clinical pearls",
                        target_files=[
                            "statement_generator/src/processing/statements/extractors/critique.py",
                        ],
                        code_snippet="# Add: Extract and preserve diagnostic criteria and clinical pearls",
                        expected_impact="Better understanding and retention of clinical concepts",
                        effort_estimate="medium",
                    )
                )

        if not recommendations:
            # Default recommendations if no significant differences
            recommendations.append(
                Recommendation(
                    priority="medium",
                    category="general",
                    finding="AnKing represents best practices in flashcard design",
                    mksap_current="MKSAP follows good patterns but has room for improvement",
                    recommendation="Use AnKing patterns as reference for validation rules and quality standards",
                    target_files=["statement_generator/src/validation/validator.py"],
                    code_snippet="# Enhance validation checks based on AnKing patterns",
                    expected_impact="Improved overall quality and consistency",
                    effort_estimate="medium",
                )
            )

        return recommendations

    def _format_dict_as_list(self, d: Dict) -> str:
        """
        Format dictionary as markdown bullet list.

        Args:
            d: Dictionary to format

        Returns:
            Formatted markdown list string
        """
        if not d:
            return "- No data available"

        lines = []
        for key, value in sorted(d.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _format_deck_list(self, deck_names: List[str]) -> str:
        """
        Format deck list as markdown bullet list.

        Args:
            deck_names: List of deck names

        Returns:
            Formatted markdown list string
        """
        unique_decks = sorted(set(deck_names))
        lines = [f"- {d}" for d in unique_decks]
        return "\n".join(lines)
