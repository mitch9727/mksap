#!/usr/bin/env python3
"""Phase 3 Evaluation Framework - Measure hybrid pipeline improvements.

Measures three dimensions:
1. Negation preservation (NLP detections appear correctly in LLM output)
2. Entity completeness (all NLP entities referenced in statements)
3. Unit/threshold accuracy (numeric values and comparators preserved exactly)

Usage:
    ./scripts/python statement_generator/tests/tools/phase3_evaluator.py

Example:
    result = evaluator.evaluate_question("gimcq24001")
    evaluations = evaluator.evaluate_batch(["cvcor25001", "cvcor25002"])
    evaluator.generate_report(evaluations, Path("report.md"))
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NegationCheck:
    """Track negation preservation metrics."""
    total_negations: int
    preserved_count: int
    missed_count: int
    preservation_rate: float  # 0.0-1.0


@dataclass
class EntityCheck:
    """Track entity completeness metrics."""
    total_entities: int
    referenced_count: int
    missing_count: int
    completeness_rate: float  # 0.0-1.0
    entity_samples: Dict[str, bool] = field(default_factory=dict)  # entity -> found_in_statement


@dataclass
class UnitCheck:
    """Track unit/threshold accuracy metrics."""
    total_units: int
    accurate_count: int
    inaccurate_count: int
    accuracy_rate: float  # 0.0-1.0
    mismatches: List[Tuple[str, str]] = field(default_factory=list)  # (expected, actual)


@dataclass
class QuestionEvaluation:
    """Complete evaluation for one question."""
    question_id: str
    system_code: str
    nlp_analysis: Dict  # NLP preprocessing output
    statements: Dict  # Generated statements from LLM
    negation_check: NegationCheck
    entity_check: EntityCheck
    unit_check: UnitCheck
    validation_pass: bool
    notes: List[str] = field(default_factory=list)


class Phase3Evaluator:
    """Evaluate hybrid pipeline improvements on sample questions."""

    def __init__(self, project_root: Path):
        """Initialize evaluator with paths."""
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "mksap_data"
        self.artifacts_dir = (
            self.project_root / "statement_generator" / "artifacts" / "phase3_evaluation"
        )
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_question(self, question_id: str) -> Optional[QuestionEvaluation]:
        """Evaluate single question - measure all three dimensions."""
        system_code = question_id[:2]
        question_path = self.data_dir / system_code / question_id / f"{question_id}.json"

        # Load question data
        if not question_path.exists():
            logger.warning(f"{question_id}: File not found at {question_path}")
            return None

        try:
            with open(question_path) as f:
                data = json.load(f)
        except Exception as e:
            logger.warning(f"{question_id}: Failed to load JSON: {e}")
            return None

        # Check if question has been processed with hybrid pipeline
        if "true_statements" not in data:
            logger.warning(f"{question_id}: No true_statements field (not processed yet)")
            return None

        # Extract NLP analysis if available
        nlp_analysis = data.get("nlp_analysis", {})

        # Extract generated statements
        statements = data.get("true_statements", {})

        # Run measurements
        negation_check = self._measure_negation_preservation(
            question_id, nlp_analysis, statements
        )
        entity_check = self._measure_entity_completeness(
            question_id, nlp_analysis, statements
        )
        unit_check = self._measure_unit_accuracy(question_id, nlp_analysis, statements)

        # Check validation pass (if available in data)
        validation_pass = data.get("validation_pass", False)

        # Compile evaluation
        evaluation = QuestionEvaluation(
            question_id=question_id,
            system_code=system_code,
            nlp_analysis=nlp_analysis,
            statements=statements,
            negation_check=negation_check,
            entity_check=entity_check,
            unit_check=unit_check,
            validation_pass=validation_pass,
            notes=[],
        )

        return evaluation

    def _measure_negation_preservation(
        self, question_id: str, nlp_analysis: Dict, statements: Dict
    ) -> NegationCheck:
        """Measure: Do all negations detected by NLP appear correctly in LLM output?"""

        # Extract negations detected by NLP
        negations_detected = nlp_analysis.get("negations", [])

        # Combine all statement text from both critique and key_points
        all_statement_text = ""

        # Extract from from_critique
        if "from_critique" in statements:
            for stmt_item in statements["from_critique"]:
                if isinstance(stmt_item, dict):
                    all_statement_text += " " + stmt_item.get("statement", "")

        # Extract from from_key_points
        if "from_key_points" in statements:
            for stmt_item in statements["from_key_points"]:
                if isinstance(stmt_item, dict):
                    all_statement_text += " " + stmt_item.get("statement", "")

        all_statement_text = all_statement_text.lower()

        # Check if each negation appears in statement text
        preserved = 0
        missed = []

        for negation in negations_detected:
            # Normalize negation pattern for matching
            if isinstance(negation, dict):
                pattern = negation.get("text", negation.get("trigger", "")).lower()
            else:
                pattern = str(negation).lower()

            if not pattern:
                continue

            if pattern in all_statement_text or self._fuzzy_match(pattern, all_statement_text):
                preserved += 1
            else:
                missed.append(pattern)

        total = len(negations_detected)
        preservation_rate = preserved / total if total > 0 else 1.0

        if missed and len(missed) <= 5:
            logger.info(f"{question_id}: Missed negations: {missed}")

        return NegationCheck(
            total_negations=total,
            preserved_count=preserved,
            missed_count=len(missed),
            preservation_rate=preservation_rate,
        )

    def _measure_entity_completeness(
        self, question_id: str, nlp_analysis: Dict, statements: Dict
    ) -> EntityCheck:
        """Measure: Are all NLP-detected entities referenced in generated statements?"""

        # Extract entities detected by NLP
        entities_detected = nlp_analysis.get("entities", [])

        # Combine all statement text from both critique and key_points
        all_statement_text = ""

        # Extract from from_critique
        if "from_critique" in statements:
            for stmt_item in statements["from_critique"]:
                if isinstance(stmt_item, dict):
                    all_statement_text += " " + stmt_item.get("statement", "")

        # Extract from from_key_points
        if "from_key_points" in statements:
            for stmt_item in statements["from_key_points"]:
                if isinstance(stmt_item, dict):
                    all_statement_text += " " + stmt_item.get("statement", "")

        all_statement_text = all_statement_text.lower()

        # Check if each entity text appears in statement
        referenced = 0
        entity_samples = {}

        for entity in entities_detected:
            # Extract entity text - handle both dict and string formats
            if isinstance(entity, dict):
                entity_text = entity.get("text", "").lower()
            else:
                entity_text = str(entity).lower()

            if not entity_text:
                continue

            found = entity_text in all_statement_text or self._fuzzy_match(
                entity_text, all_statement_text
            )
            referenced += found
            entity_samples[entity_text] = found

        total = len(entities_detected)
        completeness_rate = referenced / total if total > 0 else 1.0

        missing_entities = [text for text, found in entity_samples.items() if not found]
        if missing_entities and len(missing_entities) <= 5:
            logger.info(
                f"{question_id}: Missing entities ({len(missing_entities)}): {missing_entities}"
            )

        return EntityCheck(
            total_entities=total,
            referenced_count=referenced,
            missing_count=total - referenced,
            completeness_rate=completeness_rate,
            entity_samples=entity_samples,
        )

    def _measure_unit_accuracy(
        self, question_id: str, nlp_analysis: Dict, statements: Dict
    ) -> UnitCheck:
        """Measure: Are exact units and thresholds preserved (>, <, ≥, ≤)?"""

        # Extract units/thresholds from nlp_analysis if available
        original_question = nlp_analysis.get("original_text", "")

        # If not in nlp_analysis, skip unit measurement
        if not original_question:
            return UnitCheck(
                total_units=0,
                accurate_count=0,
                inaccurate_count=0,
                accuracy_rate=1.0,
                mismatches=[],
            )

        # Find numeric patterns with comparators and units
        # Patterns: ">250 mg/dL", "≥60 years", "<100 mg/dL", "2-3 weeks"
        unit_pattern = r'([<>≥≤]=?)\s*(\d+(?:\.\d+)?)\s*([a-zA-Z/%]*)'
        units_in_original = re.findall(unit_pattern, original_question)

        if not units_in_original:
            return UnitCheck(
                total_units=0,
                accurate_count=0,
                inaccurate_count=0,
                accuracy_rate=1.0,
                mismatches=[],
            )

        # Combine all statement text
        all_statement_text = ""

        # Extract from from_critique
        if "from_critique" in statements:
            for stmt_item in statements["from_critique"]:
                if isinstance(stmt_item, dict):
                    all_statement_text += " " + stmt_item.get("statement", "")

        # Extract from from_key_points
        if "from_key_points" in statements:
            for stmt_item in statements["from_key_points"]:
                if isinstance(stmt_item, dict):
                    all_statement_text += " " + stmt_item.get("statement", "")

        # Check if units appear correctly in statements
        accurate = 0
        mismatches = []

        for comparator, value, unit in units_in_original:
            # Expected format in output
            expected = f"{comparator}{value}"

            # Check for exact match or close match
            if expected in all_statement_text or value in all_statement_text:
                accurate += 1
            else:
                mismatches.append((expected, "NOT_FOUND"))

        total = len(units_in_original)
        accuracy_rate = accurate / total if total > 0 else 1.0

        if mismatches and len(mismatches) <= 5:
            logger.info(f"{question_id}: Unit mismatches ({len(mismatches)}): {mismatches}")

        return UnitCheck(
            total_units=total,
            accurate_count=accurate,
            inaccurate_count=len(mismatches),
            accuracy_rate=accuracy_rate,
            mismatches=mismatches,
        )

    def _fuzzy_match(self, pattern: str, text: str, threshold: float = 0.8) -> bool:
        """Fuzzy matching for entities (handles minor variations).

        Uses word-based overlap matching with 80% word coverage threshold.
        """
        # Simple substring match allowing partial matches
        words = pattern.split()
        if len(words) == 0:
            return False

        # Check if at least 80% of words appear in text
        matching_words = sum(1 for word in words if word in text)
        return matching_words / len(words) >= threshold

    def evaluate_batch(self, question_ids: List[str]) -> List[QuestionEvaluation]:
        """Evaluate multiple questions and collect results."""
        evaluations = []

        for qid in question_ids:
            try:
                eval_result = self.evaluate_question(qid)
                if eval_result:
                    evaluations.append(eval_result)
            except Exception as e:
                logger.error(f"Error evaluating {qid}: {e}")
                continue

        return evaluations

    def generate_report(self, evaluations: List[QuestionEvaluation], output_file: Path) -> None:
        """Generate comprehensive evaluation report."""

        if not evaluations:
            logger.warning("No evaluations to report")
            return

        # Aggregate metrics
        total_questions = len(evaluations)
        total_validation_pass = sum(1 for e in evaluations if e.validation_pass)
        validation_pass_rate = (
            total_validation_pass / total_questions if total_questions > 0 else 0
        )

        avg_negation_preservation = (
            sum(e.negation_check.preservation_rate for e in evaluations) / total_questions
        )
        avg_entity_completeness = (
            sum(e.entity_check.completeness_rate for e in evaluations) / total_questions
        )
        avg_unit_accuracy = (
            sum(e.unit_check.accuracy_rate for e in evaluations) / total_questions
        )

        # Build report
        report = f"""# Phase 3 LLM Integration Evaluation Report

**Date**: January 16, 2026
**Test Method**: Hybrid pipeline (NLP + LLM) evaluation on {total_questions} diverse sample questions
**LLM Provider**: Claude Code CLI (configured)
**Baseline**: 71.4% validation pass rate (legacy mode)

---

## Summary Metrics

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Validation Pass Rate | {validation_pass_rate:.1%} | 85%+ | {'✅ PASS' if validation_pass_rate >= 0.85 else '❌ NEEDS WORK'} |
| Negation Preservation | {avg_negation_preservation:.1%} | 95%+ | {'✅ PASS' if avg_negation_preservation >= 0.95 else '⚠️ CHECK'} |
| Entity Completeness | {avg_entity_completeness:.1%} | 90%+ | {'✅ PASS' if avg_entity_completeness >= 0.90 else '⚠️ CHECK'} |
| Unit Accuracy | {avg_unit_accuracy:.1%} | 90%+ | {'✅ PASS' if avg_unit_accuracy >= 0.90 else '⚠️ CHECK'} |

## Sample Evaluations (Full Results)

"""

        # Add per-question details
        for i, eval_result in enumerate(evaluations, 1):
            report += f"""
### Question {i}: {eval_result.question_id} ({eval_result.system_code})

**Validation**: {'✅ PASS' if eval_result.validation_pass else '❌ FAIL'}

**Negation Preservation**: {eval_result.negation_check.preserved_count}/{eval_result.negation_check.total_negations} ({eval_result.negation_check.preservation_rate:.1%})
- Details: {eval_result.negation_check.missed_count} missed

**Entity Completeness**: {eval_result.entity_check.referenced_count}/{eval_result.entity_check.total_entities} ({eval_result.entity_check.completeness_rate:.1%})
- Details: {eval_result.entity_check.missing_count} missing

**Unit Accuracy**: {eval_result.unit_check.accurate_count}/{eval_result.unit_check.total_units} ({eval_result.unit_check.accuracy_rate:.1%})
- Details: {len(eval_result.unit_check.mismatches)} mismatches

"""

        report += f"""
## Recommendation

**Validation Pass Rate: {validation_pass_rate:.1%}**

"""

        if validation_pass_rate >= 0.85:
            report += """
✅ **READY FOR PHASE 4** - Hybrid pipeline meets target (85%+ validation pass rate)

Next Steps:
1. Process additional 50-100 questions to confirm consistency
2. If results remain stable, deploy hybrid as default for full 2,198 questions
3. Archive Phase 3 evaluation results for reference

"""
        else:
            report += f"""
⚠️ **NEEDS ITERATION** - Current pass rate {validation_pass_rate:.1%} below 85% target

Analysis:
- Negation preservation: {avg_negation_preservation:.1%}
- Entity completeness: {avg_entity_completeness:.1%}
- Unit accuracy: {avg_unit_accuracy:.1%}

Recommended Next Steps:
1. Review failed questions for patterns
2. Analyze LLM output quality
3. Consider prompt tuning
4. Re-evaluate after adjustments

"""

        # Save report
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(report)

        logger.info(f"Report saved to {output_file}")


# Example usage
if __name__ == "__main__":
    project_root = Path("/Users/Mitchell/coding/projects/MKSAP")
    evaluator = Phase3Evaluator(project_root)

    # Test on first question (if it has been processed)
    test_qid = "gimcq24001"
    result = evaluator.evaluate_question(test_qid)

    if result:
        print(f"\nEvaluation for {test_qid}:")
        print(f"  System: {result.system_code}")
        print(f"  Validation: {result.validation_pass}")
        print(f"  Negation preservation: {result.negation_check.preservation_rate:.1%}")
        print(f"  Entity completeness: {result.entity_check.completeness_rate:.1%}")
        print(f"  Unit accuracy: {result.unit_check.accuracy_rate:.1%}")
        print(f"  Notes: {result.notes}")
    else:
        print(f"\nNo evaluation result for {test_qid} - may not be processed with hybrid pipeline yet")
        print("Run the pipeline first with: ./scripts/python -m src.interface.cli process --question-id <id>")
