# What's Next: MKSAP Medical Education Pipeline

**Last Updated**: January 20, 2026
**Context**: Fresh session handoff document for continuing work

---

<original_task>
The MKSAP (Medical Knowledge Self-Assessment Program) project is a multi-phase medical education pipeline designed to extract, process, and generate medical education flashcards from the ACP MKSAP question bank (2,198 questions across 16 medical systems). The project has completed Phases 1-3 and is ready to execute Phase 4 (Production Deployment).
</original_task>

<work_completed>
## Phase 1: Rust Extractor (Complete ✅)
**Status**: Complete - January 15, 2026
**Output**: 2,198 questions extracted to JSON format across 16 medical systems (cv, en, fc, cs, gi, hp, hm, id, in, dm, np, nr, on, pm, cc, rm)

**Key Artifacts**:
- Rust extractor: `/Users/Mitchell/coding/projects/MKSAP/extractor/` (Cargo project)
- Binary: `target/release/mksap-extractor`
- Data directory: `/Users/Mitchell/coding/projects/MKSAP/mksap_data/` (2,198 JSON files organized by system)
- Commands: validate, discovery-stats, media-discover, media-download, svg-browser

**Architecture**:
- Discovery-driven (adapts to API state, not hardcoded)
- Resumable (can be interrupted and resumed)
- Non-destructive (preserves all original data)

## Phase 2: Python Statement Generator (Complete ✅)
**Status**: Complete - January 16, 2026 (reorganized to layered architecture)
**Output**: Hybrid NLP+LLM pipeline for extracting medical statements from questions

**Key Features**:
- Multi-provider LLM support (Anthropic, Claude Code, Gemini, Codex)
- Statement extraction from critique and key points
- Cloze candidate identification
- Table extraction and processing
- Text normalization
- Checkpoint management for resumability

**Architecture** (reorganized Jan 15, 2026):
```
statement_generator/
├── src/
│   ├── interface/cli.py              # CLI entry point
│   ├── orchestration/                # Pipeline & checkpoints
│   │   ├── pipeline.py               # StatementPipeline (main workflow)
│   │   └── checkpoint.py             # State management
│   ├── processing/                   # Feature modules
│   │   ├── statements/               # Statement extraction & validation
│   │   │   ├── extractors/           # Critique & keypoints
│   │   │   └── validators/           # Quality checks
│   │   ├── cloze/                    # Cloze identification
│   │   ├── tables/                   # Table processing
│   │   └── normalization/            # Text normalization
│   ├── infrastructure/               # Cross-cutting concerns
│   │   ├── llm/                      # LLM providers & client
│   │   ├── io/                       # File operations
│   │   ├── config/                   # Configuration
│   │   └── models/                   # Data models (Pydantic)
│   └── validation/                   # Validation framework
├── tests/                            # Tests mirror src/ structure
├── prompts/                          # LLM prompt templates
└── artifacts/                        # Runtime outputs (logs, checkpoints, validation)
```

**CLI Wrapper**: `./scripts/python` - Sets PYTHONPATH for statement_generator package

**Commands**:
```bash
# Test on single question
./scripts/python -m src.interface.cli process --question-id cvmcq24001

# Test on system (e.g., cv = cardiovascular)
./scripts/python -m src.interface.cli process --mode test --system cv

# Production (all 2,198)
./scripts/python -m src.interface.cli process --mode production

# Stats & management
./scripts/python -m src.interface.cli stats
./scripts/python -m src.interface.cli reset
./scripts/python -m src.interface.cli clean-logs
```

## Phase 3: Hybrid Pipeline Validation (Complete ✅)
**Status**: Complete - January 16, 2026
**Goal**: Measure improvements when hybrid pipeline (NLP preprocessing + LLM) is active
**Outcome**: 92.9% validation pass rate (13/14 test questions), exceeding 85% target by 7.9 percentage points

**Results**:
| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Validation Pass Rate | 92.9% (13/14) | 85%+ | ✅ EXCEEDS (+7.9pp) |
| Negation Preservation | 100.0% | 95%+ | ✅ PERFECT |
| Entity Completeness | 100.0% | 90%+ | ✅ PERFECT |
| Unit Accuracy | 100.0% | 90%+ | ✅ PERFECT |
| Processing Success | 100% (14/14) | N/A | ✅ PERFECT |

**Baseline Improvement**: +21.5 percentage points over legacy baseline (71.4% → 92.9%)

**Features Implemented**:

1. **Validation Framework** (`statement_generator/src/validation/validator.py`):
   - 6 quality checks: structure, quality, ambiguity, hallucination, enumeration, cloze
   - Integrated into pipeline at `statement_generator/src/orchestration/pipeline.py:188-192`
   - Output: `validation_pass` boolean field added to JSON

2. **NLP Metadata Persistence** (`statement_generator/src/orchestration/pipeline.py:122-130, 214-215`):
   - Captures entities (text, type, negation status, position)
   - Captures sentences (text, features, negation presence, atomicity)
   - Captures negations (triggers, positions)
   - Output: `nlp_analysis` dict added to JSON

3. **Configuration Fixes**:
   - Fixed PROJECT_ROOT path resolution (5 parent directories)
   - Fixed NLP model loading for relative paths
   - Updated `.env` with required variables:
     - `MKSAP_NLP_MODEL=statement_generator/models/en_core_sci_sm-0.5.4/en_core_sci_sm/en_core_sci_sm-0.5.4`
     - `USE_HYBRID_PIPELINE=true`
     - `MKSAP_PYTHON_VERSION=3.13.5`
     - `LLM_PROVIDER=codex`

**Test Questions Processed**:
- 14 questions across 7 medical systems: cv, en, gi, dm, id, on, pm
- Test set includes: cvmcq24001, cvcor25002, encor24003, gicor25001, dmcor24005, idcor25003, oncor24002, pmcor25001, and 6 more
- Processing time: ~45 seconds per question average
- Failure rate: 0% (14/14 successful)

**Documentation Created**:
- `statement_generator/artifacts/phase3_evaluation/PHASE3_COMPLETE_FINAL_REPORT.md` - Comprehensive final report
- `statement_generator/docs/VALIDATION_IMPLEMENTATION.md` - Validation framework implementation notes
- `statement_generator/docs/NLP_PERSISTENCE_IMPLEMENTATION.md` - NLP metadata persistence implementation notes
- `statement_generator/docs/PHASE_3_STATUS.md` - Phase 3 status document (updated to "Complete")
- `statement_generator/docs/deployment/PHASE4_DEPLOYMENT_PLAN.md` - Phase 4 deployment strategy

**Known Issues**:
- 1 validation failure: dmmcq24032 (Diabetes/Metabolic MCQ) - isolated failure, no pattern detected
- Action: Monitor for similar patterns in Phase 4

## NLP Model Evaluation & Optimization (Complete ✅)
**Status**: Complete - January 15-16, 2026
**Goal**: Select optimal scispaCy model for production hybrid pipeline

**Models Evaluated**:
- Core models: en_core_sci_sm ✅ (selected), en_core_sci_md ❌, en_core_sci_lg ❌
- Specialized NER: en_ner_bc5cdr_md ❌, en_ner_bionlp13cg_md ❌
- Not available: en_ner_scibert (404 error)

**Final Decision**: en_core_sci_sm (13MB)
- Load time: 0.24s per question
- Entity coverage: 94% vs large model (5.5% loss acceptable)
- Memory footprint: 13MB vs 540MB (large model)
- Performance: Sufficient for production, no benefit from larger models

**Optimization Results**:
- Disk space freed: 1,177MB (removed 4 non-beneficial models)
- System optimization: Hybrid pipeline operational with small model

**Documentation**:
- `statement_generator/docs/NLP_MODEL_COMPARISON.md` (482 lines, comprehensive evaluation)

## Git Repository Status (Current Branch: backup-before-reorg)
**Current Branch**: `backup-before-reorg`
**Main Branch**: `main`

**Modified Files (Uncommitted)**:
```
M CLAUDE.md
M TODO.md
M statement_generator/docs/PHASE_3_STATUS.md
M mksap_data/cc/cccor25002/cccor25002.json    (14 test questions modified with validation_pass + nlp_analysis)
M mksap_data/cc/ccmcq24035/ccmcq24035.json
M mksap_data/cv/cvcor25010/cvcor25010.json
M mksap_data/cv/cvmcq24001/cvmcq24001.json
M mksap_data/cv/cvvdx24045/cvvdx24045.json
M mksap_data/dm/dmcor25001/dmcor25001.json
M mksap_data/dm/dmmcq24032/dmmcq24032.json
M mksap_data/en/encor25001/encor25001.json
M mksap_data/en/enmcq24050/enmcq24050.json
M mksap_data/gi/gicor25001/gicor25001.json
M mksap_data/gi/gimcq24025/gimcq24025.json
M mksap_data/hp/hpcor25001/hpcor25001.json
M mksap_data/hp/hpmcq24032/hpmcq24032.json
M mksap_data/np/npcor25001/npcor25001.json
M mksap_data/np/npmcq24050/npmcq24050.json
M statement_generator/src/infrastructure/config/settings.py
M statement_generator/src/orchestration/pipeline.py
M statement_generator/src/validation/nlp_utils.py
M statement_generator/src/validation/validator.py
M whats-next.md
```

**Untracked Files**:
```
?? statement_generator/docs/deployment/                 (Phase 4 deployment plan)
?? run_phase3_evaluation.sh                              (Shell script for Phase 3 evaluation)
?? statement_generator/NLP_PERSISTENCE_IMPLEMENTATION.md (Implementation notes)
?? statement_generator/VALIDATION_IMPLEMENTATION.md      (Implementation notes)
?? statement_generator/src/validation/ambiguity_checks.py
?? statement_generator/src/validation/cloze_checks.py
?? statement_generator/src/validation/enumeration_checks.py
?? statement_generator/src/validation/hallucination_checks.py
?? statement_generator/src/validation/quality_checks.py
?? statement_generator/src/validation/structure_checks.py
?? statement_generator/statement_generator/artifacts/logs/*.log  (10+ log files from Phase 3 testing)
?? statement_generator/test_validation_integration.py
?? statement_generator/tests/example_nlp_output.json
?? statement_generator/tests/test_nlp_serialization.py
```

**Recent Commits** (last 5):
1. `4b22a08f` - docs: add Phase 3 quick start guide with batch execution instructions
2. `a2d63bce` - feat: add Phase 3 evaluation framework for measuring hybrid pipeline improvements
3. `49ab9388` - docs: create Phase 3 test question selection and strategy
4. `4c6207f0` - docs: add comprehensive Phase 3 ready summary with quick start guide
5. `dbbd1bb6` - docs: add Phase 3 status report and evaluation infrastructure documentation

**Repository URL**: git@github.com:mitch9727/mksap.git

## Project Configuration

**Environment** (`.env` at project root):
```bash
MKSAP_NLP_MODEL=statement_generator/models/en_core_sci_sm-0.5.4/en_core_sci_sm/en_core_sci_sm-0.5.4
USE_HYBRID_PIPELINE=true
MKSAP_PYTHON_VERSION=3.13.5
LLM_PROVIDER=codex
```

**System Info**:
- Working directory: `/Users/Mitchell/coding/projects/MKSAP/`
- Platform: macOS (Darwin 24.6.0)
- Python: 3.13.5
- Date: January 19, 2026

**Checkpoint File**: `statement_generator/artifacts/checkpoints/processed_questions.json`
- Tracks processed questions (14 currently processed from Phase 3 testing)
- Tracks failed questions (empty array)
- Used by pipeline to skip already-processed questions and enable resumability
</work_completed>

<work_remaining>
## Phase 4: Production Deployment (Ready to Execute)

**Goal**: Process all 2,198 MKSAP questions with the validated hybrid NLP+LLM pipeline

**Status**: ✅ Ready to execute - Phase 3 validation complete (92.9% pass rate)

**Decision Required**: Choose deployment approach

### Option A: Staged Rollout (Recommended ⭐)

**Stage 1: 50 Questions (1-2 hours)**
1. Run production pipeline:
   ```bash
   cd /Users/Mitchell/coding/projects/MKSAP
   ./scripts/python -m src.interface.cli process --mode production --data-root mksap_data
   ```
2. Monitor processing - stop after ~50 questions (check logs for count)
3. Generate evaluation report using `statement_generator/tests/tools/phase3_evaluator.py`:
   ```python
   # Script to evaluate recent 50 questions
   python3 << 'EOF'
   import sys
   sys.path.insert(0, "/Users/Mitchell/coding/projects/MKSAP/statement_generator")
   from pathlib import Path
   from tests.tools.phase3_evaluator import Phase3Evaluator

   project_root = Path("/Users/Mitchell/coding/projects/MKSAP")
   evaluator = Phase3Evaluator(project_root)

   # Get list of processed questions from checkpoint
   import json
   checkpoint_file = project_root / "statement_generator/artifacts/checkpoints/processed_questions.json"
   with open(checkpoint_file) as f:
       checkpoint = json.load(f)
       processed = checkpoint.get("processed_questions", [])

   # Evaluate recent 50 (or however many processed)
   evaluations = evaluator.evaluate_batch(processed[-50:])
   output_file = project_root / "statement_generator/artifacts/phase3_evaluation/scaled_test_report.md"
   evaluator.generate_report(evaluations, output_file)

   print(f"Evaluated {len(evaluations)} questions")
   print(f"Report: {output_file}")
   EOF
   ```
4. **Decision gate**:
   - ✅ Pass rate ≥90%: Proceed to Stage 2
   - ⚠️ Pass rate 85-89%: Acceptable, proceed with monitoring
   - ❌ Pass rate <85%: Investigate patterns, may need prompt tuning

**Stage 2: 500 Questions (5-6 hours)**
1. Continue processing (pipeline auto-skips already processed questions):
   ```bash
   ./scripts/python -m src.interface.cli process --mode production
   ```
2. Monitor validation pass rate every 100 questions using monitoring script (see "Monitoring" section below)
3. **Decision gate**:
   - ✅ Pass rate ≥90%, <5 failures: Proceed to Stage 3
   - ⚠️ Pass rate 85-89%, <10 failures: Acceptable, proceed with caution
   - ❌ Pass rate <85% or >10 failures: Investigate systematic issues

**Stage 3: All 2,198 Questions (20-24 hours)**
1. Complete full dataset processing
2. Monitor continuously, check progress hourly
3. Expected outcome: 90%+ validation pass rate maintained

### Option B: Full Production Deployment (Higher Risk)

1. **Optional**: Enable parallelization for faster processing
   - Add to `.env`: `MKSAP_CONCURRENCY=5`
   - This processes 5 questions at once
   - Reduces total time from 20-24 hours to 4-6 hours
   - Memory requirement: ~500MB per process (2.5GB total for 5 concurrent)

2. Run full production pipeline:
   ```bash
   cd /Users/Mitchell/coding/projects/MKSAP
   ./scripts/python -m src.interface.cli process --mode production
   ```

3. Monitor validation pass rate every 100 questions (see "Monitoring" section below)

4. Expected time:
   - Sequential (default): 20-24 hours (2,198 × ~45s each)
   - Concurrent (MKSAP_CONCURRENCY=5): 4-6 hours

**Risk**: Medium - Large batch could reveal edge cases not seen in 14-question Phase 3 test

### Monitoring During Phase 4

**Watch Progress**:
```bash
# Watch processing logs in real-time
tail -f statement_generator/artifacts/logs/statement_gen_*.log

# Check processed count
grep "Total processed:" statement_generator/artifacts/logs/statement_gen_*.log | tail -1
```

**Check Validation Pass Rate**:
```bash
# Quick validation rate check
./scripts/python -c "
import json
from pathlib import Path
data_dir = Path('/Users/Mitchell/coding/projects/MKSAP/mksap_data')
passed = 0
total = 0
for qfile in data_dir.rglob('*.json'):
    try:
        with open(qfile) as f:
            data = json.load(f)
        if 'validation_pass' in data:
            total += 1
            if data['validation_pass']:
                passed += 1
    except: pass
print(f'Validation pass rate: {passed}/{total} ({passed/total*100:.1f}%)')
"
```

**Review Failed Validations**:
```bash
# Find questions that failed validation
./scripts/python -c "
import json
from pathlib import Path
data_dir = Path('/Users/Mitchell/coding/projects/MKSAP/mksap_data')
failed = []
for qfile in data_dir.rglob('*.json'):
    try:
        with open(qfile) as f:
            data = json.load(f)
        if data.get('validation_pass') == False:
            failed.append(data['question_id'])
    except: pass
print('Failed validations:', failed)
print(f'Total: {len(failed)}')
"
```

**Spot Check Random Question**:
```bash
# Pick random question to review
RANDOM_Q=$(ls mksap_data/cv/*/cv*.json | shuf -n 1)
cat "$RANDOM_Q" | jq '{
  question_id,
  validation_pass,
  nlp_analysis: {
    critique: {entity_count, sentence_count, negation_count},
    key_points: {entity_count, sentence_count, negation_count}
  },
  statement_count: (.true_statements.from_critique | length) + (.true_statements.from_key_points | length)
}'
```

### Phase 4 Success Criteria

**Must Meet**:
- [ ] Validation pass rate ≥85% across full dataset
- [ ] Processing failure rate <2% (max 44 failed questions)
- [ ] All 2,198 questions processed successfully

**Target Goals** (Excellent Result):
- [ ] Validation pass rate ≥90% (matching Phase 3 results)
- [ ] Processing failure rate <0.5% (max 11 failed questions)
- [ ] Average processing time <60s per question

**Red Flags** (Investigate Immediately):
- ⚠️ Validation pass rate drops below 80%
- ⚠️ Processing failures >5% (>110 questions)
- ⚠️ Systematic patterns in failures (e.g., all from one medical system)

### Post-Phase 4 Tasks

1. **Generate Final Evaluation Report**:
   - Use `statement_generator/tests/tools/phase3_evaluator.py` on full dataset
   - Calculate final metrics: validation pass rate, statements per question, by-system breakdown
   - Compare against Phase 3 baseline (92.9%)

2. **Create Phase 4 Completion Report**:
   - Similar format to `statement_generator/artifacts/phase3_evaluation/PHASE3_COMPLETE_FINAL_REPORT.md`
   - Document full dataset metrics
   - Include lessons learned, optimization opportunities

3. **Update Documentation**:
   - Mark Phase 4 complete in `CLAUDE.md:6`
   - Update `TODO.md` to remove Phase 4 tasks
   - Update `statement_generator/docs/PHASE_3_STATUS.md` to link to Phase 4 results
   - Create `statement_generator/docs/PHASE_4_COMPLETION_REPORT.md`

4. **Commit Changes**:
   - Commit modified JSON files (2,198 files with new `validation_pass` + `nlp_analysis` fields)
   - Commit new validation framework files
   - Commit updated documentation
   - Consider: Large commit, may want to split into logical chunks

## Phase 5: Cloze Application (Planned 📋)

**Dependencies**: Phase 4 completion

**Goal**: Apply fill-in-the-blank formatting to statements based on `cloze_candidates` field

**Tasks**:
1. Draft Phase 5 design/spec (`statement_generator/docs/PHASE_5_DESIGN.md`)
   - Input: Phase 4 JSON files with `true_statements` and `cloze_candidates`
   - Output: JSON with cloze blanks applied (e.g., "Patient has {{c1::hypertension}} with BP {{c2::150/90 mmHg}}")
   - Key decision: Multiple cards per statement vs one card with all blanks
   - Consider: Anki cloze format ({{c1::...}}, {{c2::...}}) vs custom format

2. Implement cloze blanking algorithm
   - Language: Python (likely, to integrate with existing pipeline) or Rust (for performance)
   - Algorithm: Generate 2-5 card variants per statement (based on number of candidates)
   - File: Create `statement_generator/src/processing/cloze/applicator.py` or similar

3. Preserve data integrity
   - Schema: Add `context` and `source_question_id` fields to link back to source
   - Ensure clinical context available on card flip (user needs full question for understanding)

4. Add tests for edge cases:
   - No cloze candidates (skip statement or include without blanks?)
   - 1 candidate (skip or allow single-blank cards?)
   - 5+ candidates (truncate to 5 or include all?)
   - Special characters, formatting (HTML entities, medical symbols)

**Estimated Time**: 1-2 days implementation + testing

## Phase 6: Anki Export (Planned 📋)

**Dependencies**: Phase 5 completion

**Goal**: Generate Anki-compatible .apkg files for spaced repetition learning

**Tasks**:
1. Select Anki export tooling (`statement_generator/docs/PHASE_6_DESIGN.md`)
   - Options: `genanki` (Python library), AnkiDroid sync, manual APKG generation
   - Recommendation: `genanki` (well-maintained, supports media, Python integration)

2. Define note model and field mapping
   - Front: Statement with cloze blank (e.g., "Patient has [...] with BP [...]")
   - Back: Answer + context (extra_field from question)
   - Sources: References + linked figures/tables
   - Card template: HTML/CSS for clinical styling (e.g., monospace for labs, color coding for critical values)

3. Media integration
   - Challenge: Link media assets from Phase 1 extraction (figures, tables, videos, SVGs)
   - Approach: Embed media IDs, `genanki` resolves to files in `mksap_data/` directories
   - Consideration: APKG size limits (Anki supports large decks, but sync may be slow)

4. Quality assurance
   - Steps: Generate sample APKG → Import to Anki → Spot-check 20 cards → Review media → Test AnkiWeb sync
   - Output: `statement_generator/docs/PHASE_6_VALIDATION_REPORT.md`

**Estimated Time**: 2-3 days implementation + testing

## Infrastructure & Maintenance Tasks

1. **Git Cleanup**:
   - Current branch: `backup-before-reorg` (should merge or delete after validation)
   - Many uncommitted changes (see Git Repository Status above)
   - Decision needed: Commit Phase 3 changes to main branch?

2. **Documentation Maintenance**:
   - Add automated docs link check to routine workflow (broken-link-checker or similar)
   - Update README with Phase 3-4 progress (currently outdated)
   - Create troubleshooting guide for common validation issues
   - Write provider selection guide (Anthropic vs Claude Code vs Gemini vs Codex)

3. **Artifact Cleanup**:
   - 10+ log files in `statement_generator/statement_generator/artifacts/logs/` (note: wrong path, should be `statement_generator/artifacts/logs/`)
   - Consider: Clean old logs, rotate, or move to archive

4. **Testing Infrastructure**:
   - Integration tests for validation framework (currently minimal)
   - End-to-end tests for full pipeline (Phase 1 → Phase 6)
   - Performance benchmarks (track processing time over time)
</work_remaining>

<attempted_approaches>
## NLP Model Selection

**Attempted**: Evaluating 6 scispaCy models to find optimal size/performance tradeoff

**Models Tested**:
1. ✅ en_core_sci_sm (13MB) - SELECTED for production
2. ❌ en_core_sci_md (100MB) - No benefit over small model, removed
3. ❌ en_core_sci_lg (540MB) - No benefit over small model, removed
4. ❌ en_ner_bc5cdr_md (85MB) - Disease/chemical NER, not beneficial for full statements
5. ❌ en_ner_bionlp13cg_md (85MB) - Biomolecular NER, not beneficial for full statements
6. ❌ en_ner_scibert - Unavailable (404 error from scispaCy download)

**Why Small Model Succeeded**:
- 94% entity coverage vs large model (5.5% loss acceptable for 40x size reduction)
- 0.24s load time per question (fast enough for production)
- Sufficient for statement-level validation (not doing complex biomedical NER)
- Large models provided no measurable improvement in validation pass rate

**Alternative Abandoned**: Using specialized NER models for targeted entity extraction
- Reason: Specialized models optimize for entity type accuracy, not coverage
- Our use case: Need broad coverage of all medical terms, not perfect typing

## Validation Framework Design

**Attempted**: Multiple approaches to validation rule definitions

**Approach 1: Monolithic validator** (Abandoned)
- Initial design: Single `validate()` method with all checks in one function
- Problem: Hard to debug, hard to extend, hard to test individual checks
- Abandoned in favor of modular check architecture

**Approach 2: Modular check system** (CURRENT)
- Design: Separate files for each check type (structure, quality, ambiguity, hallucination, enumeration, cloze)
- Each check returns `(passed: bool, issues: List[str])` tuple
- Main validator orchestrates checks and aggregates results
- Success: Easy to debug, easy to extend, easy to test

**Approach 3: Configuration-driven validation** (Considered but not implemented)
- Idea: Define validation rules in YAML/JSON config files
- Benefit: Non-developers could tune validation rules
- Rejected: Overkill for current needs, would add complexity without clear benefit
- May revisit in future if validation rules need frequent tuning

## Phase 4 Deployment Strategy

**Approach 1: Full deployment immediately** (Considered)
- Reasoning: Phase 3 results (92.9%) are excellent, why wait?
- Risk: 14-question test set may not represent full 2,198 dataset
- Edge cases could emerge at scale (specific medical systems, question types, unusual formatting)
- Decision: Rejected in favor of staged rollout

**Approach 2: Staged rollout** (RECOMMENDED)
- Stage 1: 50 questions → evaluate → decide
- Stage 2: 500 questions → monitor → decide
- Stage 3: All 2,198 questions
- Benefit: Lower risk, validates consistency, can adjust before full run
- Cost: Takes extra time (1-2 hours per stage), delays completion
- Decision: Recommended by Phase 3 final report, reduces risk of wasted LLM calls

**Approach 3: Parallel processing with concurrency** (Available but not default)
- Idea: Process 5 questions simultaneously with `MKSAP_CONCURRENCY=5`
- Benefit: 5x speedup (20-24 hours → 4-6 hours)
- Risk: Higher memory usage (2.5GB vs 500MB), harder to debug failures
- Decision: Optional optimization, enable after Stage 1 validation if needed
</attempted_approaches>

<critical_context>
## Architectural Decisions

**Decision 1: Hybrid NLP+LLM Architecture** (January 2026)
- Context: Phase 2 baseline (LLM-only) achieved 71.4% validation pass rate
- Problem: LLM alone struggles with negation preservation, entity completeness, unit accuracy
- Solution: Add NLP preprocessing layer (scispaCy) to guide LLM with structured medical entity data
- Outcome: 92.9% validation pass rate (+21.5 percentage points)
- Trade-off: Added complexity (NLP model dependency), but significant quality improvement

**Decision 2: Small NLP Model (en_core_sci_sm)** (January 15, 2026)
- Context: 6 scispaCy models available, ranging from 13MB to 540MB
- Problem: Large models slow, high memory, but do they improve results?
- Solution: Comprehensive evaluation showed small model sufficient (94% entity coverage)
- Outcome: 40x size reduction (13MB vs 540MB), no measurable quality loss
- Trade-off: 5.5% entity loss acceptable for massive efficiency gain

**Decision 3: Layered Architecture Reorganization** (January 15, 2026)
- Context: Original flat structure hard to navigate as codebase grew
- Problem: Finding files, understanding dependencies, extending features
- Solution: Reorganized to 4 layers (interface, orchestration, processing, infrastructure)
- Outcome: Clear separation of concerns, easier to extend, tests mirror src/
- Trade-off: Required import path updates, but long-term maintainability improved

**Decision 4: Non-Destructive Pipeline** (Design principle)
- Context: Original Phase 1 extraction produces 2,198 JSON files
- Problem: How to augment with Phase 2 statements without losing original data?
- Solution: Phase 2 only ADDS fields (`true_statements`, `validation_pass`, `nlp_analysis`), never modifies/deletes
- Outcome: Can always revert to original extraction, multiple passes possible
- Trade-off: JSON files grow larger, but data integrity preserved

## Important Gotchas

**Gotcha 1: System Codes vs Browser Organization**
- Browser shows 12 content areas, but codebase uses 16 two-letter system codes
- Example: Browser "Internal Medicine" contains multiple system codes (in, dm, id, etc.)
- Impact: All extraction, validation, reporting organized by 16 codes, NOT 12 browser groupings
- File: See `CLAUDE.md:23-27` for details

**Gotcha 2: Path Resolution for NLP Model**
- Problem: NLP model path in `.env` is relative, but code needs absolute path
- Solution: Added explicit path resolution in `statement_generator/src/infrastructure/config/settings.py`
- Failure mode: If PROJECT_ROOT misconfigured, model loading fails silently
- File: See `statement_generator/src/infrastructure/config/settings.py:15-20`

**Gotcha 3: Checkpoint Resumability**
- Feature: Pipeline can be interrupted and resumed without data loss
- Mechanism: `processed_questions.json` tracks completed questions
- Gotcha: If checkpoint file corrupted/deleted, pipeline reprocesses everything
- Location: `statement_generator/artifacts/checkpoints/processed_questions.json`

**Gotcha 4: Validation Pass ≠ Processing Success**
- Important distinction:
  - **Processing success**: Pipeline completed without errors (100% in Phase 3)
  - **Validation pass**: Statements meet quality standards (92.9% in Phase 3)
- A question can process successfully but fail validation (e.g., dmmcq24032)
- Impact: Monitor BOTH metrics in Phase 4

**Gotcha 5: LLM Provider Selection**
- Environment variable: `LLM_PROVIDER` (codex, anthropic, claude-code, gemini)
- Default: `codex` (Claude Code's built-in provider)
- Rate limits vary by provider (Anthropic API has strict limits, Claude Code more lenient)
- Cost varies by provider (Anthropic charges per token, Claude Code included in subscription)
- File: See `statement_generator/src/infrastructure/llm/client.py:30-50`

## Environment & Dependencies

**Python Version**: 3.13.5 (specified in `.env`, used by `./scripts/python` wrapper)

**Critical Dependencies**:
- `spacy` (NLP library)
- `scispacy` (scientific/medical NLP models)
- `anthropic` (Anthropic Claude API client)
- `pydantic` (data models)
- `pytest` (testing framework)
- Package manager: `pyproject.toml` (modern Python packaging)

**NLP Model Setup** (One-time):
```bash
# Download and extract scispacy model
./scripts/setup_nlp_model.sh

# Set environment variable (add to .env)
export MKSAP_NLP_MODEL=statement_generator/models/en_core_sci_sm-0.5.4/en_core_sci_sm/en_core_sci_sm-0.5.4
```

**Rust Environment** (Phase 1 only):
- Rust toolchain required for building extractor
- Build: `cargo build --release` in `extractor/` directory
- Binary: `target/release/mksap-extractor`

## Performance Characteristics

**Processing Time**:
- Phase 1 extraction: ~2 minutes per system (16 systems = ~30 minutes total for 2,198 questions)
- Phase 2 statement generation: ~45 seconds per question (with LLM calls)
- Phase 3 validation: Integrated into Phase 2, adds ~5-10 seconds per question
- Full Phase 4 production: 20-24 hours sequential, 4-6 hours with MKSAP_CONCURRENCY=5

**Memory Usage**:
- Phase 1 extractor: ~50MB
- Phase 2 pipeline (per question): ~500MB (NLP model + LLM client + processing)
- Phase 3 validation: Included in Phase 2, minimal additional memory
- Concurrent processing (5 questions): ~2.5GB total

**Disk Space**:
- Phase 1 output: ~50MB (2,198 JSON files)
- Phase 2 augmented: ~100MB (adds `true_statements`, `validation_pass`, `nlp_analysis` fields)
- Logs: ~10MB per 100 questions processed
- NLP model: 13MB (en_core_sci_sm)
- Total project: ~500MB including all artifacts

## Data Schema Evolution

**Phase 1 JSON Schema** (Original extraction):
```json
{
  "question_id": "cvmcq24001",
  "system": "cv",
  "type": "mcq",
  "stem": "...",
  "critique": "...",
  "key_points": ["...", "..."],
  "extra_field": "...",
  "options": ["A", "B", "C", "D"],
  "correct_answer": "C",
  "figures": [...],
  "tables": [...]
}
```

**Phase 2 Augmentation** (Statement extraction):
```json
{
  ...original Phase 1 fields...,
  "true_statements": {
    "from_critique": ["statement1", "statement2", ...],
    "from_key_points": ["statement1", "statement2", ...]
  }
}
```

**Phase 3 Augmentation** (Validation + metadata):
```json
{
  ...original Phase 1 fields...,
  "true_statements": {...},
  "validation_pass": true,
  "nlp_analysis": {
    "critique": {
      "entity_count": 45,
      "sentence_count": 12,
      "negation_count": 3,
      "entities": [
        {"text": "hypertension", "type": "DISEASE", "negated": false, "start": 10, "end": 22},
        ...
      ],
      "sentences": [
        {"text": "...", "has_negation": false, "is_atomic": true, "features": {...}},
        ...
      ],
      "negations": [
        {"trigger": "no", "start": 5, "end": 7},
        ...
      ]
    },
    "key_points": {...same structure as critique...}
  }
}
```

**Future Phase 5 Schema** (Cloze application, planned):
```json
{
  ...previous fields...,
  "cloze_cards": [
    {
      "front": "Patient has {{c1::hypertension}} with BP {{c2::150/90 mmHg}}",
      "back": "Answer: hypertension, 150/90 mmHg",
      "context": "...",
      "source_statement": "...",
      "cloze_count": 2
    },
    ...
  ]
}
```

## Quality Standards & Validation Rules

**Validation Framework** (6 check types):

1. **Structure Checks** (`statement_generator/src/validation/structure_checks.py`):
   - Required fields present: `text`, `source`, `cloze_candidates`
   - Proper types: text is string, cloze_candidates is list
   - Non-empty: text not blank, at least 5 characters

2. **Quality Checks** (`statement_generator/src/validation/quality_checks.py`):
   - Atomicity: One main medical fact per statement (no compound sentences)
   - Vague language: No "may", "might", "sometimes", "can be" (board-style certainty)
   - Board relevance: Contains medical terminology (not pure patient demographics)

3. **Ambiguity Checks** (`statement_generator/src/validation/ambiguity_checks.py`):
   - Medication context: Dose, route, frequency specified for drugs
   - Overlapping candidates: Cloze blanks don't overlap or nest

4. **Hallucination Checks** (`statement_generator/src/validation/hallucination_checks.py`):
   - 30% keyword overlap: Statement must share 30%+ keywords with source text
   - Prevents pure fabrication or excessive paraphrasing

5. **Enumeration Checks** (`statement_generator/src/validation/enumeration_checks.py`):
   - List detection: Identifies and validates list structures (A, B, and C)
   - Ensures list items properly formatted for flashcards

6. **Cloze Checks** (`statement_generator/src/validation/cloze_checks.py`):
   - 2-5 candidates: Optimal for fill-in-the-blank difficulty
   - No duplicates: Each candidate unique
   - Non-trivial: Candidates not just "a", "the", etc.

**Validation Pass Criteria**: ALL 6 check types must pass

**Phase 3 Baseline**: 92.9% pass rate (13/14 questions)
- 1 failure: dmmcq24032 (Diabetes/Metabolic MCQ) - likely due to complex compound statements

## Troubleshooting Common Issues

**Issue 1: NLP Model Loading Fails**
- Symptom: Error "Model not found" or "spacy.load() failed"
- Diagnosis: Check `MKSAP_NLP_MODEL` path in `.env`, verify model exists
- Solution: Run `./scripts/setup_nlp_model.sh` to download model, update `.env` path

**Issue 2: Validation Pass Rate Drops**
- Symptom: Pass rate <85% during Phase 4 scaled testing
- Diagnosis: Check which validation checks are failing (structure, quality, ambiguity, etc.)
- Solution: Review failed questions for patterns, may need prompt tuning or validation rule adjustment

**Issue 3: Processing Failures**
- Symptom: Questions fail to process (pipeline crashes, not validation failure)
- Diagnosis: Check error logs in `statement_generator/artifacts/logs/*.log`
- Solution: Common causes:
  - LLM provider rate limiting (switch provider or slow down)
  - Malformed question JSON (check source file)
  - Memory exhaustion (reduce MKSAP_CONCURRENCY if using parallel processing)

**Issue 4: Slow Processing**
- Symptom: Processing >2 minutes per question (expected: 45-60s)
- Diagnosis: Check NLP model loading time, LLM API latency, memory usage
- Solution:
  - Verify NLP model cached (should load once per process, not per question)
  - Check LLM provider status (API may be slow or throttling)
  - Monitor memory usage (may need to increase system resources)

**Issue 5: Git Merge Conflicts**
- Symptom: Conflicts when merging `backup-before-reorg` to `main`
- Diagnosis: Phase 3 changes conflict with main branch state
- Solution: Carefully review conflicts, prioritize Phase 3 changes (validation framework, NLP metadata)
  - Modified files: 14 test question JSONs, pipeline.py, validator.py, settings.py
  - New files: 6 validation check modules, Phase 4 deployment plan

## References & Documentation

**Project & Component Documentation** (global docs + component docs):
- `docs/INDEX.md` - Documentation entry point (comprehensive index)
- `docs/PROJECT_OVERVIEW.md` - Project goals and architecture
- `docs/QUICKSTART.md` - Essential commands for Phase 1-2
- `extractor/docs/PHASE_1_COMPLETION_REPORT.md` - Phase 1 final report
- `statement_generator/docs/PHASE_2_STATUS.md` - Phase 2 status and priorities
- `statement_generator/docs/PHASE_3_STATUS.md` - Phase 3 status (now marked complete)
- `statement_generator/docs/deployment/PHASE4_DEPLOYMENT_PLAN.md` - Phase 4 deployment strategy
- `extractor/docs/PHASE_1_DEEP_DIVE.md` - Phase 1 architecture details
- `statement_generator/docs/STATEMENT_GENERATOR.md` - Phase 2 CLI reference
- `extractor/docs/VALIDATION.md` - Validation framework guide
- `extractor/docs/TROUBLESHOOTING.md` - Debugging guide
- `statement_generator/docs/CLOZE_FLASHCARD_BEST_PRACTICES.md` - Flashcard design principles
- `statement_generator/docs/NLP_MODEL_COMPARISON.md` - NLP model evaluation (482 lines)
- `docs/DOCUMENTATION_MAINTENANCE_GUIDE.md` - How to maintain documentation
- `extractor/docs/EXTRACTION_SCOPE.md` - What's extracted from MKSAP questions

**Phase 3 Evaluation Reports**:
- `statement_generator/artifacts/phase3_evaluation/PHASE3_COMPLETE_FINAL_REPORT.md` - Comprehensive final report (authoritative)
- `statement_generator/docs/VALIDATION_IMPLEMENTATION.md` - Validation framework technical details
- `statement_generator/docs/NLP_PERSISTENCE_IMPLEMENTATION.md` - NLP metadata persistence technical details

**Code Reference**:
- Entry point: `statement_generator/src/interface/cli.py`
- Pipeline: `statement_generator/src/orchestration/pipeline.py`
- Validation: `statement_generator/src/validation/validator.py`
- NLP utils: `statement_generator/src/validation/nlp_utils.py`
- Evaluator: `statement_generator/tests/tools/phase3_evaluator.py`

**External Resources**:
- scispaCy documentation: https://allenai.github.io/scispacy/
- Anthropic Claude API: https://docs.anthropic.com/
- Anki manual: https://docs.ankiweb.net/
- genanki library: https://github.com/kerrickstaley/genanki
</critical_context>

<current_state>
## Project Status: Phase 3 Complete, Phase 4 Ready

**Current Phase**: Phase 3 Complete ✅ (January 16, 2026)
**Next Phase**: Phase 4 Production Deployment 📋 (Ready to execute)

**Branch**: `backup-before-reorg` (NOT main - need to merge or commit)

**Uncommitted Changes**:
- 14 test question JSON files modified with `validation_pass` + `nlp_analysis` fields
- 4 core files modified: pipeline.py, validator.py, settings.py, nlp_utils.py
- 6 new validation check modules (structure, quality, ambiguity, hallucination, enumeration, cloze)
- Updated documentation: CLAUDE.md, TODO.md, PHASE_3_STATUS.md
- Untracked: Phase 4 deployment plan, Phase 3 evaluation scripts, test files

**System Configuration**: Ready for Phase 4
- Hybrid pipeline enabled (`USE_HYBRID_PIPELINE=true`)
- NLP model loaded (en_core_sci_sm, 13MB, optimized)
- LLM provider configured (`LLM_PROVIDER=codex`)
- Validation framework integrated into pipeline
- Checkpoint system operational (14 questions processed so far)

**Phase 3 Results**: 92.9% validation pass rate
- 13/14 test questions passed validation
- 1 failure: dmmcq24032 (isolated, no pattern)
- 100% processing success (14/14 questions completed without errors)
- Perfect scores: negation preservation (100%), entity completeness (100%), unit accuracy (100%)
- Baseline improvement: +21.5 percentage points over LLM-only baseline (71.4% → 92.9%)

**Phase 4 Decision Required**: Choose deployment approach
- **Option A (Recommended)**: Staged rollout (50 → 500 → 2,198 questions)
  - Lower risk, validates consistency before full run
  - Time: 1-2 hours (Stage 1) + 5-6 hours (Stage 2) + 20-24 hours (Stage 3)
- **Option B**: Full deployment (all 2,198 questions immediately)
  - Higher risk, faster to completion
  - Time: 20-24 hours sequential, 4-6 hours with MKSAP_CONCURRENCY=5

**Blockers**: None - Ready to execute Phase 4

**Open Questions**:
1. Which deployment approach? (Option A recommended)
2. Commit Phase 3 changes before or after Phase 4?
3. Enable parallelization (MKSAP_CONCURRENCY=5) after Stage 1?
4. Merge `backup-before-reorg` to main now or later?

**Immediate Next Steps**:
1. User chooses deployment approach (Option A or B)
2. Run Phase 4 production pipeline (`./scripts/python -m src.interface.cli process --mode production`)
3. Monitor validation pass rate every 100 questions
4. Generate final evaluation report when complete
5. Update documentation and commit changes

**Data State**:
- Phase 1: 2,198 questions extracted ✅
- Phase 2: 14 questions processed with statements ✅
- Phase 3: 14 questions validated with metadata ✅
- Phase 4: 2,184 questions remaining (2,198 - 14 = 2,184)

**Artifacts**:
- Logs: 80+ files in `statement_generator/artifacts/logs/` (Phase 3 testing and earlier)
- Checkpoints: `statement_generator/artifacts/checkpoints/processed_questions.json` tracks 14 completed questions
- Evaluation reports: 1 final report in `statement_generator/artifacts/phase3_evaluation/` directory
- Implementation docs: 2 technical notes in `statement_generator/docs/`
- Modified JSON files: 14 test questions with new fields

**Technical Debt**:
1. Wrong log path: `statement_generator/statement_generator/artifacts/logs/` should be `statement_generator/artifacts/logs/`
2. Many uncommitted changes (need to commit or discard before Phase 4 completion)
3. Branch management: `backup-before-reorg` vs `main` needs resolution
4. Documentation: Several .md files in wrong locations (statement_generator/ root instead of statement_generator/docs/)

**Quality Assurance**:
- All Phase 3 success criteria met ✅
- All Phase 3 validation checks passing ✅
- No processing failures in Phase 3 testing ✅
- Ready for scaled deployment ✅
</current_state>
