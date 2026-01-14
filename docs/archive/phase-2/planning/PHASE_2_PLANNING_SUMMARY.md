# Phase 2 Planning Summary

## Executive Overview

**Objective**: Improve Phase 2 statement generator for consistency, validation accuracy, and 90%+ concept coverage.

**Primary Focus**: Consistency + Validation + 90% Coverage

**Timeline**: 7-week implementation roadmap (Weeks 1-3: consistency & validation, Weeks 4-5: coverage, Weeks 6-7:
production prep)

**Deliverables**:
- 3 new validation modules (ambiguity, enumeration, coverage)
- Enhanced prompts with completeness guidance
- Provider consistency testing framework
- Full dataset validation (2,198 questions)
- Phase 2 completion report with metrics

---

## User Priorities & Decisions

### Primary Objectives
1. **Consistency** - Minimize variation between runs and across providers
2. **Validation** - Improve quality checks, align with best practices
3. **Coverage** - Extract 90%+ of testable concepts from critique

### Key Architectural Decisions

#### Provider Strategy
- **Selected**: Codex CLI only (single-provider testing)
- **Rationale**:
  - Same underlying model = reduced variation
  - Prompt quality > provider choice for consistency
  - Lower cost (single CLI provider)
  - Test hypothesis: "Does single provider + good prompts = deterministic output?"
- **Temperature**: Baseline 0.1, test range 0.1-0.5 only
- **Note**: If consistency <70%, may need to evaluate provider differences

#### Pipeline Architecture
- **Order**: Critique → Key Points → Tables → Cloze → Normalization (NO CHANGE)
- **Rationale**: Current order is working correctly, no need to modify
- **Design**: Non-destructive JSON updates (adds `true_statements` field only)

#### Statement & Cloze Philosophy
- **Statement Count**: No upper limit (extract ALL testable facts)
- **Cloze Candidates**: No upper limit (more is better, refine later)
- **Coverage Target**: 90%+ concept coverage per question
- **Baseline**: 64% coverage on pmmcq24048 (7/11 concepts)

#### Prompt Enhancements
- **Remove**: Patient-specific details ("this patient", "this case")
- **Remove**: Statement count guidance ("3-7 statements")
- **Add**: "Extract ALL testable facts comprehensively"
- **Add**: Completeness verification checklist
- **Add**: Diverse statement patterns (not limited to examples)
- **Add**: Double-check instruction (review critique twice)

### Successful Completion Criteria

| Metric | Target | Current | Critical For |
|--------|--------|---------|--------------|
| Consistency | >90% overlap (Jaccard similarity) | TBD | Production reliability |
| Validation | <5% false positives, >95% true positives | TBD | Automated quality assurance |
| Coverage | >90% concept coverage | 64% | Learning effectiveness |
| Best Practices | 100% compliance | ~80% (7/9 principles) | Standards alignment |

---

## Analysis & Findings

### Current State (pmmcq24048)

**Existing Output**:
- 7 statements from critique
- 2 statements from key_points
- 0 statements from tables (skipped - lab values)
- Coverage: 64% (7/11 concepts)

**Concept Gap Analysis**:
1. ✅ Tezepelumab definition
2. ✅ Phenotype independence
3. ✅ Severe asthma definition
4. ✅ Severe asthma treatment
5. ✅ Dupilumab efficacy thresholds
6. ✅ Omalizumab mechanism
7. ✅ Azithromycin indication
8. ❌ Biologic phenotype-driven selection (mentioned, not extracted as atomic)
9. ❌ Long-term oral glucocorticoid use
10. ❌ IgE biomarker requirement for omalizumab
11. ❌ Patient-specific application (IgE 18 U/mL, eosinophils 110/μL)

**Root Cause**: Prompt limits extraction to "3-7 statements", missing comprehensive coverage

### Best Practices Compliance

**Current Implementation Status**:

| Principle | Status | Implementation | Gap |
|-----------|--------|----------------|-----|
| Atomic facts | ✅ | `check_atomicity()` | None |
| Cloze efficiency | ✅ | Core design | None |
| Avoid ambiguity | ⚠️ | Prompts only | No validation (NEW: ambiguity_checks.py) |
| Concise questions | ⚠️ | Length check (info level) | Severity too low (NEW: upgrade to warning) |
| Avoid overloaded | ❌ | Not enforced | No list detection (NEW: enumeration_checks.py) |
| Context/imagery | ✅ | `extra_field` | None |
| Multiple angles | ✅ | Cloze deletions + no upper limit | None |
| Source fidelity | ✅ | 30% keyword overlap | None |
| 2-5 cloze candidates | ⚠️ | Enforced as max | Update: remove upper limit |

**Identified Gaps**:
1. No ambiguity detection for overlapping candidates
2. No enumeration detection for lists
3. No comprehensive concept coverage validation
4. Cloze count enforces upper limit (should remove)

### Validation Framework

**Current Modules** (4):
- `structure_checks.py` - JSON validity, required fields
- `quality_checks.py` - Atomicity, vague language, board relevance, length
- `cloze_checks.py` - Count (2-5), existence, uniqueness, trivial detection
- `hallucination_checks.py` - Keyword overlap 30% threshold

**To Implement** (3):
- `ambiguity_checks.py` - Overlapping/ambiguous cloze candidates with hint suggestions
- `enumeration_checks.py` - List detection and chunking recommendations
- `coverage_checks.py` - Medical concept extraction and coverage percentage calculation

---

## Week 1: Baseline Testing & Prompt Enhancement

### Goal
Test current pipeline, enhance prompts for completeness, re-test with metrics.

### Task Sequence

**1. Run Baseline Tests (Codex CLI, temp=0.1, current prompts)**
```bash
# 3 runs with current prompts
./scripts/python -m src.main process --question-id pmmcq24048 --provider codex --temperature 0.1
./scripts/python -m src.main process --question-id pmmcq24048 --provider codex --temperature 0.1
./scripts/python -m src.main process --question-id pmmcq24048 --provider codex --temperature 0.1
```

**Measure**:
- Statement count per run
- Consistency (Jaccard similarity across 3 runs)
- Coverage % (manual analysis)
- Expected: ~64% coverage, ~60-70% consistency

**2. Enhance critique_extraction.md Prompt**
- Remove line ~58: "Extract 3-7 testable medical facts"
- Replace with: "Extract ALL testable medical facts from the critique comprehensively (no upper limit)"
- Remove line ~29: Patient-specific detail instructions
- Add after line 74: ``` **COMPLETENESS VERIFICATION CHECKLIST:** Before finalizing, verify you extracted facts about:
  ✓ Drug mechanisms and targets ✓ Indications and contraindications ✓ Diagnostic thresholds and biomarkers ✓
  Differential diagnoses (from incorrect answer explanations) ✓ Treatment approaches and management steps ✓
  Pathophysiology mechanisms

**STATEMENT PATTERN FLEXIBILITY:** Use any clear, atomic statement structure - not limited to the examples above.
Examples are illustrative, not exhaustive.

**DOUBLE-CHECK:** Review the critique a second time before finalizing. Did you miss any testable facts?
  ```

**3. Re-run with Enhanced Prompt (Codex CLI, temp=0.1)**
```bash
# 3 runs with enhanced prompts
./scripts/python -m src.main process --question-id pmmcq24048 --provider codex --temperature 0.1 ./scripts/python -m
src.main process --question-id pmmcq24048 --provider codex --temperature 0.1 ./scripts/python -m src.main process
--question-id pmmcq24048 --provider codex --temperature 0.1
```

**Measure**:
- Statement count per run
- Coverage % (manual analysis)
- Consistency (Jaccard similarity)
- Compare baseline vs enhanced

**4. Test on 4 Additional Questions**
- Run enhanced prompt on: cvmcq24001, enmcq24001, fcmcq24001, gimcq24001
- Manual coverage analysis on each
- Validate improvement across diverse specialties

### Deliverables
- Baseline metrics (3 runs, current prompts)
- Enhanced critique_extraction.md prompt
- Enhanced metrics (3 runs, new prompts)
- Coverage improvement report (baseline vs enhanced)

### Success Criteria
- Coverage increased to >85% (target: 90%+)
- Consistency >80% (Jaccard similarity)
- Prompt improvements don't reduce consistency

---

## Week 2: Validation Framework Enhancement

### Goal
Improve validation accuracy, align with best practices.

### Task Sequence

**1. Implement Ambiguity Detector**
- File: `statement_generator/src/validation/ambiguity_checks.py`
- Function: `detect_ambiguous_clozes()` - Flag overlapping candidates
- Function: `suggest_hints()` - Recommend "(drug)", "(organism)", "(test)" hints
- Integration: Add to `validate_statement_clozes()`

**2. Implement Enumeration Detector**
- File: `statement_generator/src/validation/enumeration_checks.py`
- Function: `detect_enumerations()` - Pattern matching for lists
- Function: `count_list_items()` - Count enumeration size
- Function: `suggest_chunking_strategy()` - Recommend overlapping chunks
- Integration: Add to `validate_statement_quality()`

**3. Enhance Existing Quality Checks**
- Upgrade statement length severity: info → warning if >200 chars
- Add check for patient-specific language ("this patient", "this case")
- Improve atomicity detection (detect semicolons, compound sentences)

**4. Test & Tune**
- Run validator on 10 existing questions
- Measure false positive rate
- Tune hallucination threshold (test 20%, 30%, 40%)

### Deliverables
- `ambiguity_checks.py` module (complete)
- `enumeration_checks.py` module (complete)
- Enhanced quality checks in `quality_checks.py`
- Validation report on 10-question sample
- False positive analysis and threshold tuning

### Success Criteria
- <5% false positives in 10-question sample
- All best practices principles validated
- Thresholds tuned for accuracy

---

## Week 3: Consistency Improvements

### Goal
Stabilize output, minimize variation between runs.

### Task Sequence

**1. Lock Temperature Settings**
- Document Codex CLI temperature support in config
- Add warnings if provider doesn't support temp=0.0
- Update all prompts to reference locked temperature

**2. Enhance Prompts for Determinism**
- Add to critique_extraction.md: "Be consistent - extract the same facts every time"
- Add to cloze_identification.md: "Prefer objective medical terms"
- Add few-shot examples (3 good + 1 bad) to each prompt

**3. Implement Provider Consistency Tester**
- File: `statement_generator/tests/consistency_test.py`
- CLI command: `./scripts/python -m src.main test-consistency --question-id pmmcq24048 --runs 5`
- Function: `calculate_statement_overlap()` - Jaccard similarity
- Function: `identify_provider_biases()` - Provider-specific patterns
- Report generation: HTML/markdown output

**4. Re-run Consistency Tests**
- 5 runs with improved prompts and locked temperature
- Compare to Week 1 baseline
- Measure improvement in overlap percentage

### Deliverables
- Temperature locking implementation
- Enhanced prompts with few-shot examples
- `consistency_test.py` module (complete)
- Consistency improvement report (baseline vs Week 3)

### Success Criteria
- Consistency >90% (Jaccard similarity)
- Temperature locked and documented
- Provider tester CLI command working

---

## Week 4-5: Coverage Enhancement

### Week 4: Concept Coverage Analyzer

**1. Implement Coverage Analyzer**
- File: `statement_generator/src/validation/coverage_checks.py`
- Function: `extract_medical_concepts()` - NLP-based extraction (drugs, conditions, mechanisms, thresholds)
- Function: `calculate_coverage()` - Percent of concepts in statements
- Function: `identify_missing_concepts()` - Gap analysis
- Integration: Add to `StatementValidator.validate_question()`

**2. Enhance Critique Extraction Prompt**
- Add: "Extract ALL testable facts comprehensively (aim for 90%+ coverage)"
- Add verification checklist (drug mechanisms, contraindications, thresholds, differentials)

**3. Test Coverage Analyzer**
- Test on 10 questions with manual concept annotation
- Measure precision/recall of automated extraction
- Tune concept extraction patterns

### Week 5: Coverage Optimization

**1. Implement Iterative Coverage Improvement**
- If coverage <90%, generate targeted follow-up prompt
- Append supplemental statements to `true_statements`
- Re-validate coverage

**2. Test on 5 Low-Coverage Questions**
- Find questions with <80% coverage
- Apply iterative improvement
- Document final coverage achieved

**3. Run Coverage Validation on 50 Questions**
- Measure coverage distribution
- Identify systematic gaps (missing concept types)
- Adjust prompts based on patterns

### Deliverables
- `coverage_checks.py` module (complete)
- Concept coverage validation report (50 questions)
- Iterative improvement strategy documented

### Success Criteria
- >90% coverage on pmmcq24048
- Systematic gaps identified and addressed
- Scalable strategy for 2,198 questions

---

## Week 6-7: Production Preparation

### Week 6: Full Dataset Validation

**1. Run Validation Suite on 2,198 Questions**
- Structure checks
- Quality checks
- Cloze checks
- Hallucination checks
- Coverage checks

**2. Generate Comprehensive Report**
- Per-system statistics (cv, en, fc, etc.)
- Error distribution by severity
- Coverage distribution histogram
- Top 10 most common issues

**3. Identify Manual Review Queue**
- Coverage <70% (critical gaps)
- Multiple validation errors
- Hallucination warnings
- Ambiguous cloze candidates

**4. Batch Fixing**
- Re-process low-coverage questions
- Fix hallucination warnings
- Tune validation thresholds

### Week 7: Documentation & Handoff

**1. Update Documentation**
- [docs/PHASE_2_STATUS.md](../../../PHASE_2_STATUS.md) - Final statistics
- [docs/reference/STATEMENT_GENERATOR.md](../../../reference/STATEMENT_GENERATOR.md) - New modules
- [docs/archive/phase-2/reports/WEEK2_COMPLETION_REPORT.md](../reports/WEEK2_COMPLETION_REPORT.md) - Results

**2. Generate Production Dataset**
- Export validated `true_statements` for all 2,198 questions
- Flag questions with warnings
- Create backup before Phase 3

**3. Phase 3 Readiness**
- Verify all statements ready for cloze application
- Document any known limitations
- Prepare handoff documentation

### Deliverables
- Full validation report (2,198 questions)
- Manual review queue with fixes
- Updated documentation (3 files)
- Production dataset export
- Phase 3 readiness sign-off

### Success Criteria
- <5% error rate across dataset
- >90% coverage on 90%+ of questions
- Documentation complete and accurate

---

## New Validation Modules (Detailed Specs)

### Module 1: coverage_checks.py
**Functions**:
- `extract_medical_concepts(critique: str) -> Set[str]`
- `calculate_coverage(statements: List[Statement], concepts: Set[str]) -> float`
- `identify_missing_concepts(critique: str, statements: List[Statement]) -> List[str]`
- `validate_concept_coverage(question_data: Dict, threshold: float = 0.9) -> List[ValidationIssue]`

**Integration**: Add to `StatementValidator.validate_question()`

### Module 2: ambiguity_checks.py
**Functions**:
- `detect_ambiguous_clozes(statement: Statement) -> List[ValidationIssue]`
- `suggest_hints(candidate: str, statement: str) -> Optional[str]`
- `detect_overlapping_candidates(candidates: List[str]) -> List[Tuple[str, str]]`

**Integration**: Add to `validate_statement_clozes()`

### Module 3: enumeration_checks.py
**Functions**:
- `detect_enumerations(statement: str) -> Optional[ValidationIssue]`
- `count_list_items(statement: str) -> int`
- `suggest_chunking_strategy(items: List[str]) -> str`

**Integration**: Add to `validate_statement_quality()`

---

## Implementation Approach

### Sequential Processing Only
- One question at a time (LLM-bound, simpler error handling)
- Avoids rate limits, reduces memory usage
- Checkpoint every 10 questions

### Non-Destructive Updates
- Adds `true_statements` field only
- Preserves all original Phase 1 data
- Allows re-running Phase 2 without re-extraction

### Temperature Consistency
- Baseline: 0.1 (minimizes hallucination)
- Test range: 0.1-0.5 only
- Locked in configuration
- Document provider support

### Evidence-Based Design
- Follows CLOZE_FLASHCARD_BEST_PRACTICES.md
- Atomic facts (one concept per statement)
- Anti-hallucination constraints
- Modifier splitting for clinical importance
- 2-5 cloze candidates (no upper limit)

---

## Risk Assessment

### High Risk
- **LLM Stochasticity**: Variation even at temp=0.1
  - Mitigation: Lock temp, test single provider, measure Jaccard similarity
- **Incomplete Coverage**: Missing 30-40% of concepts hurts learning
  - Mitigation: Implement coverage validator, iterative improvement

### Medium Risk
- **Provider Inconsistency**: Different providers extract different statements
  - Mitigation: Focus on single provider + prompts, test hypothesis
- **Validation False Positives**: Too many incorrect issue flags
  - Mitigation: Tune thresholds, manual review, measure accuracy

### Low Risk
- **Performance**: Processing 2,198 questions takes time
  - Mitigation: Sequential processing is acceptable for Phase 2
- **Cost**: API costs for provider testing
  - Mitigation: Use Codex CLI (single CLI provider, lower cost)

---

## Success Metrics

### PRIMARY

**Consistency**
- Target: >90% statement overlap (Jaccard similarity)
- Baseline: TBD (Week 1)
- Measurement: 3-run overlap analysis
- Critical for: Production reliability

**Validation**
- Target: <5% false positives, >95% true positives
- Baseline: TBD (Week 2)
- Measurement: Manual review of 10-question sample
- Critical for: Automated quality assurance

**Coverage**
- Target: >90% concept coverage per question
- Baseline: 64% (pmmcq24048)
- Measurement: Automated concept extraction + matching
- Critical for: Learning effectiveness

### SECONDARY

**Best Practices Compliance**
- Target: 100% alignment with best practices
- Current: ~80% (7/9 principles)
- Measurement: Validation checklist
- Goal: Week 2 (add ambiguity + enumeration detection)

**Processing Efficiency**
- Target: <30 seconds per question (all 5 phases)
- Baseline: TBD (need benchmarking)
- Note: Not critical for Phase 2, important for Phase 3

---

## Files to Modify/Create

### Critical Paths

**Modify** (Prompt Enhancement):
- `statement_generator/prompts/critique_extraction.md` - Remove limits, add checklist, add pattern flexibility

**Create** (Validation Modules):
- `statement_generator/src/validation/ambiguity_checks.py`
- `statement_generator/src/validation/enumeration_checks.py`
- `statement_generator/src/validation/coverage_checks.py`

**Modify** (Integration):
- `statement_generator/src/validation/validator.py` - Integrate new checks
- `statement_generator/src/validation/quality_checks.py` - Enhance existing checks
- `statement_generator/src/validation/cloze_checks.py` - Update count check, add ambiguity integration

**Create** (Testing):
- `statement_generator/tests/consistency_test.py` - Provider consistency tester

**Modify** (CLI):
- `statement_generator/src/main.py` - Add `test-consistency` command

**Create** (Documentation):
- `docs/PHASE_2_PLANNING_SUMMARY.md` (THIS FILE)
- `docs/PHASE_2_COMPLETION_REPORT.md` (Week 7)

---

## Next Steps

### Immediate (After This Document)
1. Review this summary with user
2. Begin Week 1 baseline testing (Codex CLI, temp=0.1, current prompts)
3. Enhance critique_extraction.md prompt
4. Run Week 1 enhanced testing
5. Measure baseline vs enhanced metrics

### Upon Week 1 Completion
- Evaluate coverage improvement (target: >85%)
- Evaluate consistency (target: >80%)
- Decide if Week 2 validation enhancements are needed
- Proceed to Week 2 implementation

### Upon Completion of Phase 2
- Generate PHASE_2_COMPLETION_REPORT.md with metrics
- Prepare hand-off to Phase 3 (Cloze Application)
- Archive planning documents

---

## Reference Documents

- **Full Plan**: `/Users/Mitchell/.claude/plans/giggly-finding-quilt.md`
- **Best Practices**: `docs/reference/CLOZE_FLASHCARD_BEST_PRACTICES.md`
- **Current Status**: `docs/PHASE_2_STATUS.md`
- **Architecture**: `docs/reference/STATEMENT_GENERATOR.md`

---

**Status**: Planning complete - ready for Week 1 implementation
**Created**: 2026-01-03
**Based on User Decisions**:
- Provider (Codex CLI only)
- Coverage (90%+)
- Pipeline (no change)
- Temperature (0.1 baseline, 0.1-0.5 range)
