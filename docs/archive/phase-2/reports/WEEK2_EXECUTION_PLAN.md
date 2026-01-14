# Week 2 Validation Framework Implementation Plan

**Status:** Ready for immediate execution ✅ **Last Updated:** 2026-01-04 **Estimated Time:** 2-3 hours total

---

## Executive Summary

All 4 subagents have completed analysis. Root causes identified, solutions designed, ready for parallel implementation.

**Critical Discovery:** Enumeration module already exists - only needs tests.

**Tasks:**
1. Fix table extraction JSON parsing (3 edits to prompt)
2. Create ambiguity detector module + tests (~450 lines)
3. Create enumeration detector tests (~390 lines)
4. Enhance quality checks + create tests (~250 lines)

---

## PHASE 1: Parallel Implementation (Execute First)

### Task 1: Fix Table Extraction JSON Parsing ✅ SOLUTION READY
**Agent ID:** a7f9ab6 **File:** `statement_generator/prompts/table_extraction.md` **Priority:** CRITICAL BLOCKER

**Root Cause:** Claude Code CLI wraps JSON in markdown fences (` ```json ... ``` `), causing
`JSONDecodeError: Expecting value: line 1 column 1`

**Solution - Three edits:**

1. **After line 131** (before JSON example) - Add:
```markdown
OUTPUT FORMAT:

Return ONLY the raw JSON object below. DO NOT wrap it in markdown code fences.
DO NOT include any text before or after the JSON.
```

2. **After line 158** (after JSON example) - Add:
```markdown
CRITICAL: Your response must be ONLY the JSON object above. Do not include:
- Markdown code fences (```json or ```)
- Explanatory text before or after
- Any formatting other than the raw JSON

The first character of your response must be `{` and the last character must be `}`.
```

3. **Replace lines 160-162** with:
```markdown
**Note**: Notice how extra_field is ALWAYS the table caption, providing source context for every statement.

NOW EXTRACT THE FACTS:

Your response must be raw JSON only. Start with `{` and end with `}`. No markdown fences. No explanatory text.
```

---

### Task 2: Create Ambiguity Detector Module ✅ DESIGN COMPLETE
**Agent ID:** a35a122 **Files to Create:**
- `statement_generator/src/validation/ambiguity_checks.py` (~200 lines)
- `statement_generator/tests/test_ambiguity_checks.py` (~250 lines)

**Module Functions (7 total):**
1. `validate_statement_ambiguity()` - Main entry point
2. `detect_ambiguous_medication_clozes()` - Detect medications lacking mechanism/indication/class
3. `detect_overlapping_candidates()` - Find overlapping candidates (e.g., "severe asthma" and "asthma")
4. `detect_ambiguous_organism_clozes()` - Detect organisms without context
5. `detect_ambiguous_procedure_clozes()` - Detect procedures without indication/timing
6. `suggest_hint()` - Recommend parenthetical hints: "(drug)", "(organism)", "(mechanism)"
7. `find_overlapping_pairs()` - Helper for overlap detection

**Pattern Matching:**
- Medication suffixes: -mab, -nib, -statin, -pril, -olol, -sartan, -mycin
- Context requirements: mechanism, drug class, indication, or comparative context
- Organism format: Capitalized genus + lowercase species
- Procedure terms: CT, MRI, colonoscopy, biopsy

**Test Coverage:**
- Week 1 Reslizumab example (critical test case)
- Medication context detection (4 test methods)
- Overlapping candidates (3 test methods)
- Organism/procedure detection (2 test methods each)
- Edge cases (multiple overlaps, case sensitivity)

**Success Criteria:**
- Week 1 Reslizumab example correctly flagged as ambiguous
- Medications with mechanism/indication/class pass
- >80% test coverage

---

### Task 3: Create Enumeration Detector Tests ✅ MODULE EXISTS
**Agent ID:** a6cf8a9 **File to Create:** `statement_generator/tests/test_enumeration_checks.py` (~390 lines)

**IMPORTANT:** Module `enumeration_checks.py` already fully implemented (339 lines) and integrated into validator.py.
Only tests are missing.

**Existing Functions to Test:**
1. `validate_statement_enumerations()` - Main entry point
2. `check_list_statement()` - Detects "includes X, Y, and Z" patterns
3. `check_multi_item_cloze()` - Detects 4+ sequential cloze candidates
4. `check_numeric_enumeration()` - Detects numbered steps/lists
5. `check_comprehensive_coverage_claim()` - Detects "all", "every", "complete list"
6. `count_list_items()` - Helper function
7. `check_candidates_in_sequence()` - Helper function

**Test Structure (8 test classes, 45+ test cases):**
- Helper function tests (10 tests)
- Detection function tests (29 tests)
- Integration tests (5 tests)
- Edge cases (5 tests)

**Examples from Best Practices:**
- ❌ "Beck's triad includes hypotension, JVD, and muffled heart sounds" (should flag)
- ✅ "One component of Beck's triad is muffled heart sounds" (should pass)

---

### Task 4: Enhance Quality Checks ✅ PLAN COMPLETE
**Agent ID:** a646cb4 **Files to Modify/Create:**
- `statement_generator/src/validation/quality_checks.py` (add ~50 lines)
- `statement_generator/tests/test_quality_checks.py` (create ~200 lines)

**Three Enhancements:**

**A. Upgrade Statement Length Check Severity (5 min)**
- Change INFO → WARNING for >200 chars
- Add message: "Long statements slow reviews and reduce retention"

**B. Add Patient-Specific Language Detection (10 min)**
- New function: `check_patient_specific_language()`
- Patterns: "this patient", "this case", "the patient", "in this patient"
- Issue type: `PATIENT_SPECIFIC_LANGUAGE`
- Severity: INFO (recommendation)

**C. Improve Atomicity Detection (15 min)**
- Detect ALL semicolons (compound sentences)
- Detect multiple "and" conjunctions
- Detect multi-clause conditionals
- Better feedback: "semicolon suggests compound sentence"

**Test Coverage (6 test classes, ~20 methods):**
- Atomicity enhancements (5 tests)
- Patient-specific detection (3 tests)
- Length check severity (2 tests)
- Vague language (3 tests)
- Board relevance (3 tests)
- Integration tests (4 tests)

---

## PHASE 2: Integration (After Phase 1 Complete)

**Estimated Time:** 15-20 minutes

**File to Modify:** `statement_generator/src/validation/validator.py`

**Tasks:**
1. Import new ambiguity_checks module:
```python
from .ambiguity_checks import validate_statement_ambiguity
```

2. Add call to `validate_statement_ambiguity()` in appropriate location

3. Aggregate validation issues from all modules

4. Update validation report format for new issue types

---

## PHASE 3: Testing & Validation (After Phase 2 Complete)

**Estimated Time:** 45-60 minutes

### Test 1: Run Validator on 20 Questions
- Select 4 questions per system: cv, en, fc, gi, pm
- Run enhanced validation framework
- Analyze false positive rate (target: <5%)
- Tune thresholds if needed

### Test 2: Verify Table Extraction Fix
- Re-run pmmcq24048 with fixed table_extraction.md
- Verify 10 table statements extracted (no JSON errors)
- Test on 3 additional questions with tables
- Update coverage metrics: 75-95% → 85-95%

---

## PHASE 4: Documentation (After Phase 3 Complete)

**Estimated Time:** 20-30 minutes

**Files to Create/Update:**
1. Create `WEEK2_COMPLETION_REPORT.md`
   - Document all deliverables
   - Update metrics (coverage, validation accuracy, processing time)
   - Identify Week 3 priorities

2. Update `docs/PHASE_2_STATUS.md`
   - Mark Week 2 complete
   - Add validation module inventory

---

## PHASE 5: Handoff (Final Step)

**Estimated Time:** 10 minutes

**File to Create:** `WEEK2_HANDOFF.md`
- Summary of Week 1-2 achievements
- Current state snapshot
- Week 3 task list
- Critical files reference
- Ready-to-execute commands

---

## Execution Strategy

### Step 1: Launch 4 Parallel Subagents
Use Task tool with 4 invocations in ONE message for parallel execution.

### Step 2: Review Subagent Outputs
Wait for all 4 to complete, review deliverables.

### Step 3: Integration
Manually update validator.py with new imports and calls.

### Step 4: Testing
Run validation on 20 questions + table extraction verification.

### Step 5: Documentation
Create completion report and handoff document.

---

## Success Criteria

**Week 2 Complete When:**
1. ✅ Table extraction works with Claude Code CLI (no JSON errors)
2. ✅ Ambiguity detector module implemented and tested
3. ✅ Enumeration detector tests created
4. ✅ Quality checks enhanced
5. ✅ Validator integration complete
6. ✅ Validation testing complete on 20 questions (<5% false positives)
7. ✅ Week 2 documentation complete

---

## Critical Files Reference

**Prompts:**
- `statement_generator/prompts/table_extraction.md` - Needs 3 edits
- `statement_generator/prompts/critique_extraction.md` - Already enhanced Week 1

**Validation Modules:**
- `statement_generator/src/validation/ambiguity_checks.py` - CREATE
- `statement_generator/src/validation/enumeration_checks.py` - EXISTS (339 lines)
- `statement_generator/src/validation/quality_checks.py` - ENHANCE
- `statement_generator/src/validation/validator.py` - INTEGRATE

**Tests:**
- `statement_generator/tests/test_ambiguity_checks.py` - CREATE (~250 lines)
- `statement_generator/tests/test_enumeration_checks.py` - CREATE (~390 lines)
- `statement_generator/tests/test_quality_checks.py` - CREATE (~200 lines)

**Models:**
- `statement_generator/src/models.py` - Reference for Statement, ValidationIssue structures

---

## Risk Mitigation

**Risk 1:** Subagent conflicts **Mitigation:** All work on independent files (no merge conflicts)

**Risk 2:** Table extraction unfixable **Mitigation:** Fallback to Codex CLI for tables only (hybrid approach)

**Risk 3:** Validation false positives >5% **Mitigation:** Threshold tuning in Phase 3

---

## Quick Start Commands

```bash
# From repo root

# After implementation, test table extraction fix:
./scripts/python -m src.main process --question-id pmmcq24048 --force --provider claude-code --log-level INFO

# Run validation on sample:
./scripts/python -m src.main validate --question-id pmmcq24048
```

---

**Next Action:** Begin PHASE 1 - Launch 4 parallel subagents for implementation

---

## PHASE 1A: Subagent Dispatch Packets (Copy/Paste)

Per `~/.claude/skills-internal/create-subagents/SKILL.md`, subagents are black boxes: no AskUserQuestion, no waiting for
user input. Provide all requirements up front and enforce scope/constraints.

### Task Tool Message (single message, 4 invocations)

```text
Global constraints (apply to all tasks):
- NO user interaction; do not use AskUserQuestion or wait for confirmation.
- Limit edits strictly to the stated Scope.
- If blocked, state assumptions and deliver best-effort output.
- Report back with files touched, brief diff summary, and tests run (if any).

Task: table-extraction-fix
Role: Prompt editor
Goal: Apply the three prompt edits described in "Task 1: Fix Table Extraction JSON Parsing".
Scope: statement_generator/prompts/table_extraction.md only.
Definition of done:
- OUTPUT FORMAT block inserted after line 131 (before JSON example)
- CRITICAL block inserted after line 158 (after JSON example)
- Lines 160-162 replaced with the updated Note + raw JSON reminder
Deliverables: Updated prompt file, no other changes.
Report back: file path, brief diff summary, tests run (if any).

Task: ambiguity-detector-module
Role: Validation engineer
Goal: Implement ambiguity detection module and tests per "Task 2: Create Ambiguity Detector Module".
Scope:
- Create statement_generator/src/validation/ambiguity_checks.py
- Create statement_generator/tests/test_ambiguity_checks.py
Key requirements:
- Implement the 7 functions listed in Task 2 with the specified patterns
- Reuse ValidationIssue patterns from existing validation modules
- Include the Reslizumab ambiguity test case
Deliverables: module + tests with coverage across medications, overlaps, organisms, procedures.
Report back: files created, test coverage summary, tests run (if any).

Task: enumeration-detector-tests
Role: Test engineer
Goal: Write tests for existing enumeration_checks.py per "Task 3: Create Enumeration Detector Tests".
Scope: Create statement_generator/tests/test_enumeration_checks.py
Key requirements:
- Test all 7 functions listed in Task 3
- Include best-practice examples (Beck's triad, etc.)
- Cover helper functions, detection functions, integration, and edge cases
Deliverables: full test suite aligned with module behavior.
Report back: file created, test count, tests run (if any).

Task: quality-checks-enhancements
Role: Validation engineer
Goal: Implement quality check enhancements + tests per "Task 4: Enhance Quality Checks".
Scope:
- Update statement_generator/src/validation/quality_checks.py
- Create statement_generator/tests/test_quality_checks.py
Key requirements:
- Length check INFO -> WARNING with new message
- Add patient-specific language detection
- Improve atomicity detection (semicolons, multiple "and", multi-clause conditionals)
Deliverables: updated module + tests for all enhancements and existing checks.
Report back: files updated/created, brief diff summary, tests run (if any).
```
