# Week 2 Handoff Document

**Date**: 2026-01-05
**Status**: Week 2 Complete → Ready for Week 3
**Next Session Focus**: Scale processing to full dataset + refinement

---

## Quick Context: Where We Are

### Weeks 1-2 Summary

**Week 1** (Dec 27-31, 2025):
- ✅ Core pipeline implemented (4 phases: critique → key_points → cloze → normalization)
- ✅ Multi-provider support (Anthropic, Claude Code, Gemini, Codex)
- ✅ Checkpoint/resume system
- ✅ 7 questions processed successfully
- ⚠️ Table extraction broken (0 statements extracted)
- ⚠️ No validation framework

**Week 2** (Jan 5, 2026):
- ✅ Table extraction fixed (0 → 12 statements per question)
- ✅ Validation framework complete (6 check categories, 130 tests)
- ✅ 71.4% validation pass rate (5 of 7 questions)
- ✅ All tests passing (100% pass rate)

---

## Current State Snapshot

### What's Working

1. **Statement Extraction Pipeline** ✅
   - Critique extraction: 10-20 statements per question
   - Key points extraction: 2-5 statements per question
   - **Table extraction: 8-15 statements per table** (NEW - Week 2 fix)
   - Cloze identification: 2-5 candidates per statement
   - Text normalization: symbols, units, formatting

2. **Validation Framework** ✅
   - 6 check categories: structure, quality, cloze, ambiguity, enumeration, hallucination
   - 130 tests, 100% pass rate
   - <5% false positive rate
   - Detailed reporting with severity levels (error, warning, info)

3. **Multi-Provider Support** ✅
   - Anthropic API: Fully tested
   - Claude Code CLI: Tested (table extraction working)
   - Gemini CLI: Implemented, needs testing
   - Codex CLI: Implemented, needs testing

4. **Infrastructure** ✅
   - Checkpoint/resume: Atomic saves, batch processing
   - Non-destructive updates: Preserves all Phase 1 data
   - Sequential processing: Stable, no race conditions
   - Logging: Detailed debug logs, auto-cleanup

### What Needs Work

1. **Scale** - Only 7 of 2,198 questions processed (0.3%)
2. **Provider Testing** - Gemini/Codex CLI not tested yet
3. **Refinement** - Procedure ambiguity detector has some false positives
4. **Performance** - Sequential processing (no parallelism yet)
5. **Cloze Candidates** - Some "not found in statement" errors

---

## Critical Files Reference

### Core Implementation
```
statement_generator/
├── src/
│   ├── main.py                              # CLI entry point
│   ├── pipeline.py                          # 4-phase orchestration
│   ├── critique_processor.py                # Phase 1
│   ├── keypoints_processor.py               # Phase 2
│   ├── cloze_identifier.py                  # Phase 3
│   ├── text_normalizer.py                   # Phase 4
│   ├── table_processor.py                   # Table extraction
│   ├── llm_client.py                        # Multi-provider client
│   └── validation/
│       ├── validator.py                     # Main validation entry
│       ├── structure_checks.py              # JSON validation
│       ├── quality_checks.py                # ✨ Enhanced Week 2
│       ├── cloze_checks.py                  # Cloze candidate validation
│       ├── ambiguity_checks.py              # ✨ NEW Week 2
│       ├── enumeration_checks.py            # List/enumeration detection
│       └── hallucination_checks.py          # Source fidelity
│
├── prompts/
│   ├── critique_extraction.md               # Phase 1 prompt
│   ├── keypoints_extraction.md              # Phase 2 prompt
│   ├── cloze_identification.md              # Phase 3 prompt
│   ├── text_normalization.md                # Phase 4 prompt
│   └── table_extraction.md                  # ✨ Fixed Week 2
│
└── tests/
    ├── test_ambiguity_checks.py             # ✨ NEW Week 2 (36 tests)
    ├── test_enumeration_checks.py           # ✨ NEW Week 2 (63 tests)
    └── test_quality_checks.py               # ✨ NEW Week 2 (31 tests)
```

### Documentation
```
statement_generator/
├── WEEK2_EXECUTION_PLAN.md                  # Week 2 plan (reference)
├── WEEK2_COMPLETION_REPORT.md               # Week 2 results
└── WEEK2_HANDOFF.md                         # This file

docs/
└── PHASE_2_STATUS.md                        # Updated with Week 2 progress
```

---

## Ready-to-Execute Commands

### Process Questions

```bash
# From repo root

# Single question (test)
./scripts/python -m src.main process --question-id cvmcq24001 --provider claude-code

# All questions in a system
./scripts/python -m src.main process --system cv --provider claude-code

# Production mode (all 2,198 questions)
./scripts/python -m src.main process --mode production --provider claude-code
```

### Validate Questions

```bash
# Single question
./scripts/python -m src.main validate --question-id cvmcq24001 --detailed

# All processed questions
./scripts/python -m src.main validate --all --severity error

# Generate report
./scripts/python -m src.main validate --all --output validation_report.txt
```

### Run Tests

```bash
# All validation tests
./scripts/python -m pytest statement_generator/tests/test_ambiguity_checks.py -v
./scripts/python -m pytest statement_generator/tests/test_enumeration_checks.py -v
./scripts/python -m pytest statement_generator/tests/test_quality_checks.py -v

# All tests with coverage
./scripts/python -m pytest statement_generator/tests/ --cov=statement_generator/src/validation --cov-report=html
```

### Check Progress

```bash
# Show statistics
./scripts/python -m src.main stats

# Show processed questions
./scripts/python -c "
import json
from pathlib import Path

checkpoint = Path('statement_generator/outputs/checkpoints/processed_questions.json')
if checkpoint.exists():
    data = json.loads(checkpoint.read_text())
    print(f'Processed: {len(data[\"processed_questions\"])}')
    print(f'Failed: {len(data[\"failed_questions\"])}')
"
```

---

## Week 3 Task List

### High Priority (Do First)

1. **Scale Processing** 🎯
   - Target: Process 10-20 questions per day
   - Start with: System cv (240 questions)
   - Monitor: API costs, processing time
   - Command: `./scripts/python -m src.main process --system cv --provider claude-code`

2. **Validation Refinement** 🔧
   - Review: Procedure ambiguity false positives
   - Fix: "clinical characteristics", "physical inactivity" patterns
   - Test: Run validation on 20+ questions
   - Update: Ambiguity detection patterns in `ambiguity_checks.py`

3. **Automated Reporting** 📊
   - Create: `validation_metrics.py` script
   - Track: Pass rate, issue distribution, processing time
   - Output: Daily summary reports
   - Location: `statement_generator/outputs/reports/`

### Medium Priority (Next)

4. **Provider Testing** 🧪
   - Test: Gemini CLI integration
   - Test: Codex CLI integration
   - Verify: Temperature support, error handling
   - Document: Cost comparison (API vs CLI providers)

5. **Performance Optimization** ⚡
   - Batch LLM calls (if provider supports)
   - Parallel processing (with rate limiting)
   - Cache expensive operations
   - Target: <30 seconds per question

6. **Cloze Candidate Debugging** 🐛
   - Investigate: "not found in statement" errors
   - Fix: Formatting issues, special characters
   - Test: Re-validate failed questions
   - Update: Cloze identification patterns

### Low Priority (Later)

7. **Documentation Updates** 📝
   - Update: README with Week 2 progress
   - Create: Troubleshooting guide
   - Document: Common validation issues
   - Write: Provider selection guide

8. **Threshold Tuning** 🎚️
   - Analyze: Warning thresholds on larger sample (50+ questions)
   - Adjust: Length threshold (200 chars), cloze candidate count (6+)
   - Test: Impact on pass rate
   - Document: Rationale for changes

---

## Known Issues & Workarounds

### Issue 1: Procedure Ambiguity False Positives

**Problem**: Some medical terms flagged as "procedures" when they're actually conditions or risk factors.

**Examples**:
- "physical inactivity"
- "clinical characteristics"
- "at least one additional risk factor"

**Workaround**: Manual review of validation warnings, ignore procedure warnings for these patterns.

**Fix**: Update `detect_ambiguous_procedure_clozes()` to exclude common false positives.

---

### Issue 2: Cloze Candidate "Not Found" Errors

**Problem**: Some cloze candidates not found in statement text (e.g., ">250 mg/dL", "IL-4").

**Cause**: Likely special characters, formatting inconsistencies, or tokenization issues.

**Workaround**: Review failed questions manually, consider adding hints in extra_field.

**Fix**: Improve cloze candidate extraction to handle special characters and units.

---

### Issue 3: macOS grep -P Not Supported

**Problem**: `tools/validation/validate_sample.sh` uses `grep -P` (Perl regex) which isn't available on macOS.

**Workaround**: Use Python for parsing validation output instead of bash+grep.

**Fix**: Rewrite validation scripts to use Python only (no shell dependencies).

---

## Critical Reminders

### For Statement Processing

1. **Always use claude-code provider first** - Most reliable for table extraction
2. **Check validation after processing** - Catch issues early
3. **Monitor API costs** - Track usage per provider
4. **Review failed questions** - Learn from extraction errors

### For Validation

1. **<5% false positive target** - Review warnings manually when tuning
2. **Errors are blockers** - Fix before marking question as "complete"
3. **Warnings are recommendations** - May need manual review
4. **Info is FYI** - Document patterns for future improvement

### For Testing

1. **Run tests before committing** - Ensure no regressions
2. **Add tests for new patterns** - Especially false positives
3. **Maintain >80% coverage** - Check with `pytest --cov`
4. **Test with real questions** - Not just unit tests

---

## Success Metrics (Week 3 Goals)

### Processing
- [ ] **100 questions processed** (4.5% of total)
- [ ] **<5% extraction failures** (robust error handling)
- [ ] **<30 seconds per question average** (performance)

### Validation
- [ ] **>75% pass rate** (quality threshold)
- [ ] **<3% false positive rate** (refinement)
- [ ] **Daily validation reports** (monitoring)

### Testing
- [ ] **All tests passing** (no regressions)
- [ ] **>80% code coverage** (maintained)
- [ ] **Provider integration tests** (Gemini/Codex)

---

## Environment & Dependencies

### Python Environment
```bash
./scripts/python --version  # 3.9+
pip3 list | grep anthropic  # anthropic==0.39.0
pip3 list | grep pydantic    # pydantic==2.10.6
pip3 list | grep pytest      # pytest==9.0.2
```

### Claude CLI
```bash
claude --version  # 2.0.76 (Claude Code)
```

### Environment Variables
```bash
# Required for Anthropic API
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Override provider
export LLM_PROVIDER="claude-code"

# Optional: Override model/temperature
export LLM_MODEL="sonnet"
export LLM_TEMPERATURE="0.2"
```

---

## Quick Troubleshooting

### Problem: JSONDecodeError from table extraction

**Solution**: Prompt was fixed in Week 2 - update to latest `table_extraction.md`

### Problem: "Command not found: python"

**Solution**: Use `./scripts/python` (repo wrapper) instead of `python`

### Problem: Validation tests fail

**Solution**: Verify all modules imported correctly, check for syntax errors in test files

### Problem: Rate limiting from Anthropic API

**Solution**: Switch to `--provider claude-code` (CLI) to avoid API costs

---

## Next Session Checklist

When you start Week 3, do this first:

1. ✅ Read this handoff document (you're doing it!)
2. ⬜ Review `WEEK2_COMPLETION_REPORT.md` for full context
3. ⬜ Run validation tests: `./scripts/python -m pytest statement_generator/tests/ -v`
4. ⬜ Check current stats: `./scripts/python -m src.main stats`
5. ⬜ Pick a task from High Priority list
6. ⬜ Start processing: `./scripts/python -m src.main process --system cv --provider claude-code`

---

## Key Decisions Made

### Week 1-2 Architectural Decisions

1. **Sequential processing only** - Simpler error handling, avoids rate limits
2. **Non-destructive updates** - Preserves Phase 1 data integrity
3. **Multi-provider support** - Flexibility for cost/performance trade-offs
4. **Checkpoint batching** - Balance between I/O efficiency and resume granularity
5. **Validation as separate step** - Decouples extraction from quality checking
6. **Table extraction via LLM** - More flexible than HTML parsing

### Week 2 Implementation Decisions

1. **6 validation categories** - Comprehensive without being overwhelming
2. **3 severity levels** - Error (blocker), Warning (review), Info (FYI)
3. **<5% false positive target** - Balance between coverage and noise
4. **Procedure ambiguity detection** - Aggressive (some false positives acceptable)
5. **Prompt fixes over code changes** - Easier to iterate on prompts
6. **Test-first for validation** - Ensures patterns work before integration

---

## Contact & Resources

### Documentation
- **Phase 1**: `docs/PHASE_1_COMPLETION_REPORT.md`
- **Phase 2**: `docs/PHASE_2_STATUS.md`
- **Week 1**: `docs/archive/phase-2/reports/WEEK1_FINAL_REPORT.md`
- **Week 2**: `docs/archive/phase-2/reports/WEEK2_COMPLETION_REPORT.md`

### Code Location
- **Main**: `statement_generator/`
- **Tests**: `statement_generator/tests/`
- **Data**: `mksap_data/`

### Useful Commands
```bash
# Full test suite
./scripts/python -m pytest statement_generator/tests/ -v --cov=statement_generator/src

# Process + validate pipeline
./scripts/python -m src.main process --question-id cvmcq24001 && \
./scripts/python -m src.main validate --question-id cvmcq24001 --detailed

# Cleanup old logs
./scripts/python -m src.main clean-logs --keep-days 7

# Reset checkpoints (use with caution!)
./scripts/python -m src.main reset
```

---

**Handoff Complete** - Ready for Week 3!

**Next Focus**: Scale to 100 processed questions with validation refinement.

**Status**: ✅ Week 2 deliverables complete, validation framework production-ready, table extraction working.

---

**Created**: 2026-01-05
**For**: Week 3 continuation
**Priority**: High - Start scaling processing immediately
