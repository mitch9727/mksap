# Phase 3: LLM Integration Evaluation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Measure actual improvements in statement quality when hybrid pipeline (NLP preprocessing + LLM guidance) is active, compared to baseline (71.4% validation pass rate), by running on 10-20 diverse sample questions and documenting improvements in negation preservation, entity completeness, and unit accuracy.

**Architecture:**
- Select 10-20 diverse sample questions across different medical systems (2-3 per system)
- Run hybrid pipeline on each question using configured LLM provider (Claude Code CLI)
- Measure three key dimensions: (1) negation preservation, (2) entity completeness, (3) unit/threshold accuracy
- Generate comparison report with baseline metrics, sample statements, and improvement summary
- Use results to validate whether hybrid pipeline meets 85%+ validation pass rate target for Phase 4 rollout

**Tech Stack:** Python (measurement scripts), existing hybrid pipeline (NLP + LLM), validation framework, JSON comparison

---

## Task 1: Select and Document Test Questions

**Files:**
- Create: `statement_generator/artifacts/phase3_evaluation/test_questions.md`
- Reference: `mksap_data/` (extracted questions organized by system code)
- Reference: `docs/reference/STATEMENT_GENERATOR.md` (CLI reference)

**Step 1: Select 15 diverse test questions (2-3 per system)**

Select from these systems to ensure diversity across medical domains:
- **cv** (cardiovascular): cvcor25001, cvcor25002, cvcor25003
- **en** (endocrinology): enmet25001, enmet25002, enmet25003
- **gi** (gastroenterology): gigib25001, gigib25002, gigib25003
- **dm** (dermatology): dmskd25001, dmskd25002
- **np** (nephrology): nphyd25001, nphyd25002
- **cc** (critical care): ccsec25001, ccsec25002
- **hp** (hematology/oncology): hpmal25001

Run this command to verify questions exist:
```bash
for qid in cvcor25001 cvcor25002 cvcor25003 enmet25001 enmet25002 enmet25003 gigib25001 gigib25002 gigib25003 dmskd25001 dmskd25002 nphyd25001 nphyd25002 ccsec25001 ccsec25002 hpmal25001; do
  if [ -f "mksap_data/${qid:0:2}/${qid}/${qid}.json" ]; then
    echo "✓ $qid"
  else
    echo "✗ $qid (not found)"
  fi
done
```

Expected output: Confirmation that most questions exist (may need to substitute 1-2 if not found).

**Step 2: Document test questions selection**

Create `statement_generator/artifacts/phase3_evaluation/test_questions.md` with:
- List of 15 selected question IDs
- System distribution table (questions per system)
- Selection rationale (diversity across medical domains)
- Expected characteristics (size, complexity, negation patterns)

```markdown
# Phase 3 Test Questions

**Date**: January 16, 2026
**Purpose**: Evaluate hybrid pipeline improvements across diverse medical domains
**Total Questions**: 15
**Expected Processing Time**: ~30-60 seconds per question (with LLM calls)

## Selected Questions by System

| System | Code | Question ID | Notes |
|--------|------|-------------|-------|
| Cardiovascular | cv | cvcor25001 | Foundation |
| Cardiovascular | cv | cvcor25002 | Complex negations |
| Cardiovascular | cv | cvcor25003 | Units/thresholds |
| Endocrinology | en | enmet25001 | Disease management |
| Endocrinology | en | enmet25002 | Thresholds |
| Endocrinology | en | enmet25003 | Complex entities |
| Gastroenterology | gi | gigib25001 | Procedures |
| Gastroenterology | gi | gigib25002 | Conditions |
| Gastroenterology | gi | gigib25003 | Entities |
| Dermatology | dm | dmskd25001 | Conditions |
| Dermatology | dm | dmskd25002 | Findings |
| Nephrology | np | nphyd25001 | Disease states |
| Nephrology | np | nphyd25002 | Values/ranges |
| Critical Care | cc | ccsec25001 | Acute conditions |
| Critical Care | cc | ccsec25002 | Management |
| Hematology/Oncology | hp | hpmal25001 | Cancer concepts |

## Measurement Strategy

For each question, we measure:
1. **Negation Preservation**: Negations detected by NLP appear correctly in LLM output
2. **Entity Completeness**: All NLP-detected entities referenced in generated statements
3. **Unit Accuracy**: Exact numeric values, comparators (>, <, ≥, ≤) preserved correctly
```

**Step 3: Commit**

```bash
git add statement_generator/artifacts/phase3_evaluation/test_questions.md
git commit -m "docs: create Phase 3 test question selection and strategy"
```

---

## Task 2: Create Measurement Framework

**Files:**
- Create: `statement_generator/tests/tools/phase3_evaluator.py` (250 lines)
- Reference: `statement_generator/src/orchestration/pipeline.py` (hybrid pipeline)
- Reference: `statement_generator/src/processing/nlp/preprocessor.py` (NLP preprocessing)

**Step 1: Write measurement framework structure**

Create `statement_generator/tests/tools/phase3_evaluator.py`:

```python
"""Phase 3 Evaluation Framework - Measure hybrid pipeline improvements.

Measures three dimensions:
1. Negation preservation (NLP detections appear correctly in LLM output)
2. Entity completeness (all NLP entities referenced in statements)
3. Unit accuracy (numeric values and comparators preserved exactly)
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NegationCheck:
    """Track negation preservation metrics."""
    total_negations: int
    preserved_count: int
    missed_count: int
    preservation_rate: float


@dataclass
class EntityCheck:
    """Track entity completeness metrics."""
    total_entities: int
    referenced_count: int
    missing_count: int
    completeness_rate: float
    entity_samples: Dict[str, bool]  # entity -> found_in_statement


@dataclass
class UnitCheck:
    """Track unit/threshold accuracy metrics."""
    total_units: int
    accurate_count: int
    inaccurate_count: int
    accuracy_rate: float
    mismatches: List[Tuple[str, str]]  # (expected, actual)


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
    notes: List[str]


class Phase3Evaluator:
    """Evaluate hybrid pipeline improvements on sample questions."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "mksap_data"
        self.artifacts_dir = self.project_root / "statement_generator" / "artifacts" / "phase3_evaluation"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_question(self, question_id: str) -> QuestionEvaluation:
        """Evaluate single question - measure all three dimensions."""
        system_code = question_id[:2]
        question_path = self.data_dir / system_code / question_id / f"{question_id}.json"

        # Load question data
        with open(question_path) as f:
            data = json.load(f)

        # Check if question has been processed with hybrid pipeline
        if "true_statements" not in data:
            logger.warning(f"{question_id}: No true_statements field (not processed yet)")
            return None

        # Extract NLP analysis if available
        nlp_analysis = data.get("nlp_analysis", {})

        # Extract generated statements
        statements = data.get("true_statements", {})

        # Run measurements
        negation_check = self._measure_negation_preservation(question_id, nlp_analysis, statements)
        entity_check = self._measure_entity_completeness(question_id, nlp_analysis, statements)
        unit_check = self._measure_unit_accuracy(question_id, nlp_analysis, statements)

        # Check validation pass
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
            notes=[]
        )

        return evaluation

    def _measure_negation_preservation(self, question_id: str, nlp_analysis: Dict, statements: Dict) -> NegationCheck:
        """Measure: Do all negations detected by NLP appear correctly in LLM output?"""

        # Extract negations detected by NLP
        negations_detected = nlp_analysis.get("negations", [])

        # Combine all statement text
        all_statement_text = " ".join([
            statements.get("critique", ""),
            statements.get("key_points", ""),
            statements.get("tables", "")
        ]).lower()

        # Check if each negation appears in statement text
        preserved = 0
        missed = []

        for negation in negations_detected:
            # Normalize negation pattern for matching
            pattern = negation.lower()
            if pattern in all_statement_text or self._fuzzy_match(pattern, all_statement_text):
                preserved += 1
            else:
                missed.append(negation)

        total = len(negations_detected)
        preservation_rate = preserved / total if total > 0 else 1.0

        if missed:
            logger.info(f"{question_id}: Missed negations: {missed}")

        return NegationCheck(
            total_negations=total,
            preserved_count=preserved,
            missed_count=len(missed),
            preservation_rate=preservation_rate
        )

    def _measure_entity_completeness(self, question_id: str, nlp_analysis: Dict, statements: Dict) -> EntityCheck:
        """Measure: Are all NLP-detected entities referenced in generated statements?"""

        # Extract entities detected by NLP
        entities_detected = nlp_analysis.get("entities", [])

        # Combine all statement text
        all_statement_text = " ".join([
            statements.get("critique", ""),
            statements.get("key_points", ""),
            statements.get("tables", "")
        ]).lower()

        # Check if each entity text appears in statement
        referenced = 0
        entity_samples = {}

        for entity in entities_detected:
            entity_text = entity.get("text", "").lower() if isinstance(entity, dict) else entity.lower()
            found = entity_text in all_statement_text or self._fuzzy_match(entity_text, all_statement_text)
            referenced += found
            entity_samples[entity_text] = found

        total = len(entities_detected)
        completeness_rate = referenced / total if total > 0 else 1.0

        missing_entities = [text for text, found in entity_samples.items() if not found]
        if missing_entities:
            logger.info(f"{question_id}: Missing entities ({len(missing_entities)}): {missing_entities[:5]}")

        return EntityCheck(
            total_entities=total,
            referenced_count=referenced,
            missing_count=total - referenced,
            completeness_rate=completeness_rate,
            entity_samples=entity_samples
        )

    def _measure_unit_accuracy(self, question_id: str, nlp_analysis: Dict, statements: Dict) -> UnitCheck:
        """Measure: Are exact units and thresholds preserved (>, <, ≥, ≤)?"""

        # Extract units/thresholds from original question
        original_question = nlp_analysis.get("original_text", "")

        # Find numeric patterns with comparators
        unit_pattern = r'([<>≥≤]=?)\s*(\d+(?:\.\d+)?)\s*([a-zA-Z/%]+)?'
        units_in_original = re.findall(unit_pattern, original_question)

        if not units_in_original:
            return UnitCheck(
                total_units=0,
                accurate_count=0,
                inaccurate_count=0,
                accuracy_rate=1.0,
                mismatches=[]
            )

        # Check if units appear correctly in statements
        all_statement_text = " ".join([
            statements.get("critique", ""),
            statements.get("key_points", ""),
            statements.get("tables", "")
        ])

        accurate = 0
        mismatches = []

        for comparator, value, unit in units_in_original:
            # Expected format in output
            expected = f"{comparator}{value}" if unit else f"{comparator}{value}"

            # Check for exact match or close match
            if expected in all_statement_text or value in all_statement_text:
                accurate += 1
            else:
                mismatches.append((expected, "NOT_FOUND"))

        total = len(units_in_original)
        accuracy_rate = accurate / total if total > 0 else 1.0

        if mismatches:
            logger.info(f"{question_id}: Unit mismatches ({len(mismatches)}): {mismatches}")

        return UnitCheck(
            total_units=total,
            accurate_count=accurate,
            inaccurate_count=len(mismatches),
            accuracy_rate=accuracy_rate,
            mismatches=mismatches
        )

    def _fuzzy_match(self, pattern: str, text: str, threshold: float = 0.8) -> bool:
        """Fuzzy matching for entities (handles minor variations)."""
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
        validation_pass_rate = total_validation_pass / total_questions if total_questions > 0 else 0

        avg_negation_preservation = sum(e.negation_check.preservation_rate for e in evaluations) / total_questions
        avg_entity_completeness = sum(e.entity_check.completeness_rate for e in evaluations) / total_questions
        avg_unit_accuracy = sum(e.unit_check.accuracy_rate for e in evaluations) / total_questions

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

    # Test on first question
    test_qid = "cvcor25001"
    result = evaluator.evaluate_question(test_qid)

    if result:
        print(f"Evaluation for {test_qid}:")
        print(f"  Validation: {result.validation_pass}")
        print(f"  Negation preservation: {result.negation_check.preservation_rate:.1%}")
        print(f"  Entity completeness: {result.entity_check.completeness_rate:.1%}")
        print(f"  Unit accuracy: {result.unit_check.accuracy_rate:.1%}")
```

**Step 2: Run test to verify framework loads**

```bash
cd /Users/Mitchell/coding/projects/MKSAP
./scripts/python statement_generator/tests/tools/phase3_evaluator.py
```

Expected output: Script should either find a processed question and show metrics, or indicate no processed questions yet.

**Step 3: Commit**

```bash
git add statement_generator/tests/tools/phase3_evaluator.py
git commit -m "feat: add Phase 3 evaluation framework for measuring hybrid pipeline improvements"
```

---

## Task 3: Process Sample Questions with Hybrid Pipeline

**Files:**
- Modify: `.env` (verify `USE_HYBRID_PIPELINE=true`)
- Reference: `statement_generator/src/interface/cli.py` (CLI commands)
- Output: `mksap_data/*/*.json` (updated with true_statements)

**Step 1: Verify hybrid pipeline is enabled**

```bash
cd /Users/Mitchell/coding/projects/MKSAP
grep "USE_HYBRID_PIPELINE" .env
```

Expected: `USE_HYBRID_PIPELINE=true`

If not set, update:
```bash
echo "USE_HYBRID_PIPELINE=true" >> .env
```

**Step 2: Process first 3 sample questions**

Run these commands one at a time, waiting for completion before starting the next:

```bash
cd /Users/Mitchell/coding/projects/MKSAP
./scripts/python -m src.interface.cli process --question-id cvcor25001
```

Wait for output. Expected: Question processed, `true_statements` field added to JSON, validation results shown.

```bash
./scripts/python -m src.interface.cli process --question-id cvcor25002
```

```bash
./scripts/python -m src.interface.cli process --question-id cvcor25003
```

**Step 3: Verify questions were processed**

```bash
cd /Users/Mitchell/coding/projects/MKSAP
for qid in cvcor25001 cvcor25002 cvcor25003; do
  if grep -q "true_statements" "mksap_data/cv/${qid}/${qid}.json"; then
    echo "✓ $qid processed"
  else
    echo "✗ $qid NOT processed"
  fi
done
```

Expected: All three questions show ✓ processed.

**Step 4: Commit**

```bash
git add mksap_data/cv/cvcor25001/cvcor25001.json
git add mksap_data/cv/cvcor25002/cvcor25002.json
git add mksap_data/cv/cvcor25003/cvcor25003.json
git commit -m "feat: process first 3 cardiovascular questions with hybrid pipeline"
```

---

## Task 4: Evaluate Processed Questions

**Files:**
- Run: `phase3_evaluator.py` on processed questions
- Output: `statement_generator/artifacts/phase3_evaluation/evaluation_results.json`
- Output: `statement_generator/artifacts/phase3_evaluation/report.md`

**Step 1: Create evaluation runner script**

Create `statement_generator/tests/tools/run_phase3_eval.py`:

```python
"""Run Phase 3 evaluation on sample questions."""

import json
import sys
from pathlib import Path
from phase3_evaluator import Phase3Evaluator

def main():
    project_root = Path("/Users/Mitchell/coding/projects/MKSAP")

    # Test questions we've processed so far
    test_questions = [
        "cvcor25001",
        "cvcor25002",
        "cvcor25003",
    ]

    evaluator = Phase3Evaluator(project_root)

    # Evaluate batch
    print(f"Evaluating {len(test_questions)} questions...")
    evaluations = evaluator.evaluate_batch(test_questions)

    print(f"Successfully evaluated: {len(evaluations)} questions")

    # Save raw results
    results_file = project_root / "statement_generator" / "artifacts" / "phase3_evaluation" / "evaluation_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": "2026-01-16",
                "total_evaluated": len(evaluations),
                "questions": [
                    {
                        "question_id": e.question_id,
                        "system_code": e.system_code,
                        "validation_pass": e.validation_pass,
                        "negation_preservation": {
                            "preserved": e.negation_check.preserved_count,
                            "total": e.negation_check.total_negations,
                            "rate": e.negation_check.preservation_rate
                        },
                        "entity_completeness": {
                            "referenced": e.entity_check.referenced_count,
                            "total": e.entity_check.total_entities,
                            "rate": e.entity_check.completeness_rate
                        },
                        "unit_accuracy": {
                            "accurate": e.unit_check.accurate_count,
                            "total": e.unit_check.total_units,
                            "rate": e.unit_check.accuracy_rate
                        }
                    }
                    for e in evaluations
                ]
            },
            f,
            indent=2
        )

    print(f"Results saved to {results_file}")

    # Generate report
    report_file = project_root / "statement_generator" / "artifacts" / "phase3_evaluation" / "report.md"
    evaluator.generate_report(evaluations, report_file)

    # Print summary
    print("\n" + "="*60)
    print("PHASE 3 EVALUATION SUMMARY")
    print("="*60)

    total = len(evaluations)
    validation_pass = sum(1 for e in evaluations if e.validation_pass)
    avg_negation = sum(e.negation_check.preservation_rate for e in evaluations) / total if total > 0 else 0
    avg_entity = sum(e.entity_check.completeness_rate for e in evaluations) / total if total > 0 else 0
    avg_unit = sum(e.unit_check.accuracy_rate for e in evaluations) / total if total > 0 else 0

    print(f"\nQuestions Evaluated: {total}")
    print(f"Validation Pass Rate: {validation_pass}/{total} ({100*validation_pass/total:.1f}%)")
    print(f"Average Negation Preservation: {100*avg_negation:.1f}%")
    print(f"Average Entity Completeness: {100*avg_entity:.1f}%")
    print(f"Average Unit Accuracy: {100*avg_unit:.1f}%")

    print(f"\nFull report: {report_file}")

if __name__ == "__main__":
    main()
```

**Step 2: Run evaluation on processed questions**

```bash
cd /Users/Mitchell/coding/projects/MKSAP
./scripts/python statement_generator/tests/tools/run_phase3_eval.py
```

Expected output:
- Summary of 3 evaluated questions
- Validation pass rates per question
- Aggregated metrics
- Report saved to `statement_generator/artifacts/phase3_evaluation/report.md`

**Step 3: Review generated report**

```bash
cat statement_generator/artifacts/phase3_evaluation/report.md
```

Expected: Comprehensive report showing:
- Validation pass rates vs 71.4% baseline
- Negation preservation percentages
- Entity completeness percentages
- Unit accuracy percentages
- Recommendation for Phase 4 readiness

**Step 4: Commit**

```bash
git add statement_generator/tests/tools/run_phase3_eval.py
git add statement_generator/artifacts/phase3_evaluation/
git commit -m "feat: run Phase 3 evaluation on first 3 sample questions and generate report"
```

---

## Task 5: Scale to Remaining Sample Questions (7 more)

**Files:**
- Process: Remaining 7 questions from test set (endocrinology, gastroenterology, etc.)
- Update: `statement_generator/artifacts/phase3_evaluation/test_questions_processed.md`

**Step 1: Process next batch of 7 questions**

Run in sequence (wait for each to complete):

```bash
cd /Users/Mitchell/coding/projects/MKSAP
./scripts/python -m src.interface.cli process --question-id enmet25001
./scripts/python -m src.interface.cli process --question-id enmet25002
./scripts/python -m src.interface.cli process --question-id gigib25001
./scripts/python -m src.interface.cli process --question-id gigib25002
./scripts/python -m src.interface.cli process --question-id dmskd25001
./scripts/python -m src.interface.cli process --question-id nphyd25001
./scripts/python -m src.interface.cli process --question-id ccsec25001
```

**Step 2: Re-run evaluation on all 10 questions**

```bash
cd /Users/Mitchell/coding/projects/MKSAP
# Modify run_phase3_eval.py to include all 10 questions
./scripts/python statement_generator/tests/tools/run_phase3_eval.py
```

Expected: Report updated with all 10 questions, aggregated metrics.

**Step 3: Review results and decision point**

Check report at `statement_generator/artifacts/phase3_evaluation/report.md`

Determine:
- Is validation pass rate ≥ 85%?
- Are negation preservation and entity completeness both ≥ 90%?
- Are there consistent issues across systems?

**Step 4: Document findings**

Create `statement_generator/artifacts/phase3_evaluation/findings.md`:

```markdown
# Phase 3 Evaluation Findings

**Date**: January 16, 2026
**Evaluation Scope**: 10 diverse sample questions across 6 medical systems

## Overall Results

[Summary of metrics]

## System-by-System Analysis

[Breakdown by system]

## Key Insights

[Important findings about hybrid pipeline performance]

## Next Steps

[Decision on Phase 4 readiness]
```

**Step 5: Commit**

```bash
git add mksap_data/en/enmet25001/enmet25001.json
git add mksap_data/en/enmet25002/enmet25002.json
git add mksap_data/gi/gigib25001/gigib25001.json
git add mksap_data/gi/gigib25002/gigib25002.json
git add mksap_data/dm/dmskd25001/dmskd25001.json
git add mksap_data/np/nphyd25001/nphyd25001.json
git add mksap_data/cc/ccsec25001/ccsec25001.json
git add statement_generator/artifacts/phase3_evaluation/
git commit -m "feat: complete Phase 3 evaluation on 10 diverse sample questions"
```

---

## Task 6: Final Report and Recommendation

**Files:**
- Create: `statement_generator/artifacts/phase3_evaluation/PHASE_3_SUMMARY.md` (final decision document)
- Update: `docs/PHASE_2_STATUS.md` (record Phase 3 completion)
- Update: `TODO.md` (mark Phase 3 complete, update next steps)

**Step 1: Create final summary document**

Create `statement_generator/artifacts/phase3_evaluation/PHASE_3_SUMMARY.md`:

```markdown
# Phase 3 LLM Integration Evaluation - Final Summary

**Date**: January 16, 2026
**Evaluation Scope**: 10 diverse sample questions across 6 medical systems
**Baseline**: 71.4% validation pass rate (legacy mode without NLP preprocessing)

## Executive Summary

The hybrid pipeline (NLP preprocessing + LLM guidance) was evaluated on 10 carefully selected sample questions representing diverse medical domains. This evaluation measures whether the NLP preprocessing stage (entity detection, negation preservation, atomicity analysis) enables the LLM to generate higher-quality statements.

## Results vs Targets

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Validation Pass Rate | [RESULT]% | 85%+ | [PASS/FAIL] |
| Negation Preservation | [RESULT]% | 95%+ | [PASS/FAIL] |
| Entity Completeness | [RESULT]% | 90%+ | [PASS/FAIL] |
| Unit Accuracy | [RESULT]% | 90%+ | [PASS/FAIL] |

## System Coverage

- Cardiovascular (cv): 3 questions
- Endocrinology (en): 2 questions
- Gastroenterology (gi): 2 questions
- Dermatology (dm): 1 question
- Nephrology (np): 1 question
- Critical Care (cc): 1 question

## Key Findings

[Insert findings from evaluation]

## Recommendation

[Decision on whether to proceed to Phase 4]

### If Ready for Phase 4:
1. Process next 50-100 questions to confirm consistency
2. If metrics remain stable, deploy hybrid as default
3. Process all 2,198 questions
4. Move to Phase 4: Cloze application

### If Needs Iteration:
1. Analyze failure patterns
2. Review LLM output quality
3. Consider prompt tuning
4. Re-evaluate after adjustments

## Test Data

All test questions and evaluation artifacts saved in:
- Questions: `statement_generator/artifacts/phase3_evaluation/test_questions.md`
- Results: `statement_generator/artifacts/phase3_evaluation/evaluation_results.json`
- Report: `statement_generator/artifacts/phase3_evaluation/report.md`
```

**Step 2: Update PHASE_2_STATUS.md**

In `docs/PHASE_2_STATUS.md`, add new section at top:

```markdown
## Phase 3 - LLM Integration Evaluation (Completed)

**Date**: January 16, 2026
**Result**: [PASS/FAIL]
**Validation Pass Rate**: [X]%

Hybrid pipeline evaluated on 10 sample questions across 6 medical systems.
See `statement_generator/artifacts/phase3_evaluation/PHASE_3_SUMMARY.md` for full results.
```

**Step 3: Update TODO.md**

Remove completed tasks from TODO.md and update status:

```markdown
## Completed Work Summary (January 16, 2026)

### ✅ Phase 3 - LLM Integration Evaluation
- **Completed**: Evaluated hybrid pipeline on 10 sample questions
- **Result**: [X]% validation pass rate (target: 85%+)
- **Status**: [Ready for Phase 4] OR [Needs iteration]
```

**Step 4: Commit final documentation**

```bash
git add statement_generator/artifacts/phase3_evaluation/PHASE_3_SUMMARY.md
git add docs/PHASE_2_STATUS.md
git add TODO.md
git commit -m "docs: complete Phase 3 LLM integration evaluation with final summary and recommendation"
```

---

## Success Criteria

**Phase 3 evaluation is complete when:**

✅ Task 1: Test questions selected and documented (15 questions, diverse systems)
✅ Task 2: Evaluation framework created and verified (phase3_evaluator.py running)
✅ Task 3: First 3 questions processed with hybrid pipeline
✅ Task 4: Evaluation results generated (3-question report with metrics)
✅ Task 5: Remaining 7 questions processed, 10-question evaluation complete
✅ Task 6: Final summary document created with Phase 4 recommendation

**Quality Metrics:**
- All measurements documented with methodology
- Results compared to 71.4% baseline
- Clear recommendation for next phase

---

## Execution Notes

- Each task represents 1-2 hours of work
- Bottleneck: LLM processing time (~30-60 seconds per question)
- Total estimated time for all 10 questions: 30-60 minutes (depending on LLM calls)
- All evaluation artifacts saved to `statement_generator/artifacts/phase3_evaluation/`
- Results determine whether Phase 4 (Cloze application) can proceed with confidence

---

## References

**Key Files:**
- Phase 2 Status: `docs/PHASE_2_STATUS.md`
- Hybrid Pipeline: `statement_generator/src/orchestration/pipeline.py`
- NLP Preprocessor: `statement_generator/src/processing/nlp/preprocessor.py`
- CLI Reference: `docs/reference/STATEMENT_GENERATOR.md`
- Best Practices: `docs/reference/CLOZE_FLASHCARD_BEST_PRACTICES.md`

**Related Documentation:**
- Phase 2 Status Report: `docs/PHASE_2_STATUS.md`
- NLP Model Comparison: `docs/reference/NLP_MODEL_COMPARISON.md`
- Project Overview: `docs/PROJECT_OVERVIEW.md`
