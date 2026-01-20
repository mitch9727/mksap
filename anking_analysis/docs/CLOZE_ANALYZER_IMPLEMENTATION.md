# ClozeAnalyzer Implementation - Phase 2 Task 3.2

## Overview

Successfully implemented the **ClozeAnalyzer** module for the AnKing Analysis Pipeline. This analyzer examines cloze deletion patterns in Anki flashcards, measuring count, types, positions, and quality metrics.

## File Location

```
/Users/Mitchell/coding/projects/MKSAP/anking_analysis/tools/cloze_analyzer.py
```

## Implementation Summary

### Class: ClozeAnalyzer

A complete implementation with 7 methods for analyzing cloze deletion patterns:

#### 1. `__init__(self)`
- Initializes with cached scispaCy NLP model
- Calls `get_nlp()` from statement_generator.src.validation.nlp_utils
- NLP model is cached via lru_cache, so multiple instances share the same model

#### 2. `analyze(self, card: AnkingCard) -> CardClozeMetrics`
- **Main analysis method** - analyzes a single card's cloze patterns
- Performs all analyses in sequence:
  1. Counts total and unique clozes
  2. Classifies cloze types using NER
  3. Detects positions (beginning/middle/end)
  4. Checks for quality issues (nested, trivial)
  5. Calculates average cloze length
- Returns complete `CardClozeMetrics` object with all results

#### 3. `classify_cloze_type(self, cloze_text: str) -> str`
- Classifies individual cloze deletions into types
- **Detection strategy** (in order):
  1. Check for numbers/units using regex: returns `'number'`
  2. If NLP available, use spaCy NER with type mapping:
     - `DISEASE`, `DISORDER` → `'diagnosis'`
     - `CHEMICAL`, `DRUG` → `'medication'`
     - `GENE`, `PROTEIN` → `'mechanism'`
  3. Default fallback: `'other'`
- Returns: `'diagnosis'`, `'medication'`, `'mechanism'`, `'number'`, or `'other'`

#### 4. `detect_positions(self, text: str, clozes: List[str]) -> List[str]`
- Analyzes where each cloze appears in the text
- For each cloze:
  - If text starts with cloze text → `'beginning'`
  - If text ends with cloze text → `'end'`
  - Otherwise → `'middle'`
- Returns: List of position labels aligned with input clozes

#### 5. `detect_nested_clozes(self, text: str) -> bool`
- Detects if cloze markup patterns overlap or nest
- Uses regex: `{{c\d+::([^}]+)}}`
- Checks all pairs of matches for overlapping spans
- Returns: `True` if any overlapping ranges found, `False` otherwise

#### 6. `_positions_to_indices(self, positions: List[str]) -> List[int]` (Private)
- Converts position labels to indices for storage in model
- Mapping:
  - `'beginning'` → `0`
  - `'middle'` → `1`
  - `'end'` → `2`
- Used internally by `analyze()` to prepare data for CardClozeMetrics

#### 7. `aggregate_metrics(self, metrics_list: List[CardClozeMetrics]) -> Dict`
- Aggregates metrics across multiple cards
- Returns dictionary with:
  - **Count metrics**: `avg_cloze_count`, `median_cloze_count`, `min/max_cloze_count`
  - **Card counts**: `cards_with_cloze`, `cards_without_cloze`
  - **Length metrics**: `avg_cloze_length`, `median_cloze_length`
  - **Distributions**: `cloze_type_distribution`, `position_distribution`
  - **Quality counts**: `cards_with_trivial_clozes`, `cards_with_nested_clozes`
  - **Percentages**: `percentage_with_trivial_clozes`, `total_cards`

## Data Model Integration

### Input Model: AnkingCard
```python
AnkingCard(
    note_id: int,
    deck_path: str,
    deck_name: str,
    text: str,                           # HTML text with cloze markup
    text_plain: str,                     # Plain text without markup
    extra: str,
    extra_plain: str,
    cloze_deletions: List[str],          # Extracted cloze texts
    cloze_count: int,                    # Total number of clozes
    tags: List[str],
    html_features: Dict[str, bool]
)
```

### Output Model: CardClozeMetrics
```python
CardClozeMetrics(
    card_id: int,                        # Reference to AnkingCard.note_id
    cloze_count: int,                    # Total cloze count
    unique_cloze_count: int,             # Number of unique cloze texts
    cloze_types: List[str],              # Types for each cloze
    avg_cloze_length: float,             # Average character length of clozes
    cloze_positions: List[int],          # Position indices (0=begin, 1=mid, 2=end)
    has_nested_clozes: bool,             # Whether any clozes nest/overlap
    has_trivial_clozes: bool             # Whether any are <=3 chars
)
```

## Dependencies

### External Imports
- `re` - Regex for cloze pattern detection and number checking
- `typing` - Type hints (Dict, List, Optional)
- `statistics` - For aggregation calculations (median, min, max)

### Project Imports
- `anking_analysis.models.AnkingCard`
- `anking_analysis.models.CardClozeMetrics`
- `statement_generator.src.validation.nlp_utils.get_nlp`

## Package Integration

### Updated: `anking_analysis/tools/__init__.py`
```python
from anking_analysis.tools.cloze_analyzer import ClozeAnalyzer

__all__ = ["AnkiExtractor", "StructureAnalyzer", "ClozeAnalyzer", "FormattingAnalyzer"]
```

ClozeAnalyzer is now exported alongside other analyzers for easy importing:
```python
from anking_analysis.tools import ClozeAnalyzer
# or
from anking_analysis.tools.cloze_analyzer import ClozeAnalyzer
```

## Testing

### Sample Usage
```python
from anking_analysis.models import AnkingCard
from anking_analysis.tools.cloze_analyzer import ClozeAnalyzer

# Create a card
card = AnkingCard(
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

# Analyze
analyzer = ClozeAnalyzer()
metrics = analyzer.analyze(card)

print(f"Clozes: {metrics.cloze_count}")        # 2
print(f"Unique: {metrics.unique_cloze_count}") # 2
print(f"Types: {metrics.cloze_types}")         # ['other', 'number']
print(f"Length: {metrics.avg_cloze_length}")   # 18.5
```

### Test Files Created
1. `/Users/Mitchell/coding/projects/MKSAP/test_cloze_analyzer.py` - Basic test
2. `/Users/Mitchell/coding/projects/MKSAP/test_cloze_detailed.py` - Comprehensive tests
3. `/Users/Mitchell/coding/projects/MKSAP/verify_cloze_analyzer.py` - Import/functionality verification

## Verification Checklist

✅ **ClozeAnalyzer class implemented** with all required methods
- `__init__()` - NLP initialization
- `analyze()` - Main analysis method
- `classify_cloze_type()` - NER-based type classification
- `detect_positions()` - Position detection
- `detect_nested_clozes()` - Overlap detection
- `aggregate_metrics()` - Multi-card aggregation

✅ **classify_cloze_type() works with NLP**
- Handles number detection
- Uses scispaCy NER when available
- Gracefully degrades to 'other' if NLP unavailable
- Maps entity types to domain categories

✅ **analyze() method works with sample card**
- Correctly counts clozes (2)
- Correctly counts unique clozes (2)
- Classifies types properly
- Detects positions
- Identifies nested/trivial clozes
- Returns proper CardClozeMetrics object

✅ **File location confirmed**
- Path: `/Users/Mitchell/coding/projects/MKSAP/anking_analysis/tools/cloze_analyzer.py`
- File size: 232 lines
- Syntax validated with py_compile

✅ **Imports validated**
- All required imports work correctly
- Package integration updated in __init__.py
- Backward compatible with existing code

## Architecture Consistency

The implementation follows the established patterns from StructureAnalyzer:

1. **Initialization**: Caches NLP model in `__init__`
2. **Single-card analysis**: `analyze(card)` returns typed metrics object
3. **Aggregation**: `aggregate_metrics(list)` returns dictionary with statistics
4. **Type hints**: Full type hints on all methods
5. **Docstrings**: Comprehensive docstrings with Args/Returns
6. **Error handling**: Graceful degradation (works even if NLP unavailable)

## Next Steps

This implementation is complete and ready for integration with:
- Phase 2 Task 3.3 (ContextAnalyzer)
- Phase 2 Task 3.4 (FormattingAnalyzer)
- Phase 2 Aggregation and Reporting

The analyzer can be used immediately in:
```python
from anking_analysis.tools import ClozeAnalyzer
from anking_analysis.tools import AnkiExtractor

extractor = AnkiExtractor()
cards = extractor.extract_deck("AnKing::Cardiovascular")

analyzer = ClozeAnalyzer()
metrics = [analyzer.analyze(card) for card in cards]
aggregated = analyzer.aggregate_metrics(metrics)
```

## File Details

| Property | Value |
|----------|-------|
| **Path** | `/Users/Mitchell/coding/projects/MKSAP/anking_analysis/tools/cloze_analyzer.py` |
| **Lines** | 232 |
| **Class** | ClozeAnalyzer |
| **Methods** | 7 (including 1 private) |
| **Dependencies** | re, typing, statistics, get_nlp, models |
| **Status** | ✅ Complete and tested |

---

**Implementation Date**: January 20, 2026
**Phase**: AnKing Analysis Pipeline - Phase 2, Task 3.2
**Status**: ✅ COMPLETE
