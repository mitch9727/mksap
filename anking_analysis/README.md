# AnKing Analysis Pipeline

**Comprehensive analysis of 1,000 AnKing flashcards vs 393 MKSAP Phase 3 statements to identify best practices for flashcard design and statement generation.**

---

## 📊 Quick Summary

This analysis extracted and systematically compared AnKing flashcards against MKSAP-generated statements across **4 key dimensions**:

| Dimension | AnKing Pattern | MKSAP Current | Delta | Impact |
|-----------|----------------|---------------|-------|--------|
| **Cloze Selectivity** | 1.8 avg per card | 3.1 avg per statement | -42.7% ✓ | Too many clozes per card overwhelms learners |
| **Context Preservation** | 90% with extra field | 10% with extra field | +827.7% ✓ | Missing clinical reasoning and mechanisms |
| **Atomicity** | 0.98 (single concepts) | 0.99 | -0.9% | MKSAP is already atomic |
| **Formatting** | 98.7% bold usage | 0% | N/A | AnKing emphasizes key terms visually |

**Result**: 3 actionable improvement areas for statement_generator

---

## 📁 Project Structure

```
anking_analysis/
├── README.md                          (this file)
├── run_pipeline.py                    (orchestration script)
├── models.py                          (Pydantic data models - 8 classes)
│
├── reports/                           (MAIN OUTPUT - Start here)
│   ├── ANKING_ANALYSIS.md            (Full metrics from 1,000 cards)
│   ├── MKSAP_VS_ANKING.md            (Comparison tables with deltas)
│   └── IMPROVEMENTS.md                (Executive summary + recommendations)
│
├── DETAILED_IMPROVEMENTS.md          (FOR DEVELOPERS - Technical guide)
├── IMPLEMENTATION_CHECKLIST.md       (FOR DEVELOPERS - File-by-file tasks)
│
├── data/
│   ├── raw/
│   │   └── anking_cards.json         (1,000 extracted cards, 3.1 MB)
│   └── processed/
│       └── anking_metrics.json       (Aggregated analysis metrics)
│
├── tools/                             (Analysis modules)
│   ├── anki_extractor.py             (SQLite extraction from Anki database)
│   ├── structure_analyzer.py         (Text length, complexity, atomicity)
│   ├── cloze_analyzer.py             (Cloze patterns, types, positions)
│   ├── context_analyzer.py           (Clinical context preservation)
│   ├── formatting_analyzer.py        (HTML features, markdown)
│   ├── baseline_comparator.py        (Compare vs MKSAP Phase 3)
│   ├── report_generator.py           (Generate 3 markdown reports)
│   └── __init__.py                   (Package exports)
│
├── tests/                             (Unit & integration tests)
│   ├── test_anki_extractor.py
│   ├── test_cloze_analyzer.py
│   ├── test_formatting_analyzer.py
│   └── verify_cloze_analyzer.py
│
└── docs/                              (Implementation iteration notes)
    ├── INDEX.md
    ├── archive/
        └── phase1/
            └── PHASE1_TASK2_*.md
    ├── ANKI_EXTRACTOR_REFERENCE.md
    └── ... (reference documentation)
```

---

## 🚀 Quick Start

### 1. View Results
Already executed! Results available in:
- `reports/IMPROVEMENTS.md` - High-level findings (5 min read)
- `reports/MKSAP_VS_ANKING.md` - Detailed metrics comparison (10 min read)

### 2. Understand the Data
- `data/raw/anking_cards.json` - 1,000 AnKing flashcards (3.1 MB)
- `data/processed/anking_metrics.json` - Aggregated metrics

### 3. Implement Improvements
- `DETAILED_IMPROVEMENTS.md` - Complete technical guide (30 min read)
- `IMPLEMENTATION_CHECKLIST.md` - Step-by-step tasks (reference doc)

---

## 🎯 Key Findings

### Finding #1: Cloze Selectivity (Priority: HIGH)
**AnKing averages 1.8 clozes per card vs MKSAP's 3.1**

Problem: MKSAP packs multiple test points into single flashcards
- Violates spaced repetition principle (one concept per card)
- Overwhelms learners with too many questions per review
- Results in worse retention

Solution: Modify cloze identification to prioritize ONE primary cloze + optional related ones

**Implementation**: 2-3 hours work in statement_generator/

---

### Finding #2: Context Preservation (Priority: HIGH)
**AnKing includes extra_field (back/explanation) 90% vs MKSAP's 10%**

Problem: MKSAP statements lack clinical reasoning and mechanisms
- Students learn isolated facts without understanding WHY
- Missing pathophysiology, mechanisms, clinical pearls
- Reduces retention and clinical application

Solution: Create ContextEnhancer module to automatically generate context for each statement

**Implementation**: 3-4 hours work in statement_generator/

---

### Finding #3: Trivial Cloze Detection (Priority: MEDIUM)
**Current validation flags legitimate medical terms as "trivial"**

Problem: Terms like "hemochromatosis" or "36°C" flagged for being short
- Medical terms shouldn't be filtered by length
- Clinical thresholds are inherently numeric

Solution: Use NLP entity recognition + medical term whitelist for smarter filtering

**Implementation**: 1-2 hours work in statement_generator/

---

## 📊 Analysis Methodology

### Data Source
- **AnKing**: 1,000 flashcards sampled randomly from 40 AnKing subdecks
  - Includes: Main AnKing, Zanki systems, Lolnotacop, CheesyDorian, etc.
- **MKSAP**: 393 statements from 14 Phase 3 test questions (baseline)

### Dimensions Analyzed
1. **Structure** - Text length, word count, sentence complexity, atomicity
2. **Cloze Patterns** - Count, distribution, types, positions, quality
3. **Context** - Extra field presence, length, clinical reasoning
4. **Formatting** - Bold, italic, lists, tables, markdown compatibility

### Statistical Significance
- Deltas > 20% flagged as "significant" (✓ marker)
- 10 high-impact differences identified

---

## 🔧 For Developers

### Architecture
Each analysis tool is independent and follows same pattern:
```python
class AnalyzerName:
    def analyze(card: AnkingCard) -> Metrics
    def aggregate_metrics(metrics: List[Metrics]) -> Dict
```

All use **Pydantic** for type safety and JSON serialization.

### Reusing Components
- `tools/anki_extractor.py` - Can extract from any Anki database
- `tools/baseline_comparator.py` - Can compare any metrics
- `tools/report_generator.py` - Can generate reports from any analysis

### NLP Integration
- Uses **scispaCy** entity recognition for medical term classification
- Loaded via `statement_generator/src/validation/nlp_utils.py`
- Automatically detects DISEASE, DRUG, SYMPTOM, etc.

### Database Access
- Queries Anki SQLite at: `~/Library/Application Support/Anki2/[Profile]/collection.anki2`
- Parses note field format (field separator: ASCII 31)
- Handles HTML/formatting in front and back

---

## 📈 Metrics Dashboard

### AnKing Baseline (from 1,000 cards):
```
Structure:
- Avg text: 121 chars
- Avg words: 14.9 words
- Atomicity: 0.98 (highly atomic)
- With formatting: 98.7%

Cloze Patterns:
- Avg count: 1.8 per card
- Median: 1.0 (most cards have 1)
- With context: 99.9%
- Trivial: 6.9%

Context:
- With extra field: 89.7%
- Avg length: 161 chars
- Pathophysiology: 11.7%
- Clinical pearls: 4%
```

### MKSAP Current (393 statements):
```
Structure:
- Avg text: 106 chars
- Avg words: 14.4 words
- Atomicity: 0.99

Cloze Patterns:
- Avg count: 3.1 per statement
- Median: 3.0
- Trivial: 1%

Context:
- With extra: 9.7%
- Avg length: 95 chars
```

### Target After Implementation:
```
Structure:
- Avg text: 110-120 chars
- Avg words: 14-15 words
- Atomicity: 0.97+ (stay atomic)

Cloze:
- Avg count: 1.8-2.0 (match AnKing)
- Median: 1.0-2.0
- Trivial: 3-5% (improved filtering)

Context:
- With extra: 80%+ (major improvement)
- Avg length: 140+ chars (major improvement)
```

---

## 🛠️ Implementation Path

### Phase 1: Validation (30-60 min)
- Update cloze count validation thresholds
- Add smarter trivial cloze detection
- Test on Phase 3 questions

### Phase 2: Prompts & Context (2-3 hours)
- Update critique prompt for context extraction
- Create context_enhancer module
- Update cloze_identifier prompt for priority-based selection

### Phase 3: Integration (1-2 hours)
- Integrate context_enhancer into pipeline
- Add atomic extraction guidance
- Update validation rules

### Phase 4: Testing & Tuning (1-2 hours)
- Run on Phase 3 test set
- Collect metrics
- Adjust parameters based on results

### Phase 5: Deployment (1 day)
- Run Phase 4 production batch with improvements
- Monitor quality metrics
- Compare against baseline

**Total Effort**: 4-6 hours active implementation

---

## 📚 Documentation

### For Understanding Results:
1. Start: `reports/IMPROVEMENTS.md` (5 min)
2. Details: `reports/MKSAP_VS_ANKING.md` (10 min)
3. Full: `reports/ANKING_ANALYSIS.md` (15 min)

### For Implementing Changes:
1. Start: `DETAILED_IMPROVEMENTS.md` (30 min, technical overview)
2. Reference: `IMPLEMENTATION_CHECKLIST.md` (step-by-step tasks)
3. Code: Check `statement_generator/` for current structure

### For Understanding the Analysis:
1. Architecture: This README (reference)
2. Components: `tools/*.py` (review docstrings)
3. Data Models: `models.py` (Pydantic schemas)

---

## 🔍 Validation & Testing

### Unit Tests (5 test files)
- `tests/test_anki_extractor.py` - Database connection & extraction
- `tests/test_cloze_analyzer.py` - Cloze detection & classification
- `tests/test_formatting_analyzer.py` - HTML & formatting detection

### Integration Tests
- Full pipeline: `run_pipeline.py` (executes all 4 phases)
- Baseline: 14 Phase 3 MKSAP questions
- Metrics collection & comparison

### Regression Testing
- Validation rules still catch real errors
- LLM response parsing still works
- Data model serialization/deserialization

---

## 🚨 Known Limitations

1. **NLP Model Version**: Uses scispaCy 0.5.4 (trained on spaCy 3.7.4)
   - May have minor compatibility warnings with spaCy 3.8.11
   - Doesn't affect entity recognition accuracy

2. **Anki Database**: Requires Anki to be closed (database lock)
   - SQLite WAL file must be clean
   - Works only with local Anki profile

3. **Sample Size**: 1,000 cards vs 393 statements
   - AnKing sample is larger and more diverse
   - MKSAP baseline is from 14 test questions only
   - Results biased toward AnKing patterns

4. **Context Enhancement**: Manual inspection recommended
   - LLM-generated context should be reviewed
   - Not all clozes may need extensive extra fields

---

## 📝 Next Steps

1. **Review Results**
   - Read `reports/IMPROVEMENTS.md` (executive summary)
   - Review `reports/MKSAP_VS_ANKING.md` (detailed metrics)

2. **Plan Implementation**
   - Review `DETAILED_IMPROVEMENTS.md` (technical details)
   - Create feature branch in statement_generator/

3. **Implement Changes**
   - Follow `IMPLEMENTATION_CHECKLIST.md` (step-by-step)
   - Test on Phase 3 questions as you go
   - Run full test suite

4. **Deploy & Monitor**
   - Merge improvements to main
   - Run Phase 4 production batch
   - Monitor metrics vs baseline

---

## 📞 Questions?

- **What did the analysis find?** → Read `reports/IMPROVEMENTS.md`
- **How do I implement it?** → Read `IMPLEMENTATION_CHECKLIST.md`
- **What's the technical detail?** → Read `DETAILED_IMPROVEMENTS.md`
- **What data was used?** → See `data/` folder
- **How does the pipeline work?** → See `run_pipeline.py` and `tools/*.py`

---

**Generated**: January 20, 2026
**Analysis Period**: Complete pipeline execution
**Status**: ✅ Complete - Ready for implementation
