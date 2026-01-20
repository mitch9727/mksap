# Statement Generator Improvement Recommendations

## High Priority Recommendations

### 1. Structure: Add brevity guidelines to LLM prompts and validation

**Finding:** AnKing statements are more concise (18.0 words vs 28.0)

**Current MKSAP Behavior:** MKSAP statements are verbose

**Recommendation:** Add brevity guidelines to LLM prompts and validation

**Files to Modify:**
- `statement_generator/prompts/critique.txt`
- `statement_generator/src/processing/statements/extractors/critique.py`

**Expected Impact:** More readable statements, easier to study

**Effort:** small

**Code Example:**
```python
# Add to prompt: "Keep statements under 20 words when possible"
```

### 2. Cloze: Improve cloze candidate selection algorithm to prioritize ke...

**Finding:** AnKing uses optimal 2-5 cloze deletions per card

**Current MKSAP Behavior:** MKSAP has suboptimal cloze distribution

**Recommendation:** Improve cloze candidate selection algorithm to prioritize key learning points

**Files to Modify:**
- `statement_generator/src/processing/cloze/validators/cloze_checks.py`
- `statement_generator/src/processing/cloze/extractors/cloze_extractor.py`

**Expected Impact:** Better flashcard quality and higher retention

**Effort:** medium

**Code Example:**
```python
# Prioritize cloze selection: diagnosis > mechanism > medication > number
```


## Medium Priority Recommendations


## Low Priority Recommendations

