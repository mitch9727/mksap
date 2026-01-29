"""
Baseline Comparator for AnKing Analysis Pipeline - Phase 3 Task 4

Loads Phase 3 MKSAP test questions and compares them against AnKing metrics.

Implements analysis of MKSAP-generated statements using the full 4-analyzer pipeline
(structure, cloze, context, formatting), enabling direct comparison with AnKing deck metrics.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from anking_analysis.models import (
    AnkingCard,
    CardStructureMetrics,
    CardClozeMetrics,
    CardContextMetrics,
    CardFormattingMetrics,
)
from anking_analysis.tools.structure_analyzer import StructureAnalyzer
from anking_analysis.tools.cloze_analyzer import ClozeAnalyzer
from anking_analysis.tools.context_analyzer import ContextAnalyzer
from anking_analysis.tools.formatting_analyzer import FormattingAnalyzer
from statement_generator.src.infrastructure.models.data_models import Statement

logger = logging.getLogger(__name__)


class BaselineComparator:
    """
    Compares MKSAP statement_generator output against AnKing deck metrics.

    Loads Phase 3 test questions, extracts statements, and runs all 4 analyzers
    to generate MKSAP baseline metrics for comparison with AnKing production decks.

    Attributes:
        mksap_data_dir: Path to MKSAP extracted questions directory
        structure_analyzer: Analyzer for statement structure and complexity
        cloze_analyzer: Analyzer for cloze deletion patterns
        context_analyzer: Analyzer for context preservation
        formatting_analyzer: Analyzer for formatting and readability
    """

    # Phase 3 test question IDs from the evaluation plan
    PHASE3_TEST_QUESTIONS = [
        "cvmcq24001",  # Cardiovascular
        "cvcor25002",
        "encor25001",  # Endocrinology
        "enmcq24050",
        "gimcq24025",  # Gastroenterology & Hepatology
        "gicor25001",
        "dmmcq24032",  # Dermatology
        "dmcor25001",
        "npmcq24050",  # Nephrology
        "npcor25001",
        "cccor25002",  # Critical Care
        "ccmcq24035",
        "hpmcq24032",  # Hematology & Oncology
        "hpcor25001",
    ]

    def __init__(self, mksap_data_dir: Path):
        """
        Initialize comparator with path to MKSAP data directory.

        Args:
            mksap_data_dir: Path to MKSAP extracted questions directory
                (typically /Users/Mitchell/coding/projects/MKSAP/mksap_data)
        """
        self.mksap_data_dir = Path(mksap_data_dir)
        self.structure_analyzer = StructureAnalyzer()
        self.cloze_analyzer = ClozeAnalyzer()
        self.context_analyzer = ContextAnalyzer()
        self.formatting_analyzer = FormattingAnalyzer()

    def load_mksap_statements(self) -> List[Statement]:
        """
        Load Phase 3 test questions and extract statements.

        Reads the 14 Phase 3 test questions from MKSAP data directory,
        extracts Statement objects from both critique and key_points sections,
        and returns them for analysis.

        Returns:
            List of Statement objects extracted from Phase 3 test questions.
            Returns empty list if no statements found or errors occur.

        Raises:
            None - all errors are caught and logged, returns whatever was loaded
        """
        statements = []

        for qid in self.PHASE3_TEST_QUESTIONS:
            # Extract category from question ID (first 2 characters)
            category = qid[:2]
            qfile = self.mksap_data_dir / category / qid / f"{qid}.json"

            if not qfile.exists():
                logger.warning(f"Question file not found: {qfile}")
                continue

            try:
                with open(qfile) as f:
                    qdata = json.load(f)

                # Extract statements from both critique and key_points sections
                if "true_statements" in qdata:
                    # Extract from critique
                    for stmt_dict in qdata["true_statements"].get("from_critique", []):
                        statements.append(Statement(**stmt_dict))

                    # Extract from key_points
                    for stmt_dict in qdata["true_statements"].get("from_key_points", []):
                        statements.append(Statement(**stmt_dict))

            except Exception as e:
                logger.error(f"Failed to load {qfile}: {e}")
                continue

        logger.info(
            f"Loaded {len(statements)} statements from {len(self.PHASE3_TEST_QUESTIONS)} MKSAP questions"
        )
        return statements

    def analyze_mksap_baseline(self) -> Dict[str, Any]:
        """
        Run all 4 analyzers on MKSAP statements and aggregate results.

        Loads all Phase 3 test statements, converts them to pseudo-AnkingCard objects,
        runs the structure, cloze, context, and formatting analyzers on each,
        and aggregates the results.

        Returns:
            Dictionary with keys: 'structure', 'cloze', 'context', 'formatting'
            Each containing aggregated metrics from all analyzed cards.

            Example:
                {
                    'structure': {
                        'avg_word_count': 18.5,
                        'avg_atomicity_score': 0.85,
                        ...
                    },
                    'cloze': {
                        'avg_cloze_count': 2.3,
                        'cards_with_cloze': 92,
                        ...
                    },
                    ...
                }
        """
        statements = self.load_mksap_statements()

        if not statements:
            logger.warning("No statements loaded for baseline analysis")
            return {
                "structure": {},
                "cloze": {},
                "context": {},
                "formatting": {},
            }

        structure_metrics = []
        cloze_metrics = []
        context_metrics = []
        formatting_metrics = []

        for i, stmt in enumerate(statements):
            try:
                # Convert Statement to pseudo-AnkingCard for analysis
                # Note: Using index as note_id since MKSAP statements don't have unique IDs
                pseudo_card = AnkingCard(
                    note_id=i,
                    deck_path="MKSAP",
                    deck_name="MKSAP",
                    text=stmt.statement,
                    text_plain=stmt.statement,
                    extra=stmt.extra_field or "",
                    extra_plain=stmt.extra_field or "",
                    cloze_deletions=stmt.cloze_candidates,
                    cloze_count=len(stmt.cloze_candidates),
                    tags=[],
                    html_features={},
                )

                # Run all 4 analyzers
                structure_metrics.append(self.structure_analyzer.analyze(pseudo_card))
                cloze_metrics.append(self.cloze_analyzer.analyze(pseudo_card))
                context_metrics.append(self.context_analyzer.analyze(pseudo_card))
                formatting_metrics.append(self.formatting_analyzer.analyze(pseudo_card))

            except Exception as e:
                logger.error(f"Failed to analyze statement {i}: {e}")
                continue

        logger.info(f"Analyzed {len(structure_metrics)} statements successfully")

        return {
            "structure": self.structure_analyzer.aggregate_metrics(structure_metrics),
            "cloze": self.cloze_analyzer.aggregate_metrics(cloze_metrics),
            "context": self.context_analyzer.aggregate_metrics(context_metrics),
            "formatting": self.formatting_analyzer.aggregate_metrics(formatting_metrics),
        }

    def compare(
        self, anking_metrics: Dict[str, Any], mksap_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare AnKing metrics against MKSAP baseline metrics.

        Performs metric-by-metric comparison across all 4 categories (structure,
        cloze, context, formatting), calculating deltas and flagging significant
        differences (>20%).

        Args:
            anking_metrics: Dictionary with keys 'structure', 'cloze', 'context', 'formatting'
                containing AnKing aggregated metrics
            mksap_metrics: Dictionary with same structure containing MKSAP baseline metrics

        Returns:
            Dictionary with comparison results for each category. Structure:
                {
                    'structure': {
                        'avg_word_count': {
                            'anking': 22.5,
                            'mksap': 18.5,
                            'delta_pct': 21.6,
                            'significant': True
                        },
                        ...
                    },
                    ...
                }
        """
        comparison = {}

        # Structure comparison
        if "structure" in anking_metrics and "structure" in mksap_metrics:
            comparison["structure"] = self._compare_dicts(
                anking_metrics["structure"], mksap_metrics["structure"], "structure"
            )

        # Cloze comparison
        if "cloze" in anking_metrics and "cloze" in mksap_metrics:
            comparison["cloze"] = self._compare_dicts(
                anking_metrics["cloze"], mksap_metrics["cloze"], "cloze"
            )

        # Context comparison
        if "context" in anking_metrics and "context" in mksap_metrics:
            comparison["context"] = self._compare_dicts(
                anking_metrics["context"], mksap_metrics["context"], "context"
            )

        # Formatting comparison
        if "formatting" in anking_metrics and "formatting" in mksap_metrics:
            comparison["formatting"] = self._compare_dicts(
                anking_metrics["formatting"], mksap_metrics["formatting"], "formatting"
            )

        return comparison

    def _compare_dicts(
        self, anking: Dict[str, Any], mksap: Dict[str, Any], category: str
    ) -> Dict[str, Any]:
        """
        Compare two metric dictionaries and calculate deltas.

        For each numeric metric present in both dictionaries, calculates the
        percentage delta and flags significant differences (>20%).

        Args:
            anking: AnKing metrics dictionary for one category
            mksap: MKSAP metrics dictionary for same category
            category: Category name for logging purposes

        Returns:
            Dictionary with comparison results for each metric:
                {
                    'metric_name': {
                        'anking': <value>,
                        'mksap': <value>,
                        'delta_pct': <percentage change>,
                        'significant': <bool>
                    }
                }

        Note:
            - Dict and non-numeric values are included as-is without delta calculation
            - Zero MKSAP values result in 0% delta (avoids division by zero)
            - Significant difference threshold is 20%
        """
        result = {}

        for key in anking.keys():
            if key not in mksap:
                continue

            anking_val = anking[key]
            mksap_val = mksap[key]

            # Skip dict values - include as-is
            if isinstance(anking_val, dict) or isinstance(mksap_val, dict):
                result[key] = {"anking": anking_val, "mksap": mksap_val}
                continue

            # Calculate delta for numeric values
            delta_pct = 0
            if isinstance(mksap_val, (int, float)) and mksap_val != 0:
                delta_pct = ((anking_val - mksap_val) / mksap_val) * 100

            # Flag significant differences (>20%)
            significant = abs(delta_pct) > 20

            result[key] = {
                "anking": (
                    round(anking_val, 2) if isinstance(anking_val, float) else anking_val
                ),
                "mksap": (
                    round(mksap_val, 2) if isinstance(mksap_val, float) else mksap_val
                ),
                "delta_pct": round(delta_pct, 1),
                "significant": significant,
            }

        return result
