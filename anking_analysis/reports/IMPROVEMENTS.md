# Statement Generator Improvement Recommendations

**⚠️ IMPORTANT: Detailed implementation guides available:**
- **[DETAILED_IMPROVEMENTS.md](../DETAILED_IMPROVEMENTS.md)** - Complete technical analysis with code examples
- **[IMPLEMENTATION_CHECKLIST.md](../IMPLEMENTATION_CHECKLIST.md)** - File-by-file implementation guide

---

## Executive Summary

Analysis of 1,000 AnKing cards vs 393 MKSAP Phase 3 test statements reveals **3 critical differences** where AnKing significantly outperforms MKSAP:

| Finding | AnKing | MKSAP | Delta | Priority |
|---------|--------|-------|-------|----------|
| Cloze selectivity | 1.8 avg | 3.1 avg | -42.7% ✓ | HIGH |
| Context preservation | 90% with extra | 10% with extra | +827.7% ✓ | HIGH |
| Trivial cloze quality | 6.9% | 1% | N/A | MEDIUM |

---

## HIGH PRIORITY RECOMMENDATIONS

### 1. ⭐ Reduce Cloze Count (Target: 1.8 per statement)

**The Issue**: MKSAP averages 3.1 clozes per statement vs AnKing's 1.8
- MKSAP extracts every testable fact into separate clozes
- Results in cluttered flashcards with multiple learning points
- Violates spaced repetition principle: one concept per card

**The Fix**:
1. Update validation to accept 1-3 clozes as normal (currently requires 2-5)
2. Modify cloze identification prompt to prioritize PRIMARY cloze
3. Only include secondary clozes if tightly related

**Impact**: Better flashcard quality, improved retention

**Effort**: 4-6 hours for full implementation

**Start Here**: `IMPLEMENTATION_CHECKLIST.md` → Priority 1 & 3

**Files to Modify**:
- `statement_generator/prompts/cloze_identifier.txt` - Priority-based selection
- `statement_generator/src/processing/cloze/validators/cloze_checks.py` - Update thresholds
- `statement_generator/src/processing/cloze/identifier.py` - Add priority scoring

---

### 2. ⭐ Enhance Context Preservation (Target: 80%+ with extra field)

**The Issue**: Only 10% of MKSAP statements include extra_field vs AnKing's 90%
- MKSAP extracts facts without clinical reasoning
- Missing pathophysiology, mechanisms, clinical pearls
- Students learn isolated facts, not connected concepts

**The Fix**:
1. Create ContextEnhancer module (new component)
2. Enhance critique prompt to request context for each statement
3. Use NLP entity detection to add relevant context
4. Optionally use LLM to generate clinical reasoning

**Impact**: Better clinical understanding, improved retention

**Effort**: 4-6 hours for full implementation

**Start Here**: `IMPLEMENTATION_CHECKLIST.md` → Priority 2, 4, 5

**Files to Modify**:
- `statement_generator/prompts/critique.txt` - Add context requirements
- `statement_generator/src/processing/statements/extractors/context_enhancer.py` - CREATE NEW
- `statement_generator/src/orchestration/pipeline.py` - Integrate new module
- `statement_generator/src/validation/validator.py` - Add extra_field validation

---

## MEDIUM PRIORITY RECOMMENDATIONS

### 3. Improve Trivial Cloze Detection

**The Issue**: Current validation flags legitimate medical terms as "trivial"
- Disease names like "hemochromatosis" flagged for being short
- Clinical thresholds like "36°C" flagged for being numeric
- Over-filtering prevents good clozes from being included

**The Fix**:
1. Use NLP entity type to distinguish medical terms from grammar
2. Create whitelist of medical abbreviations and common terms
3. Context-aware evaluation of numeric values

**Impact**: Fewer false-positive warnings, better cloze quality

**Effort**: 2-3 hours

**Start Here**: `DETAILED_IMPROVEMENTS.md` → FINDING #3

---

## IMPLEMENTATION ROADMAP

### Week 1: Foundation
- [ ] Update validation rules (Priority 1)
- [ ] Add context validation (Priority 2)
- [ ] Test on 5 Phase 3 questions

### Week 2: Features
- [ ] Create context enhancer module
- [ ] Update prompts (cloze & critique)
- [ ] Integrate into pipeline

### Week 3: Tuning
- [ ] Run on Phase 3 test set
- [ ] Collect metrics
- [ ] Adjust thresholds

### Week 4: Deployment
- [ ] Run Phase 4 production batch
- [ ] Monitor quality metrics
- [ ] Compare against AnKing baseline

---

## Target Metrics (After Implementation)

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Avg cloze count | 3.1 | ? | 1.8-2.0 |
| Statements with extra_field | 10% | ? | 80%+ |
| Avg extra_field length | 95 chars | ? | 140+ chars |
| Trivial cloze % | 1% | ? | 3-5% |

---

## Documentation

**For Implementation Details**: See `DETAILED_IMPROVEMENTS.md`
- Complete technical analysis
- Code snippets for each change
- Rationale behind each decision
- Before/after examples

**For Step-by-Step Checklist**: See `IMPLEMENTATION_CHECKLIST.md`
- File-by-file modification guide
- Checkboxes for tracking progress
- Testing strategy
- Rollout plan

---

## Questions?

These recommendations are based on systematic analysis of 1,000 AnKing cards vs 393 MKSAP statements across 4 dimensions:
- Statement structure (length, complexity, atomicity)
- Cloze patterns (count, distribution, quality)
- Context preservation (extra field usage, types)
- Formatting (HTML features, markdown compatibility)

See `/anking_analysis/reports/MKSAP_VS_ANKING.md` for detailed comparison metrics.

