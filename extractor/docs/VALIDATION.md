# Rust MKSAP Extractor - Validation Guide

## Data Validation Overview

The Rust MKSAP Extractor includes comprehensive validation to ensure extracted question data meets quality standards and
matches the specification.

## Running Validation

### Validate All Extracted Data

```bash
cd /path/to/MKSAP/extractor
./target/release/mksap-extractor validate
```

### What Validation Checks

The validator performs these checks on all extracted questions:

1. **File Existence**
   - JSON file present: `{id}.json`

2. **JSON Structure**
   - Valid JSON syntax
   - All required fields present
   - Correct data types

3. **Required Fields**
   - question_id
   - category
   - educational_objective
   - metadata
   - question_text
   - question_stem
   - options (array with letter/text)
   - user_performance
   - critique
   - key_points
   - references
   - related_content
   - media
   - extracted_at

4. **Data Integrity**
   - Options have letter and text
   - `user_performance.correct_answer` present
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

Total Questions Found: <count>
Total Valid Questions: <count>
Total Invalid Questions: <count>

=== INVALID BREAKDOWN ===
Missing JSON: <count>
Parse Errors: <count>
Schema Invalid: <count>

=== PER-SYSTEM SUMMARY ===

✓ cv: <found>/<discovered> questions (<pct>%)
✓ en: <found>/<discovered> questions (<pct>%)
...

=== SPECIFICATION COMPLIANCE REPORT ===

Overall Coverage: <found>/<discovered> questions (<pct>%)
```

### Report Interpretation

**Green (✓)**: System at or above discovered count **Yellow (⚠)**: System partially extracted **Red (✗)**: System empty
or not started

**Validity Rate**: Percentage of extracted questions that are valid
- 100% = All questions valid (no corruption)
- <100% = Some questions have issues

## Data Quality Metrics

Use the validation report to track:

- Total questions found vs. valid
- Invalid breakdown (missing JSON, parse errors, schema issues)
- Per-system completion using discovery metadata (required)

## Known Issues

### 1. Folder Naming vs API Codes

**Issue**: Interdisciplinary Medicine uses `in` for question IDs while the web path remains `/dmin/`.

**Mitigation**:
- Current data is valid and usable
- Question IDs remain consistent across API responses

### 2. Missing Discovery Metadata

**Issue**: Validation now fails if `.checkpoints/discovery_metadata.json` is missing.

**Resolution**: Run extraction (or `media-discover` plus discovery metadata generation) to produce discovery metadata
before validating.

### 3. Peer Performance Data

**Issue**: `peer_percentage` values are always 0

**Reason**: API doesn't provide this data during bulk extraction

**Impact**: Minor - only needed for comparative learning features

## Validation Workflow

### Recommended Validation Schedule

1. **After Each Extraction Session** ```bash ./target/release/mksap-extractor validate ```

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

3. **Resolution** ```bash # Delete problematic question directory rm -rf mksap_data/cv/cvmcq24001/

# Re-run extraction (will skip existing valid questions) ./target/release/mksap-extractor
   ```

4. **Verify Fix**
   ```bash
./target/release/mksap-extractor validate
   ```

## Validation Implementation

### Validator Module

The validator is implemented in the extractor validation module:

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

- Use `discovery-stats` to see discovered counts per system.
- Use `list-missing` to generate a remaining ID list for targeted retries.

### For Data Usage

- **100% validity**: Safe to use entire dataset
- **Incomplete coverage**: Plan workflows around missing systems
- **Named quirks**: Handle folder naming in scripts
- **100% validity**: Safe to use entire dataset

## Discovery-Based Completion Tracking

### How It Works

1. **Discovery Phase**: Each extraction run discovers available questions via HTTP HEAD requests
2. **Metadata Storage**: Statistics saved to `.checkpoints/discovery_metadata.json`:
   - Discovered count per system
   - Candidates tested (how many IDs were checked)
   - Hit rate (% of candidates that exist)
   - Question types found (mcq, qqq, vdx, cor, mqq, sq)
   - Discovery timestamp

3. **Validator Usage**: Completion metrics use discovered counts (required)
4. **Discovery Required**: Validation fails if discovery metadata is missing

### Viewing Discovery Statistics

```bash
# From extractor directory:
./target/release/mksap-extractor discovery-stats
```

Example output:
```
=== MKSAP Discovery Statistics ===

Overall:
  Total Discovered: 1,790 questions
  Total Candidates Tested: ~500,000
  Overall Hit Rate: 0.36%

Per-System Breakdown:
System Discovered      Candidates Hit Rate Types Found
cv         239           41958    0.57%    mcq,qqq,vdx,cor
en         159           41958    0.38%    mcq,qqq,vdx,cor
...
```

### Interpreting Results

- **100%+**: All discovered questions have been extracted (system complete)
- **90-99%**: Nearly complete - missing only a few questions
- **<90%**: Incomplete - extraction still in progress
- **⚠ Over-extracted**: More extracted than discovered (check for data issues)

### Why This Matters

The MKSAP API availability changes over time:
- Questions can be retired (marked as `invalidated`)
- New questions are added (2025 content)
- Historical baselines become stale

With API-driven metrics, the system automatically adapts to real API state without manual updates.

## Next Steps

1. Run validation regularly during extraction
2. Monitor per-system coverage progress
3. Use `list-missing` for targeted retries
4. Review [Troubleshooting Guide](TROUBLESHOOTING.md) if issues found
5. Check [Architecture](archive/phase1/RUST_ARCHITECTURE.md) for technical details
