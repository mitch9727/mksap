# NLP Metadata Persistence Implementation

**Date**: January 16, 2026
**Status**: Complete
**Purpose**: Enable evaluation framework to measure hybrid pipeline improvements

## Overview

Modified the statement generation pipeline to persist NLP analysis metadata to JSON files. This allows the Phase 3 evaluation framework to measure metrics like entity extraction accuracy, negation detection, and atomicity analysis.

## Changes Made

### 1. Modified Files

#### `/Users/Mitchell/coding/projects/MKSAP/statement_generator/src/orchestration/pipeline.py`

**Added 3 new methods:**

1. **`_extract_nlp_metadata()`** (lines 290-337)
   - Extracts NLP metadata from critique and keypoints contexts
   - Returns dict with structure for both critique and key_points sections
   - Handles None contexts gracefully (for hybrid mode disabled)

2. **`_serialize_nlp_artifacts()`** (lines 339-392)
   - Converts Pydantic NLPArtifacts models to JSON-serializable dicts
   - Extracts key fields: entities, sentences, negations
   - Includes summary counts for quick reference

3. **`_get_empty_nlp_section()`** (lines 394-407)
   - Returns empty structure matching serialization format
   - Used when NLP data is unavailable

**Modified `process_question()` method:**

- Line 108: Added `nlp_analysis = None` initialization
- Lines 114-116: Extract NLP metadata after preprocessing completes
- Lines 192-194: Add `nlp_analysis` field to augmented_data before writing

**Updated module docstring:**

- Added documentation for `nlp_analysis` output structure
- Clarified that hybrid mode now persists metadata

### 2. Created Test File

**`/Users/Mitchell/coding/projects/MKSAP/statement_generator/tests/test_nlp_serialization.py`**

Comprehensive test suite verifying:
- NLP artifacts serialize correctly to JSON
- Metadata extraction works with both contexts populated
- Empty sections are generated when NLP is disabled
- All data is JSON-serializable (no Pydantic model leaks)

All 3 tests pass:
```
✓ test_serialize_nlp_artifacts
✓ test_extract_nlp_metadata_both_contexts
✓ test_extract_nlp_metadata_none_contexts
```

### 3. Created Example Output

**`/Users/Mitchell/coding/projects/MKSAP/statement_generator/tests/example_nlp_output.json`**

Shows the exact structure of the `nlp_analysis` field for reference.

## Output Structure

When hybrid mode is enabled (`USE_HYBRID_PIPELINE=true`), the pipeline adds an `nlp_analysis` field to each question JSON:

```json
{
  "question_id": "cvmcq24001",
  "... other fields ...": "...",
  "nlp_analysis": {
    "critique": {
      "entities": [
        {
          "text": "pneumonia",
          "entity_type": "DISEASE",
          "is_negated": false,
          "negation_trigger": null,
          "modifiers": [],
          "sentence_index": 0,
          "spacy_label": "DISEASE"
        }
      ],
      "sentences": [
        {
          "text": "Patient has severe pneumonia without fever.",
          "index": 0,
          "has_negation": true,
          "verb_count": 1,
          "is_complex": false,
          "entity_count": 2
        }
      ],
      "negations": [
        {
          "trigger": "without",
          "start_char": 29,
          "end_char": 36
        }
      ],
      "entity_count": 2,
      "sentence_count": 1,
      "negation_count": 1
    },
    "key_points": {
      "entities": [],
      "sentences": [],
      "negations": [],
      "entity_count": 0,
      "sentence_count": 0,
      "negation_count": 0
    }
  }
}
```

## Key Features

1. **Non-intrusive**: Only adds data when hybrid mode is enabled
2. **Backward compatible**: Existing JSON files without `nlp_analysis` continue to work
3. **Complete metadata**: Captures all NLP preprocessing outputs
4. **JSON-safe**: All Pydantic models converted to primitive types
5. **Evaluation-ready**: Structure designed for metric calculation

## Usage

### Running Pipeline with NLP Persistence

```bash
# Enable hybrid mode
export MKSAP_USE_HYBRID_PIPELINE=true
export MKSAP_NLP_MODEL=statement_generator/models/en_core_sci_sm

# Run pipeline
./scripts/python -m src.interface.cli process --question-id cvmcq24001
```

The output JSON will now include the `nlp_analysis` field.

### Accessing NLP Data in Evaluation

```python
import json

# Load processed question
with open("mksap_data/cv/cvmcq24001.json") as f:
    data = json.load(f)

# Access NLP metadata
if "nlp_analysis" in data:
    critique_entities = data["nlp_analysis"]["critique"]["entities"]
    negated_count = data["nlp_analysis"]["critique"]["negation_count"]

    # Measure metrics
    for entity in critique_entities:
        if entity["is_negated"]:
            print(f"Negated: {entity['text']} (trigger: {entity['negation_trigger']})")
```

## Testing

Run the test suite:

```bash
./scripts/python -m pytest statement_generator/tests/test_nlp_serialization.py -v
```

Or standalone:

```bash
./scripts/python statement_generator/tests/test_nlp_serialization.py
```

## Edge Cases Handled

1. **Hybrid mode disabled**: `nlp_analysis` field is not added to JSON
2. **NLP preprocessing fails**: Empty sections returned (not None)
3. **Empty text fields**: Empty entity/sentence lists returned
4. **Partial data**: Critique may have data while key_points is empty (or vice versa)

## Next Steps

This implementation enables the Phase 3 evaluation framework to:

1. **Measure entity extraction accuracy**: Compare NLP entities to LLM-extracted statements
2. **Validate negation detection**: Ensure negated entities don't become positive statements
3. **Analyze atomicity recommendations**: Check if LLM follows split recommendations
4. **Track improvement metrics**: Compare hybrid vs legacy pipeline outputs

## Files Modified

- `/Users/Mitchell/coding/projects/MKSAP/statement_generator/src/orchestration/pipeline.py` (updated)

## Files Created

- `/Users/Mitchell/coding/projects/MKSAP/statement_generator/tests/test_nlp_serialization.py` (new)
- `/Users/Mitchell/coding/projects/MKSAP/statement_generator/tests/example_nlp_output.json` (new)
- `/Users/Mitchell/coding/projects/MKSAP/statement_generator/NLP_PERSISTENCE_IMPLEMENTATION.md` (this file)

## Verification

Run syntax check:
```bash
./scripts/python -m py_compile statement_generator/src/orchestration/pipeline.py
```

Run tests:
```bash
./scripts/python -m pytest statement_generator/tests/test_nlp_serialization.py -v
```

Both should pass without errors.
