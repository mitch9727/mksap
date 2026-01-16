# Project TODO - MKSAP Medical Education Pipeline

**Last Updated**: January 16, 2026
**Current Phase**: Phase 2 (Statement Generator) - NLP Model Selection Complete, Ready for Integration Testing
**Source of Truth**: This file is the single source for active and planned project todos
**Completed Work**: Tracked in git history; remove finished tasks from this list

This file tracks outstanding work across the 4-phase pipeline. Completed todos are removed once finished. Reference documents:
- `docs/PHASE_2_STATUS.md` - Current status and implementation details
- `docs/reference/STATEMENT_GENERATOR.md` - Phase 2 CLI and pipeline reference

---

## Completed Work Summary (January 16, 2026)

### ✅ NLP Model Evaluation & Optimization
- **Completed**: Comprehensive evaluation of 6 scispaCy models
- **Models Tested**:
  - Core models: en_core_sci_sm ✅ (selected), en_core_sci_md ❌, en_core_sci_lg ❌
  - Specialized NER: en_ner_bc5cdr_md ❌, en_ner_bionlp13cg_md ❌
  - Other: en_ner_scibert (404 unavailable)
- **Key Decision**: Production model = en_core_sci_sm (13MB, 0.24s/question, 94% entity coverage)
- **System Optimization**: 1,177MB freed by removing non-beneficial models
- **Documentation**: Comprehensive NLP_MODEL_COMPARISON.md created (482 lines)
- **Commits**: 5 commits completed (Jan 15-16)
- **Status**: ✅ Production ready, hybrid pipeline operational with small model

---

## Phase 2: Statement Generator (🔄 ACTIVE)

**Overall**: ~95% foundation complete, NLP integration ready for testing
**Last Updated**: January 16, 2026 (Model selection complete, integration testing ready)

### WEEK 3 - High Priority Tasks (Start Here)

These are the immediate next steps:

#### LLM Integration Evaluation (🎯 Do First) - NEW
- [ ] Run hybrid pipeline on 10-20 sample questions for baseline comparison
- [ ] Selected test questions: Pick 2-3 from each major system (cv, en, gi, dm, etc.)
- [ ] Measure: Negation preservation, entity completeness, unit accuracy
- [ ] Command: `./scripts/python -m src.interface.cli process --question-id <id>`
- [ ] Document: Create comparison report in `statement_generator/artifacts/phase3_evaluation/`
- [ ] Success criteria: Measure improvements vs baseline (71.4% validation pass rate)
- [ ] Decision point: Results determine Phase 4 (default switch) readiness

#### Scale Processing (After evaluation)
- [ ] Process 10-20 questions per day (target: 100 questions by end of week)
- [ ] Start with: System cv (240 questions) using claude-code provider
- [ ] Command: `./scripts/python -m src.interface.cli process --system cv --provider claude-code`
- [ ] Monitor: API costs, processing time, validation pass rate

#### Validation Refinement (🔧 Critical)
- [ ] Review: Procedure ambiguity false positives (clinical characteristics, physical inactivity)
- [ ] Fix: Update `ambiguity_checks.py` to exclude common false positive patterns
- [ ] Test: Run validation on 20+ new questions
- [ ] Target: Reduce false positive rate to <3%

#### Automated Reporting (📊 Infrastructure)
- [ ] Create: `validation_metrics.py` script for daily metrics
- [ ] Track: Pass rate, issue distribution, processing time
- [ ] Output: Daily summary reports to `statement_generator/outputs/reports/`

### Phase 2 - Medium Priority Tasks (Week 3-4)

#### Provider Testing (🧪 Integration)
- [ ] Test: Gemini CLI integration
- [ ] Test: Codex CLI integration
- [ ] Verify: Temperature support, error handling
- [ ] Document: Cost comparison (API vs CLI providers)

#### Performance Optimization (⚡ Efficiency)
- [ ] Investigate: Batch LLM calls (if provider supports)
- [ ] Explore: Parallel processing with rate limiting
- [ ] Cache: Expensive operations
- [ ] Target: <30 seconds per question average

#### Cloze Candidate Debugging (🐛 Quality)
- [ ] Investigate: "not found in statement" errors (special characters, formatting)
- [ ] Fix: Cloze candidate extraction patterns
- [ ] Re-validate: Failed questions
- [ ] Update: Cloze identification patterns

### Phase 2 - Quality & Reliability (Week 4+)

- [ ] Improve provider error classification (retryable vs permanent)
- [ ] Add Phase 2 validation guidance documentation
- [ ] Track processing time per question and provider usage
- [ ] Capture rough cost estimates for paid providers
- [ ] Run full production pass on all 2,198 questions

### Phase 2 - Week 3-7 Detailed Roadmap

**Week 3**: Consistency improvements & scaling
- [ ] Lock temperature settings (Codex CLI or selected provider)
- [ ] Enhance prompts with few-shot examples
- [ ] Implement provider consistency tester
- [ ] Scale to 100 processed questions
- [ ] Target: >90% Jaccard similarity, <30 sec per question

**Week 4-5**: Coverage enhancement
- [ ] Implement coverage analyzer (`coverage_checks.py`)
- [ ] Enhance critique extraction for >90% coverage
- [ ] Test iterative coverage improvement
- [ ] Run coverage validation on 50 questions

**Week 6-7**: Production preparation
- [ ] Run validation suite on all 2,198 questions
- [ ] Generate comprehensive validation report
- [ ] Identify manual review queue
- [ ] Batch fix low-coverage questions
- [ ] Update documentation (3 files)
- [ ] Generate production dataset export

---

## Phase 3: Cloze Application (📋 PLANNED)

**Dependencies**: Phase 2 completion

### Design & Specification
- [ ] Draft Phase 3 design/spec for cloze application
  - Input: Phase 2 JSON files with `true_statements` field
  - Output: JSON with cloze blanks applied
  - Key decision: Multiple cards per statement vs one card with all blanks
  - File: Create `docs/PHASE_3_DESIGN.md`

### Implementation
- [ ] Implement cloze blanking based on `cloze_candidates`
  - Language: Python or Rust (TBD)
  - Algorithm: Generate 2-5 card variants per statement
  - File: Create `statement_generator/src/phase3_cloze.py` or extractor module

### Data Integrity
- [ ] Preserve `extra_field` and link to source data
  - Schema: Add `context` and `source_question_id` fields
  - Ensure clinical context available on card flip

### Testing
- [ ] Add tests for cloze generation edge cases
  - No cloze candidates (skip or allow?)
  - 1 candidate (skip or allow?)
  - 5+ candidates (truncate or include all?)
  - Special characters and formatting

---

## Phase 4: Anki Export (📋 PLANNED)

**Dependencies**: Phase 3 completion

### Tooling Selection
- [ ] Select Anki export tooling (likely `genanki`)
  - Options: genanki (Python), AnkiDroid sync, manual APKG
  - Decision file: `docs/PHASE_4_DESIGN.md`

### Card Schema
- [ ] Define note model and field mapping
  - Front: Statement with cloze blank [...]
  - Back: Answer + context (extra_field)
  - Sources: References + linked figures/tables
  - Card template: HTML/CSS for clinical styling

### Media Integration
- [ ] Include media assets (figures/tables/videos/SVGs)
  - Challenge: Link media from Phase 1 extraction
  - Approach: Embed media IDs, genanki resolves to files
  - Consideration: APKG size limits

### Quality Assurance
- [ ] Validate import into Anki and review card quality
  - Steps: Generate APKG → Import → Spot-check 20 cards → Review media → Test sync
  - Output: `docs/PHASE_4_VALIDATION_REPORT.md`

---

## Tooling and Maintenance (🔧 Infrastructure)

### Documentation
- [ ] Ensure global Claude config supports `/maintain` workflows
  - Location: `~/.claude/` (project no longer uses `.claude/`)
  - Add any required skills/commands there if needed

- [ ] Add automated docs link check to routine workflow
  - Tools: broken-link-checker or similar
  - Scope: Check all internal links in `docs/`
  - Frequency: Pre-commit or weekly
  - File: Create `scripts/check-docs.sh`

### Documentation Updates (Post-Week 2)
- [ ] Update README with Week 2-3 progress
- [ ] Create troubleshooting guide
- [ ] Document common validation issues
- [ ] Write provider selection guide

---

## Success Metrics & Goals

### Week 3 Goals
- [ ] **100 questions processed** (4.5% of total) - currently 7 questions (0.3%)
- [ ] **>75% validation pass rate** - currently 71.4% (5 of 7 questions)
- [ ] **<3% false positive rate** - currently <5% (acceptable, but refining)
- [ ] **<30 seconds per question average** - need benchmarking

### Phase 2 Completion Criteria
- [ ] **Consistency**: >90% statement overlap (Jaccard similarity)
- [ ] **Validation**: <5% false positives, >95% true positives
- [ ] **Coverage**: >90% concept coverage per question
- [ ] **Best Practices**: 100% compliance with 9 core principles
- [ ] **Processing**: All 2,198 questions with <5% extraction failures

### Phase 2-4 Final Goals
- [ ] Phase 2: Complete processing of all 2,198 questions
- [ ] Phase 3: Generate ~6,700 Anki-ready flashcards
- [ ] Phase 4: Export final mksap.apkg ready to import into Anki

---

## Known Issues & Workarounds

### Issue 1: Procedure Ambiguity False Positives (WEEK 3 FIX)
- **Problem**: Medical terms flagged as "procedures" when they're conditions/risk factors
- **Examples**: "physical inactivity", "clinical characteristics"
- **Status**: Identified in Week 2, scheduled for Week 3 fix
- **Workaround**: Manual review of validation warnings
- **Fix**: Update `detect_ambiguous_procedure_clozes()` to exclude false positives

### Issue 2: Cloze Candidate "Not Found" Errors
- **Problem**: Some cloze candidates not found in statement (special characters, formatting)
- **Examples**: ">250 mg/dL", "IL-4"
- **Status**: Identified in Week 2, scheduled for Week 3 investigation
- **Workaround**: Manual review, add hints in extra_field
- **Fix**: Improve cloze candidate extraction patterns

### Issue 3: macOS grep -P Not Supported
- **Problem**: Validation scripts use `grep -P` (not available on macOS)
- **Status**: Identified in Week 2
- **Workaround**: Use Python for parsing
- **Fix**: Rewrite scripts to use Python only

---

## How to Update This File

**Important**: This is your single source of truth for all todos. Keep it updated:

### When Starting Work
1. Find task in this file
2. Check dependencies - is anything blocking this task?
3. Review file links in the task description for context

### When Completing Work
1. Remove the completed task from TODO.md
2. Update "Last Updated" at top
3. Commit: `git commit -m "mark: task completed"`

### When Adding New Work
1. Add task with clear description
2. Link to relevant files: `path/to/file.py:123`
3. Add context in comment if needed
4. Estimate: Is it Day, Week, or Month scale work?
5. Commit: `git commit -m "todo: add new task"`

### Section Organization
- **Current Phase** (Active work) at top
- Keep only active and planned tasks in this file
- **Dependencies** clearly marked for blocked tasks
- **Links** to reference docs for context

---

## Reference Documents

**For detailed context, see**:
- **Phase 2 Status**: `docs/PHASE_2_STATUS.md` (Current implementation details)
- **Best Practices**: `docs/reference/CLOZE_FLASHCARD_BEST_PRACTICES.md`

---

**This file is your master todo list. Update it regularly as you progress through phases.**
