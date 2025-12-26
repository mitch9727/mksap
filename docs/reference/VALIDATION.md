# Rust MKSAP Extractor - Validation Guide

## Data Validation Overview

The Rust MKSAP Extractor includes comprehensive validation to ensure extracted question data meets quality standards and matches the specification.

## Running Validation

### Validate All Extracted Data

```bash
cd "/Users/Mitchell/coding/projects/MKSAP/Rust MKSAP Extractor"
./target/release/mksap-extractor validate
```

### What Validation Checks

The validator performs these checks on all extracted questions:

1. **File Existence**
   - JSON file present: `{id}.json`
   - Metadata file present: `{id}_metadata.txt`

2. **JSON Structure**
   - Valid JSON syntax
   - All required fields present
   - Correct data types

3. **Required Fields**
   - question_id
   - category
   - educational_objective
   - question_text
   - question_stem
   - options (array with A, B, C, D)
   - correct_answer
   - critique
   - key_points
   - references
   - metadata

4. **Data Integrity**
   - Options have letter and text
   - Correct answer matches option letter
   - Key points are non-empty
   - Metadata contains expected fields

5. **Specification Compliance**
   - Question ID format correct
   - Category matches system code
   - Data matches API schema
   - Coverage compared to specification

## Understanding Validation Reports

### Validation Report Output

```
=== MKSAP DATA VALIDATION REPORT ===

Total Questions Found: 754
Total Valid Questions: 754
Total Invalid Questions: 0
Validity Rate: 100.0%

=== PER-SYSTEM SUMMARY ===

✓ cv: 130/216 questions (60.2%)
✓ en: 91/136 questions (66.9%)
⚠ hm: 61/125 questions (48.8%)
⚠ id: 87/205 questions (42.4%)
⚠ np: 104/155 questions (67.1%)
⚠ nr: 74/118 questions (62.7%)
⚠ on: 64/103 questions (62.1%)
⚠ rm: 77/131 questions (58.8%)

=== SPECIFICATION COMPLIANCE REPORT ===

Overall Coverage: 754/1810 questions (41.7%)

Systems with Good Progress (>50%):
✓ cv: 130/216 (60.2%)
✓ en: 91/136 (66.9%)
✓ np: 104/155 (67.1%)
✓ nr: 74/118 (62.7%)
✓ on: 64/103 (62.1%)

Systems with Partial Progress (30-50%):
⚠ hm: 61/125 (48.8%)
⚠ id: 87/205 (42.4%)
⚠ rm: 77/131 (58.8%)

Missing Systems (0%):
✗ cc: 0/206 (0.0%)
✗ gi: 0/154 (0.0%)
✗ in: 0/199 (0.0%)
✗ pm: 0/162 (0.0%)
```

### Report Interpretation

**Green (✓)**: System >60% complete
**Yellow (⚠)**: System 30-60% complete
**Red (✗)**: System 0% or not started

**Validity Rate**: Percentage of extracted questions that are valid
- 100% = All questions valid (no corruption)
- <100% = Some questions have issues

## Data Quality Metrics

### Current Status (as of Dec 22, 2025)

| Metric | Value | Status |
|--------|-------|--------|
| Total Valid Questions | 754 | ✓ Excellent |
| Validity Rate | 100% | ✓ Perfect |
| JSON Parse Success | 754/754 | ✓ Perfect |
| Required Fields Present | 754/754 | ✓ Perfect |
| Structure Compliance | 754/754 | ✓ Perfect |
| Overall Coverage | 41.7% | ◐ Good Progress |

## Known Issues

### 1. Folder Naming vs API Codes

**Issue**: Interdisciplinary Medicine uses `in` for question IDs while the web path remains `/dmin/`.

**Mitigation**:
- Current data is valid and usable
- Question IDs remain consistent across API responses

### 2. Incomplete System Extraction

**Issue**: 4 system codes have 0 questions extracted

**Systems**:
- Clinical Practice (cc)
- Gastroenterology (gi)
- Interdisciplinary Medicine (in)
- Pulmonary & Critical Care (pm)

**Cause**: Extraction not yet run for these systems

**Resolution**: Continue extraction phase to complete all systems

### 3. Peer Performance Data

**Issue**: `peer_percentage` values are always 0

**Reason**: API doesn't provide this data during bulk extraction

**Impact**: Minor - only needed for comparative learning features

## Validation Workflow

### Recommended Validation Schedule

1. **After Each Extraction Session**
   ```bash
   ./target/release/mksap-extractor validate
   ```

2. **Before Using Data**
   - Verify validity rate is 100%
   - Check coverage meets requirements

3. **Before Adding to Production**
   - Run validation
   - Review per-system summaries
   - Check for any issues

## Fixing Invalid Data

### If Validation Finds Issues

1. **Identify Problem Questions**
   - Note question IDs flagged as invalid
   - Understand what validation failed

2. **Root Cause**
   - File corruption during download
   - Network error during write
   - API returned malformed data

3. **Resolution**
   ```bash
   # Delete problematic question directory
   rm -rf mksap_data/cv/cvmcq24001/

   # Re-run extraction (will skip existing valid questions)
   ./target/release/mksap-extractor
   ```

4. **Verify Fix**
   ```bash
   ./target/release/mksap-extractor validate
   ```

## Validation Implementation

### Validator Module

The validator is implemented in `src/validator.rs`:

**Key Functions**:
- `validate_extraction()` - Scan and validate all questions
- `validate_question()` - Check single question
- `generate_report()` - Create human-readable report
- `compare_with_specification()` - Compare with expectations

**Validation is Non-Destructive**:
- Only reads files
- Creates no modifications
- Generates report only
- Safe to run anytime

## Using Validation Results

### For Quality Assurance

1. Track validity rate over time
2. Monitor per-system progress
3. Identify problematic systems early
4. Plan extraction phases based on gaps

### For Extraction Planning

```
Current: 754/1810 (41.7%)
Missing: 1056 questions

Priority Order:
1. Complete partial systems (hm, id, rm) → +200 more
2. Extract missing systems (cc, gi, in, pm) → +721 more
3. Fill gaps in progress systems → +135 more
```

### For Data Usage

- **100% validity**: Safe to use entire dataset
- **Incomplete coverage**: Plan workflows around missing systems
- **Known issues**: Document in code when using
- **Named quirks**: Handle folder naming in scripts

## Next Steps

1. Run validation regularly during extraction
2. Monitor per-system coverage progress
3. Plan extraction phases for missing systems
4. Review [Troubleshooting Guide](troubleshooting.md) if issues found
5. Check [Architecture](architecture.md) for technical details
