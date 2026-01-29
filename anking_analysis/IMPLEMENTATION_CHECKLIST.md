# Statement Generator Improvement - File-by-File Implementation Checklist

**Use this checklist to implement AnKing best practices into statement_generator**

Status: Ready for Claude Code / Codex implementation

---

## 1️⃣ PRIORITY 1: Validation Rules (Start Here)

### File: `statement_generator/src/processing/cloze/validators/cloze_checks.py`

**Current State**:
- Line 34-63: `validate_cloze_count()` enforces 2-5 clozes per statement
- Line 176-251: `check_trivial_clozes()` uses overly broad filters

**Changes Required**:

- [ ] **Line 34-63: Update `validate_cloze_count()`**
  - Current: Warns if < 2, flags info if > 5
  - New: Should accept 1-3 as good, only warn at > 3
  - Rationale: AnKing avg is 1.8, MKSAP current is 3.1 (too high)

  ```python
  # BEFORE:
  if count < 2:
      issues.append(ValidationIssue(severity="warning", ...))

  # AFTER:
  if count < 1:
      issues.append(ValidationIssue(severity="error", ...))
  elif count == 1:
      pass  # GOOD: atomic
  elif count <= 3:
      issues.append(ValidationIssue(severity="info", ...))
  elif count > 3:
      issues.append(ValidationIssue(severity="warning", ...))
  ```

- [ ] **Line 176-251: Rewrite `check_trivial_clozes()`**
  - Current: Flags single letters, short words too aggressively
  - New: Use medical context to distinguish valid short terms from true trivial ones
  - Add parameters: `statement_context: Optional[str] = None`
  - Create helper functions:
    - `_is_medical_abbreviation_or_unit(text: str) -> bool`
    - `_is_clinical_threshold(number: str, context: str) -> bool`
  - Rationale: Disease names, drug names, clinical thresholds are valid even if short

  Replace entire function with version from DETAILED_IMPROVEMENTS.md

**Testing**:
- Run validation on Phase 3 test questions
- Before: Should see warnings on many 1-2 cloze statements
- After: Should accept 1-2 cloze statements cleanly

---

## 2️⃣ PRIORITY 2: Context Validation (Quick Win)

### File: `statement_generator/src/validation/validator.py`

**Current State**:
- extra_field is optional, not validated

**Changes Required**:

- [ ] **Add new validation function after existing imports**
  ```python
  def validate_extra_field(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
      """Validate extra_field quality and presence"""
      # See DETAILED_IMPROVEMENTS.md for full implementation
  ```

- [ ] **Integrate into validation pipeline**
  - Find where `validate_statement_structure()` or similar is called
  - Add call to `validate_extra_field(statement, location)`

**Testing**:
- Run validator on Phase 3 statements
- Should flag statements with missing/short extra_field

---

## 3️⃣ PRIORITY 3: Prompt Updates (Medium Effort)

### File: `statement_generator/prompts/critique.txt`

**Current State**:
- Generic statement extraction prompt
- No emphasis on context or atomic facts

**Changes Required**:

- [ ] **Add section: "AnKing-Style Atomic Facts Guidance"**
  - Include GOOD/AVOID examples (see DETAILED_IMPROVEMENTS.md)
  - Explain: one concept per statement

- [ ] **Add section: "Context & Clinical Pearls Requirements"**
  - For each statement, include explanation of:
    1. Why this matters (mechanism/pathophysiology)
    2. Clinical application (how to use in practice)
    3. Memory aids (if available)
  - Include GOOD examples with pathophysiology

**Reference**: See "Context Extraction Section" in DETAILED_IMPROVEMENTS.md

---

### File: `statement_generator/prompts/cloze_identifier.txt`

**Current State**:
- "Identify 2-5 cloze candidates per statement"

**Changes Required**:

- [ ] **Replace "2-5" requirement with priority-based approach**
  - Identify PRIMARY cloze (most important)
  - Identify 0-2 SECONDARY clozes if tightly related
  - Remove generic "identify all testable facts" approach

- [ ] **Add priority guidelines**
  - CRITICAL: Diagnoses, conditions, findings
  - HIGH: Mechanisms, causes, treatments
  - MEDIUM: Numbers, parameters (if clinically critical)
  - LOW: Supporting details, examples

- [ ] **Update output format to include reasoning**
  ```json
  {
    "cloze_mapping": {
      "1": ["primary_candidate", "secondary_if_related"],
      "2": ["single_most_important"]
    },
    "reasoning": {
      "1": "Why this is most important..."
    }
  }
  ```

**Reference**: See "New Prompt Pattern" in DETAILED_IMPROVEMENTS.md

---

## 4️⃣ PRIORITY 4: Context Enhancement Module (New Component)

### File: `statement_generator/src/processing/statements/extractors/context_enhancer.py`

**Current State**:
- Doesn't exist - needs to be created

**Changes Required**:

- [ ] **Create new file** with ContextEnhancer class
  - Methods:
    - `__init__(client, prompt_template_path)`
    - `enhance_statements(statements, original_critique, use_llm)`
    - `_add_nlp_context(statement)` - Use NLP entity extraction
    - `_enhance_with_llm(statement, original_critique)` - Call LLM if needed

- [ ] **NLP Context Detection**
  - Use scispaCy to detect DISEASE, DISORDER, CHEMICAL, DRUG entities
  - Add context hints based on entities found
  - Append to extra_field if not already present

- [ ] **LLM Enhancement (Optional)**
  - If extra_field is thin, call LLM to generate clinical reasoning
  - Prompt: "Given this statement, explain the WHY and HOW"

**Reference**: See "context_enhancer.py" code in DETAILED_IMPROVEMENTS.md

**Dependencies**:
- Requires: `ClaudeClient`, `Statement`, `get_nlp()`
- Check: `statement_generator/src/validation/nlp_utils.py` for NLP loading

---

## 5️⃣ PRIORITY 5: Integrate Context Enhancement into Pipeline

### File: `statement_generator/src/orchestration/pipeline.py`

**Current State**:
- Critique extraction → Cloze identification → Validation

**Changes Required**:

- [ ] **Find the line where critique statements are extracted**
  - Likely: `statements = critique_processor.extract_statements(...)`

- [ ] **Add context enhancement AFTER critique extraction**
  ```python
  # After: statements = critique_processor.extract_statements(...)

  logger.info(f"Enhancing context for {len(statements)} statements...")
  context_enhancer = ContextEnhancer(
      client,
      prompt_path="prompts/context_enhancement.txt"
  )
  statements = context_enhancer.enhance_statements(
      statements,
      original_critique=question_data["critique"],
      use_llm=True
  )
  logger.info(f"Context enhancement complete")
  ```

- [ ] **Ensure proper initialization**
  - Import: `from ...processing.statements.extractors.context_enhancer import ContextEnhancer`
  - Verify client is available

**Testing**:
- Run pipeline on 1 test question
- Check that extra_field is populated and enhanced

---

## 6️⃣ PRIORITY 6: Update Critique Processor for Atomic Extraction

### File: `statement_generator/src/processing/statements/extractors/critique.py`

**Current State**:
- `extract_statements()` is generic, no atomic preference

**Changes Required**:

- [ ] **Add parameter to function signature** (line ~39)
  ```python
  def extract_statements(
      self,
      critique: str,
      educational_objective: str,
      nlp_context: Optional[EnrichedPromptContext] = None,
      prefer_atomic: bool = True,  # ← NEW
  ) -> List[Statement]:
  ```

- [ ] **Add atomic guidance to NLP section** (line ~56-60)
  - When `prefer_atomic=True`, inject AnKing-style guidance into prompt
  - See "Add NLP guidance for atomic extraction" in DETAILED_IMPROVEMENTS.md
  - This guides LLM to extract one-fact-per-statement

**Testing**:
- Run with `prefer_atomic=True` on test question
- Verify statements are simpler, more focused

---

## 7️⃣ PRIORITY 7: Add Cloze Priority Scoring

### File: `statement_generator/src/processing/cloze/identifier.py`

**Current State**:
- Generic LLM extraction, no priority differentiation

**Changes Required**:

- [ ] **Add before class definition** (around line ~10):
  ```python
  from enum import Enum
  from typing import Tuple

  class ClozePriority(Enum):
      CRITICAL = 1
      HIGH = 2
      MEDIUM = 3
      LOW = 4
  ```

- [ ] **Add scoring function** (around line ~80):
  ```python
  def score_cloze_importance(
      candidate: str,
      statement: str,
      is_first_mention: bool,
      nlp_entity_type: Optional[str] = None
  ) -> Tuple[ClozePriority, float]:
      # See DETAILED_IMPROVEMENTS.md for implementation
  ```

- [ ] **Use scoring in `identify_cloze_candidates()`**
  - After parsing LLM response, score each candidate
  - Filter or re-rank based on scores
  - Rationale: Ensures most important facts are selected

**Testing**:
- Run on statement with multiple cloze candidates
- Verify primary candidates are scored highest

---

## 8️⃣ Optional: Prompt Refinement Functions

### File: `statement_generator/src/processing/cloze/identifier.py`

**Purpose**: Helper function to format cloze prompts with medical guidance

- [ ] **Add helper for medical context in cloze prompt**
  ```python
  def _add_medical_guidance_to_cloze_prompt(prompt: str, medical_context: Optional[str]) -> str:
      """Inject medical entity guidance into cloze prompt"""
      if medical_context:
          return prompt + f"\n\nMedical context: {medical_context}"
      return prompt
  ```

**Testing**:
- Optional, only if want tighter control over LLM output

---

## 9️⃣ Metrics & Monitoring

### File: `statement_generator/src/validation/validator.py` (or new file)

**Consider Adding**:

- [ ] **Metrics collection function**
  ```python
  def collect_quality_metrics(statements: List[Statement]) -> Dict:
      """Collect AnKing-aligned metrics"""
      return {
          "avg_cloze_count": np.mean([len(s.cloze_candidates) for s in statements]),
          "pct_with_extra_field": sum(1 for s in statements if s.extra_field) / len(statements),
          "avg_extra_length": np.mean([len(s.extra_field) for s in statements if s.extra_field]),
          ...
      }
  ```

- [ ] **Log metrics after processing**
  - After validation, log metrics
  - Compare against AnKing baseline
  - Track improvements over time

---

## Summary of Changes

### New Files to Create:
1. `statement_generator/src/processing/statements/extractors/context_enhancer.py`

### Files to Modify:
1. `statement_generator/prompts/critique.txt` - Add atomic/context guidance
2. `statement_generator/prompts/cloze_identifier.txt` - Priority-based approach
3. `statement_generator/src/processing/cloze/validators/cloze_checks.py` - Update thresholds
4. `statement_generator/src/processing/cloze/identifier.py` - Add priority scoring
5. `statement_generator/src/processing/statements/extractors/critique.py` - Atomic parameter
6. `statement_generator/src/orchestration/pipeline.py` - Integrate context enhancer
7. `statement_generator/src/validation/validator.py` - Add extra_field validation

### Estimated Effort:
- **Phase 1 (Validation)**: 30-60 min
- **Phase 2 (Context Validation)**: 15-30 min
- **Phase 3 (Prompts)**: 30-45 min
- **Phase 4 (Context Enhancer)**: 60-90 min
- **Phase 5 (Pipeline Integration)**: 30-45 min
- **Phase 6 (Atomic Extraction)**: 15-30 min
- **Phase 7 (Priority Scoring)**: 30-45 min
- **Phase 8 (Testing & Validation)**: 60-90 min
- **Total**: ~4-6 hours for full implementation

---

## Testing Strategy

### Unit Test Locations:
- `statement_generator/tests/processing/`

### Test Coverage:
- [ ] Cloze validation accepts 1-2 clozes (new behavior)
- [ ] Cloze validation flags > 3 as warning (new behavior)
- [ ] Context enhancement adds extra_field when missing
- [ ] Medical terms not flagged as trivial
- [ ] AtomicProcessor splits compound statements
- [ ] Pipeline successfully integrates context enhancement

### Integration Test:
- [ ] Run full pipeline on 5 Phase 3 test questions
- [ ] Compare metrics:
  - avg_cloze_count: Should decrease toward 1.8
  - extra_field %: Should increase toward 80%+
  - avg_extra_length: Should increase toward 160+ chars

### Regression Test:
- [ ] Ensure validation rules still catch real errors
- [ ] Ensure LLM responses still parse correctly
- [ ] Ensure no breaking changes to data models

---

## Rollout Plan

### Step 1: Local Testing (20 min)
- Implement Phase 1-2 (validation)
- Test on 5 Phase 3 questions locally
- Verify no breakage

### Step 2: Feature Branch (2-3 hours)
- Create feature branch: `feature/anking-best-practices`
- Implement Phase 3-5 (prompts, context, pipeline)
- Test on 10 Phase 3 questions
- Run full test suite

### Step 3: Code Review (30-60 min)
- Request review against this checklist
- Verify implementation matches specifications
- Check test coverage

### Step 4: Merge & Deploy (30 min)
- Merge to main branch
- Run Phase 4 production batch
- Monitor metrics

### Step 5: Monitor & Tune (ongoing)
- Collect metrics from Phase 4
- Compare against AnKing baseline
- Adjust thresholds based on real data

---

## Quick Reference: AnKing Baseline Metrics

| Metric | AnKing | MKSAP (Pre) | Target (Post) |
|--------|--------|------------|---------------|
| Avg cloze count | 1.8 | 3.1 | 1.8-2.0 |
| Median cloze | 1.0 | 3.0 | 1.0-2.0 |
| With extra field | 90% | 10% | 80%+ |
| Avg extra length | 161 chars | 95 chars | 140+ chars |
| Trivial cloze % | 6.9% | 1% | 3-5% |
| Atomicity score | 0.98 | 0.99 | 0.97+ |

---

**Ready for implementation! Use the DETAILED_IMPROVEMENTS.md for code snippets and MKSAP Phase 3 baseline metrics as the target.**

