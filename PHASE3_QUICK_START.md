# Phase 3 Evaluation - Quick Start Guide

**Status**: ✅ Framework complete, ready for batch execution
**Date**: January 16, 2026
**Next Step**: Run the evaluation script to process remaining 14 test questions

---

## What's Ready

### ✅ Completed (January 16, 2026)

1. **Test Question Selection** (`docs/phase3_evaluation/test_questions.md`)
   - 15 diverse questions across 7 medical systems
   - Commit: `49ab9388`

2. **Measurement Framework** (`statement_generator/tests/tools/phase3_evaluator.py`)
   - Complete evaluation framework with 3 measurement dimensions
   - Data classes for NegationCheck, EntityCheck, UnitCheck
   - Report generation with markdown output
   - Commit: `a2d63bce`

3. **Proof-of-Concept**
   - First question (`cvmcq24084`) successfully processed
   - Hybrid pipeline verified working end-to-end
   - 37 statements extracted, 119 cloze candidates identified

### 🔄 Ready to Execute

**Batch Execution Script**: `/Users/Mitchell/coding/projects/MKSAP/run_phase3_evaluation.sh`
- Executable and ready to run
- Processes 14 remaining test questions
- Generates evaluation report with metrics

---

## How to Run Later

### Quick Start (One Command)

```bash
cd /Users/Mitchell/coding/projects/MKSAP
./run_phase3_evaluation.sh
```

### What It Does

1. **Validates environment** - Checks prerequisites
2. **Processes 14 questions** - Runs through hybrid pipeline:
   ```
   [1/14] Processing: encor25001... ✓
   [2/14] Processing: enmcq24050... ✓
   [3/14] Processing: gimcq24025... ✓
   ... (continues for all 14)
   ```
3. **Generates report** - Creates evaluation metrics at:
   ```
   statement_generator/artifacts/phase3_evaluation/evaluation_report.md
   ```
4. **Shows results** - Displays validation pass rate and recommendations

### Expected Runtime

- **Per question**: 30-60 seconds (includes LLM API calls)
- **Total for 14 questions**: 7-15 minutes
- **Full including first question**: ~8-16 minutes for all 15

---

## What the Report Will Show

After running the script, check the report at:
```
statement_generator/artifacts/phase3_evaluation/evaluation_report.md
```

**Metrics included:**
- **Validation Pass Rate** - Compare to 71.4% baseline, target: 85%+
- **Negation Preservation** - Verify negations appear correctly in output
- **Entity Completeness** - Check all NLP entities referenced in statements
- **Unit Accuracy** - Confirm numeric values and units preserved exactly

**Recommendation:**
- ✅ **READY FOR PHASE 4** - If pass rate ≥ 85%
- ⚠️ **NEEDS ITERATION** - If pass rate 71-84%
- ❌ **REQUIRES INVESTIGATION** - If pass rate < 71%

---

## Test Questions Being Evaluated

**15 Total Questions** (1 completed + 14 remaining):

### Already Processed
- ✅ cvmcq24084 (Cardiovascular, MCQ) - 37 statements extracted

### Ready in Script
- encor25001, enmcq24050 (Endocrinology)
- gimcq24025, gicor25001 (Gastroenterology)
- dmmcq24032, dmcor25001 (Diabetes/Metabolic)
- npmcq24050, npcor25001 (Nephrology)
- ccmcq24035, cccor25002 (Critical Care)
- cvcor25010, cvvdx24045 (Cardiovascular)
- hpmcq24032, hpcor25001 (Hematology-Oncology)

---

## Files Created This Session

### Documentation
- `docs/phase3_evaluation/test_questions.md` - Test selection and strategy
- `run_phase3_evaluation.sh` - Batch execution script
- `PHASE3_QUICK_START.md` - This file

### Code
- `statement_generator/tests/tools/phase3_evaluator.py` - Evaluation framework (488 lines)

### Outputs (Will be created when you run the script)
- `statement_generator/artifacts/phase3_evaluation/evaluation_report.md` - Final evaluation report
- `mksap_data/[system]/[question_id]/[question_id].json` - Updated with `true_statements` field

---

## Git Commits This Session

```
49ab9388 docs: create Phase 3 test question selection and strategy
a2d63bce feat: add Phase 3 evaluation framework for measuring hybrid pipeline improvements
```

---

## Troubleshooting

### If script doesn't run:
```bash
# Make script executable
chmod +x /Users/Mitchell/coding/projects/MKSAP/run_phase3_evaluation.sh

# Then run it
./run_phase3_evaluation.sh
```

### If questions already processed:
The script checks before re-processing. To force reprocess:
```bash
# Remove the true_statements field first, then run script
# Or modify run_phase3_evaluation.sh to add --force flag
```

### If you get API errors:
Check that the LLM provider (Claude Code CLI) is configured and working:
```bash
./scripts/python -m src.interface.cli process --question-id cvmcq24084
```

---

## Next Steps After Report

1. **Read the evaluation report** at `statement_generator/artifacts/phase3_evaluation/evaluation_report.md`
2. **Check metrics** - Validation pass rate against 85% target
3. **Decide Phase 4 readiness**:
   - If ≥85% → Ready to switch hybrid as default for all 2,198 questions
   - If 71-84% → Iterate on Phase 2 (prompts, NLP settings)
   - If <71% → Investigate root causes

4. **Update documentation** - Record Phase 3 results in `docs/PHASE_2_STATUS.md`

---

**Ready to run anytime. Questions? Check the troubleshooting section above.**
