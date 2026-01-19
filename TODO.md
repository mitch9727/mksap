# Project TODO - MKSAP Medical Education Pipeline

**Last Updated**: January 16, 2026
**Current Phase**: Phase 3 Complete (92.9% validation pass rate) - Ready for Phase 4 Production Deployment
**Source of Truth**: This file is the single source for active and planned project todos
**Completed Work**: Tracked in git history; remove finished tasks from this list

This file tracks outstanding work across the 4-phase pipeline. Completed todos are removed once finished. Reference documents:
- `docs/PHASE_2_STATUS.md` - Current status and implementation details
- `docs/reference/STATEMENT_GENERATOR.md` - Phase 2 CLI and pipeline reference

---

## Completed Work Summary (January 16, 2026)

### ✅ Phase 3: Hybrid Pipeline Validation (Complete)
- **Completed**: January 16, 2026
- **Features Implemented**:
  - Validation framework with 6 quality checks (structure, quality, ambiguity, hallucination, enumeration, cloze)
  - NLP metadata persistence (entities, sentences, negations)
  - Configuration fixes (PROJECT_ROOT path, NLP model loading, environment variables)
- **Results**:
  - Validation pass rate: **92.9%** (13/14 test questions)
  - Negation preservation: **100%**
  - Entity completeness: **100%**
  - Unit accuracy: **100%**
  - Processing success: **100%** (14/14 questions, 0 failures)
- **Improvement**: +21.5 percentage points over baseline (71.4% → 92.9%)
- **Documentation**:
  - `docs/PHASE_3_STATUS.md` - Status document
  - `statement_generator/artifacts/phase3_evaluation/PHASE3_COMPLETE_FINAL_REPORT.md` - Final report
  - `docs/plans/PHASE4_DEPLOYMENT_PLAN.md` - Phase 4 plan
  - `whats-next.md` - Decision guide
- **Status**: ✅ **READY FOR PHASE 4**

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

## Phase 4: Production Deployment (📋 READY TO EXECUTE)

**Overall**: Phase 3 complete (92.9% validation pass rate), ready for scaled deployment
**Last Updated**: January 16, 2026 (Phase 3 complete, Phase 4 planning done)

### Phase 4 - Immediate Priority (Decision Required)

**Decision Point**: Choose deployment approach

#### Option A: Staged Rollout (Recommended ⭐)
- [ ] **Stage 1**: Process 50 questions, evaluate (1-2 hours)
  - Command: `./scripts/python -m src.interface.cli process --mode production --data-root mksap_data`
  - Stop after ~50 questions processed
  - Generate evaluation report using phase3_evaluator.py
  - Decision gate: Pass rate ≥90% → proceed to Stage 2
- [ ] **Stage 2**: Process 500 questions, monitor (5-6 hours)
  - Continue processing (auto-skips already processed)
  - Monitor validation pass rate every 100 questions
  - Decision gate: Pass rate ≥90%, <5 failures → proceed to Stage 3
- [ ] **Stage 3**: Process all 2,198 questions (20-24 hours)
  - Complete full dataset processing
  - Monitor continuously, check progress hourly
  - Expected outcome: 90%+ validation pass rate maintained

#### Option B: Full Deployment (Higher Risk)
- [ ] Process all 2,198 questions immediately
  - Command: `./scripts/python -m src.interface.cli process --mode production`
  - Optional: Enable parallelization (MKSAP_CONCURRENCY=5 in .env)
  - Monitor validation pass rate every 100 questions
  - Expected time: 20-24 hours (or 4-6 hours with parallelization)

### Phase 4 - Quality Assurance & Monitoring

#### Automated Monitoring
- [ ] Create validation rate monitoring script (check every 100 questions)
- [ ] Set up processing failure tracking
- [ ] Implement random spot checks (3 questions per 100 processed)
- [ ] Track processing time and memory usage

#### Post-Processing (After Phase 4 Completion)
- [ ] Generate final evaluation report for all 2,198 questions
- [ ] Calculate final metrics (validation pass rate, statements per question, by-system breakdown)
- [ ] Create Phase 4 completion report
- [ ] Update documentation (mark Phase 4 complete)

### Phase 4 - Optional Optimizations

#### Performance Optimization (⚡ Optional)
- [ ] Enable parallelization (MKSAP_CONCURRENCY=5 in .env) after Stage 1 validation
- [ ] Monitor memory usage with concurrent processing
- [ ] Track LLM provider rate limits
- [ ] Optimize for <30 seconds per question average

---

## Phase 5: Cloze Application (📋 PLANNED)

**Dependencies**: Phase 4 completion (all 2,198 questions processed)

### Design & Specification
- [ ] Draft Phase 5 design/spec for cloze application
  - Input: Phase 4 JSON files with `true_statements` and `validation_pass` fields
  - Output: JSON with cloze blanks applied
  - Key decision: Multiple cards per statement vs one card with all blanks
  - File: Create `docs/PHASE_5_DESIGN.md`

### Implementation
- [ ] Implement cloze blanking based on `cloze_candidates`
  - Language: Python or Rust (TBD)
  - Algorithm: Generate 2-5 card variants per statement
  - File: Create `statement_generator/src/phase5_cloze.py` or extractor module

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

## Phase 6: Anki Export (📋 PLANNED)

**Dependencies**: Phase 5 completion

### Tooling Selection
- [ ] Select Anki export tooling (likely `genanki`)
  - Options: genanki (Python), AnkiDroid sync, manual APKG
  - Decision file: `docs/PHASE_6_DESIGN.md`

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
  - Output: `docs/PHASE_6_VALIDATION_REPORT.md`

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

### Phase 4 Success Criteria (Must Meet)
- [ ] **Validation pass rate ≥85%** across full dataset (target: 90%+)
- [ ] **Processing failure rate <2%** (max 44 failed questions, target: <0.5%)
- [ ] **All 2,198 questions processed**

### Phase 4 Target Goals (Excellent Result)
- [ ] Validation pass rate ≥90% (matching Phase 3 results)
- [ ] Processing failure rate <0.5% (max 11 failed questions)
- [ ] Average processing time <60s per question

### Red Flags (Investigate Immediately)
- [ ] Validation pass rate drops below 80%
- [ ] Processing failures >5% (>110 questions)
- [ ] Systematic patterns in failures (all from one system, one question type)

### Phase 4-6 Final Goals
- [ ] Phase 4: Complete processing of all 2,198 questions (90%+ validation pass rate)
- [ ] Phase 5: Generate ~6,700 Anki-ready flashcards with cloze formatting
- [ ] Phase 6: Export final mksap.apkg ready to import into Anki

---

## Known Issues & Workarounds

### ✅ Resolved Issues

**Issue 1: PROJECT_ROOT Path Misconfiguration** (Resolved Jan 16)
- Fixed in Phase 3: Updated PROJECT_ROOT to correct level (5 parent directories)

**Issue 2: NLP Model Loading Failure** (Resolved Jan 16)
- Fixed in Phase 3: Added path resolution logic for relative paths

**Issue 3: Python Version Mismatch** (Resolved Jan 16)
- Fixed in Phase 3: Updated MKSAP_PYTHON_VERSION to 3.13.5

### Active Issues

**Issue 1: One Validation Failure in Phase 3** (Low Priority)
- **Question**: dmmcq24032 (Diabetes/Metabolic MCQ)
- **Status**: Isolated failure (1/14), does not indicate systematic problem
- **Action**: Monitor for similar patterns in Phase 4, investigate if pattern emerges

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
- **Phase 2 Status**: `docs/PHASE_2_STATUS.md` (Implementation complete)
- **Phase 3 Status**: `docs/PHASE_3_STATUS.md` (Validation complete, 92.9% pass rate)
- **Phase 3 Final Report**: `statement_generator/artifacts/phase3_evaluation/PHASE3_COMPLETE_FINAL_REPORT.md`
- **Phase 4 Deployment Plan**: `docs/plans/PHASE4_DEPLOYMENT_PLAN.md` (Production deployment strategy)
- **What's Next**: `whats-next.md` (Decision guide for Phase 4)
- **Best Practices**: `docs/reference/CLOZE_FLASHCARD_BEST_PRACTICES.md`

---

**This file is your master todo list. Update it regularly as you progress through phases.**
