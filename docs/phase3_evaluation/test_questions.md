# Phase 3 Test Questions

**Date**: January 16, 2026
**Purpose**: Evaluate hybrid pipeline improvements across diverse medical domains
**Total Questions**: 15
**Expected Processing Time**: ~30-60 seconds per question (with LLM calls)

## Selected Questions by System

| System | Code | Question ID | Question Type | Notes |
|--------|------|-------------|---------------|-------|
| Cardiovascular | cv | cvmcq24084 | MCQ | General cardiac question |
| Cardiovascular | cv | cvcor25010 | Core | Case-oriented review |
| Cardiovascular | cv | cvvdx24045 | VDX | Visual diagnosis exam |
| Endocrinology | en | encor25001 | Core | Case-oriented review |
| Endocrinology | en | enmcq24050 | MCQ | General endocrine question |
| Gastroenterology | gi | gimcq24025 | MCQ | General GI question |
| Gastroenterology | gi | gicor25001 | Core | Case-oriented review |
| Diabetes/Metabolic | dm | dmmcq24032 | MCQ | General metabolic question |
| Diabetes/Metabolic | dm | dmcor25001 | Core | Case-oriented review |
| Nephrology | np | npmcq24050 | MCQ | General renal question |
| Nephrology | np | npcor25001 | Core | Case-oriented review |
| Critical Care | cc | ccmcq24035 | MCQ | General critical care question |
| Critical Care | cc | cccor25002 | Core | Case-oriented review |
| Hematology-Oncology | hp | hpmcq24032 | MCQ | General hematology question |
| Hematology-Oncology | hp | hpcor25001 | Core | Case-oriented review |

## System Distribution

| System | Code | Count | Coverage |
|--------|------|-------|----------|
| Cardiovascular | cv | 3 | 20% |
| Endocrinology | en | 2 | 13.3% |
| Gastroenterology | gi | 2 | 13.3% |
| Diabetes/Metabolic | dm | 2 | 13.3% |
| Nephrology | np | 2 | 13.3% |
| Critical Care | cc | 2 | 13.3% |
| Hematology-Oncology | hp | 2 | 13.3% |
| **Total** | | **15** | **100%** |

## Question Type Distribution

| Type | Count | Purpose |
|------|-------|---------|
| MCQ (Multiple Choice) | 9 | Test general knowledge statements |
| Core (Case-Oriented Review) | 6 | Test contextual statement extraction from cases |
| VDX (Visual Diagnosis) | 1 | Test image-related statement handling (cv only) |

## Measurement Strategy

For each question, we measure the following metrics to evaluate hybrid pipeline improvements:

### 1. Negation Preservation
- **Metric**: Verify that negations detected by NLP preprocessing appear correctly in LLM-generated statements
- **Why**: Negations reverse meaning (e.g., "not present" vs "present"). Loss of negation = factual error
- **Evaluation**: Compare NLP negation detection output with final statement text
- **Pass Criteria**: All negations from NLP output must appear in generated statements

### 2. Entity Completeness
- **Metric**: All NLP-detected entities (medications, conditions, lab values) referenced in statements
- **Why**: Comprehensive statement requires all key entities mentioned in the question
- **Evaluation**: Cross-reference NLP entity extraction output with statement content
- **Pass Criteria**: ≥90% of detected entities appear in statements

### 3. Unit Accuracy
- **Metric**: Exact numeric values and comparators (>, <, ≥, ≤) preserved correctly
- **Why**: Clinical values depend on units and magnitude (e.g., "BP >140/90" vs ">240/120" are very different)
- **Evaluation**: Extract numeric values from source → compare to statements
- **Pass Criteria**: 100% accuracy on numeric values and comparison operators

### 4. Hybrid Pipeline Comparison
- **Legacy Baseline**: Direct LLM extraction (Phase 2 approach)
- **Hybrid Approach**: NLP preprocessing + LLM refinement (Phase 3 approach)
- **Metric**: Count improvements across the three categories above
- **Expected Outcome**: Hybrid approach should show ≥15% improvement in aggregate metrics

## Processing Notes

- All questions are confirmed to exist in `/Users/Mitchell/coding/projects/MKSAP/mksap_data/`
- Mix of question types ensures testing across different content patterns
- Seven distinct medical systems provide good coverage of clinical domains
- Processing should be done sequentially to allow detailed analysis of each question
- Output will be stored in: `statement_generator/artifacts/phase3_evaluation/`
