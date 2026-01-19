# Phase 4 Deployment Plan

**Created**: January 16, 2026
**Phase**: 4 - Production Deployment
**Status**: 📋 Ready to Execute
**Prerequisites**: ✅ Phase 3 Complete (92.9% validation pass rate)

---

## Executive Summary

Deploy the hybrid NLP+LLM pipeline to process all 2,198 MKSAP questions, generating validated medical education statements with comprehensive quality metrics.

**Phase 3 Results**:
- ✅ 92.9% validation pass rate (exceeds 85% target)
- ✅ 100% negation preservation, entity completeness, unit accuracy
- ✅ 14/14 test questions successful (0 failures)
- ✅ +21.5 pp improvement over baseline (71.4% → 92.9%)

**Phase 4 Goal**: Maintain 90%+ validation pass rate across full 2,198 question dataset

---

## Deployment Options

### Option A: Staged Rollout (Recommended) ⭐

**Philosophy**: Validate at scale before full commitment

#### Stage 1: Scaled Testing (50 questions)
**Goal**: Confirm Phase 3 results hold on larger sample

**Execute**:
```bash
cd /Users/Mitchell/coding/projects/MKSAP

# Process next 50 unprocessed questions
./scripts/python -m src.interface.cli process \
  --mode production \
  --data-root mksap_data

# Monitor: Stop after ~50 questions processed
# Check: tail -f statement_generator/artifacts/logs/statement_gen_*.log
```

**Evaluate**:
```bash
# Generate scaled test report
python3 << 'EOF'
import sys, json
sys.path.insert(0, "/Users/Mitchell/coding/projects/MKSAP/statement_generator")
from pathlib import Path
from tests.tools.phase3_evaluator import Phase3Evaluator

project_root = Path("/Users/Mitchell/coding/projects/MKSAP")
evaluator = Phase3Evaluator(project_root)

# Get recently processed questions
checkpoint_file = project_root / "statement_generator/artifacts/checkpoints/processed_questions.json"
with open(checkpoint_file) as f:
    processed = json.load(f).get("processed_questions", [])

# Evaluate recent 50
evaluations = evaluator.evaluate_batch(processed[-50:])
output_file = project_root / "statement_generator/artifacts/phase3_evaluation/scaled_test_report.md"
evaluator.generate_report(evaluations, output_file)

pass_count = sum(1 for e in evaluations if e.validation_pass)
print(f"\n✓ Evaluated {len(evaluations)} questions")
print(f"✓ Validation pass rate: {pass_count}/{len(evaluations)} ({pass_count/len(evaluations)*100:.1f}%)")
print(f"✓ Report: {output_file}")
EOF
```

**Decision Gate**:
- ✅ Pass rate ≥90%: → Proceed to Stage 2
- ⚠️ Pass rate 85-89%: → Review patterns, proceed with caution
- ❌ Pass rate <85%: → Investigate failures, adjust before continuing

**Expected Time**: 1-2 hours
**Expected Outcome**: 90%+ validation pass rate maintained

---

#### Stage 2: Batch Processing (500 questions)
**Goal**: Validate stability and performance at larger scale

**Execute**:
```bash
# Continue processing (will auto-skip already processed)
./scripts/python -m src.interface.cli process \
  --mode production \
  --data-root mksap_data

# Monitor with:
watch -n 30 'grep "Total processed:" statement_generator/artifacts/logs/statement_gen_*.log | tail -1'

# Stop after ~500 total questions processed
```

**Monitor**:
```bash
# Check validation pass rate every 100 questions
./scripts/python -c "
import json
from pathlib import Path
data_dir = Path('/Users/Mitchell/coding/projects/MKSAP/mksap_data')
passed = failed = 0
for qfile in data_dir.rglob('*.json'):
    try:
        with open(qfile) as f:
            d = json.load(f)
        if 'validation_pass' in d:
            if d['validation_pass']: passed += 1
            else: failed += 1
    except: pass
total = passed + failed
print(f'Validation: {passed}/{total} ({passed/total*100:.1f}%) | Failed: {failed}')
"
```

**Decision Gate**:
- ✅ Pass rate ≥90%, <5 failures: → Proceed to Stage 3
- ⚠️ Pass rate 85-89%, <10 failures: → Acceptable, proceed
- ❌ Pass rate <85% or systematic failures: → Investigate before continuing

**Expected Time**: 5-6 hours
**Expected Outcome**: Consistent 90%+ pass rate, <1% failure rate

---

#### Stage 3: Full Production (2,198 questions)
**Goal**: Complete dataset processing

**Execute**:
```bash
# Process remaining questions
./scripts/python -m src.interface.cli process \
  --mode production \
  --data-root mksap_data

# Monitor continuously
tail -f statement_generator/artifacts/logs/statement_gen_*.log
```

**Checkpoint Monitoring**:
```bash
# Every hour, check progress
./scripts/python -c "
import json
from pathlib import Path
cp = Path('/Users/Mitchell/coding/projects/MKSAP/statement_generator/artifacts/checkpoints/processed_questions.json')
with open(cp) as f:
    data = json.load(f)
processed = len(data.get('processed_questions', []))
failed = len(data.get('failed_questions', []))
remaining = 2198 - processed
print(f'Processed: {processed}/2198 ({processed/2198*100:.1f}%)')
print(f'Failed: {failed} ({failed/processed*100:.2f}% if processed > 0 else 0)')
print(f'Remaining: {remaining}')
print(f'Estimated time: {remaining * 45 / 3600:.1f} hours')
"
```

**Expected Time**: 20-24 hours total
**Expected Outcome**: 2,198 questions processed, 90%+ validation pass rate

---

### Option B: Full Deployment (Higher Risk)

**Philosophy**: Phase 3 results are excellent, proceed with full deployment immediately

**Execute**:
```bash
cd /Users/Mitchell/coding/projects/MKSAP

# Process all 2,198 questions
./scripts/python -m src.interface.cli process \
  --mode production \
  --data-root mksap_data
```

**Monitoring Strategy**:
- Check validation pass rate every 100 questions
- Review failures immediately
- Prepared to stop if pass rate drops below 85%

**Expected Time**: 20-24 hours
**Risk**: Higher - less opportunity to catch systematic issues early

**Recommendation**: Only if time-constrained AND confident in Phase 3 results

---

## Parallelization (Optional)

**Goal**: Reduce processing time from 24 hours to 4-6 hours

**Setup**:
```bash
# Add to .env
echo "MKSAP_CONCURRENCY=5" >> /Users/Mitchell/coding/projects/MKSAP/.env
```

**Trade-offs**:
- ✅ Pros: 4-5x faster processing
- ❌ Cons: Higher memory usage (500MB × 5 processes), harder to monitor
- ⚠️ Caution: LLM provider rate limits may apply

**Resource Requirements**:
- Memory: ~2.5GB (5 processes × 500MB)
- CPU: Moderate (mostly waiting on LLM API calls)
- Disk: Minimal (sequential writes to different files)

**Recommendation**: Enable after Stage 1 validation successful

---

## Quality Assurance

### Automated Checks

**1. Validation Pass Rate Tracking**
```bash
# Create monitoring script
cat > /tmp/check_validation_rate.sh << 'SCRIPT'
#!/bin/bash
python3 -c "
import json
from pathlib import Path
data_dir = Path('/Users/Mitchell/coding/projects/MKSAP/mksap_data')
passed = failed = 0
failed_ids = []
for qfile in data_dir.rglob('*.json'):
    try:
        with open(qfile) as f:
            d = json.load(f)
        if 'validation_pass' in d:
            if d['validation_pass']: passed += 1
            else: failed += 1; failed_ids.append(d['question_id'])
    except: pass
total = passed + failed
if total > 0:
    print(f'Validation Rate: {passed}/{total} ({passed/total*100:.1f}%)')
    print(f'Failed: {failed} questions')
    if failed_ids[:10]: print(f'  First 10 failures: {failed_ids[:10]}')
"
SCRIPT
chmod +x /tmp/check_validation_rate.sh

# Run every 30 minutes
watch -n 1800 /tmp/check_validation_rate.sh
```

**2. Processing Failure Tracking**
```bash
# Check failed questions
./scripts/python -c "
import json
from pathlib import Path
cp = Path('/Users/Mitchell/coding/projects/MKSAP/statement_generator/artifacts/checkpoints/processed_questions.json')
with open(cp) as f:
    failed = json.load(f).get('failed_questions', [])
print(f'Failed questions: {len(failed)}')
if failed: print(f'  IDs: {failed}')
"
```

### Manual Spot Checks

**Random Sample Review** (every 100 questions):
```bash
# Pick 3 random processed questions
./scripts/python -c "
import json, random
from pathlib import Path
data_dir = Path('/Users/Mitchell/coding/projects/MKSAP/mksap_data')
processed = [p for p in data_dir.rglob('*.json') if json.load(open(p)).get('validation_pass') is not None]
samples = random.sample(processed, min(3, len(processed)))
for s in samples:
    data = json.load(open(s))
    print(f\"\n{data['question_id']}: validation_pass={data['validation_pass']}\")
    ts = data['true_statements']
    print(f\"  Statements: {len(ts['from_critique'])} critique + {len(ts['from_key_points'])} keypoints\")
    if 'nlp_analysis' in data:
        nlp = data['nlp_analysis']
        print(f\"  NLP: {nlp['critique']['entity_count']} entities, {nlp['critique']['negation_count']} negations\")
"
```

---

## Success Criteria

### Must Meet (Phase 4 Success)
- ✅ Validation pass rate ≥85% across full dataset
- ✅ Processing failure rate <2% (max 44 failed questions)
- ✅ All 2,198 questions processed

### Target (Excellent Result)
- 🎯 Validation pass rate ≥90% (matching Phase 3)
- 🎯 Processing failure rate <0.5% (max 11 failed questions)
- 🎯 Average processing time <60s per question

### Red Flags (Investigate Immediately)
- 🚨 Validation pass rate drops below 80%
- 🚨 Processing failures >5% (>110 questions)
- 🚨 Systematic pattern in failures (all from one system, one question type)

---

## Rollback Plan

### If Validation Pass Rate Drops Below 80%

**Immediate Actions**:
1. **Stop processing**: Kill the CLI process
2. **Analyze failures**: Run failure analysis script
3. **Review patterns**: Check if specific systems/question types affected

**Failure Analysis**:
```bash
# Analyze failed validations by system
./scripts/python -c "
import json
from pathlib import Path
from collections import Counter
data_dir = Path('/Users/Mitchell/coding/projects/MKSAP/mksap_data')
failed_by_system = Counter()
for qfile in data_dir.rglob('*.json'):
    try:
        data = json.load(open(qfile))
        if data.get('validation_pass') == False:
            system = data['question_id'][:2]
            failed_by_system[system] += 1
    except: pass
print('Failed validations by system:')
for system, count in failed_by_system.most_common():
    print(f'  {system}: {count}')
"
```

**Recovery Options**:
1. **Continue with caution**: If failures are isolated, proceed but monitor closely
2. **Prompt tuning**: If specific validation checks failing, adjust prompts
3. **Validation rule adjustment**: If rules too strict, relax specific checks
4. **Full stop**: If systematic quality issue, investigate thoroughly before continuing

### If Processing Failures Exceed 5%

**Immediate Actions**:
1. **Stop processing**
2. **Check error logs**: Review recent errors in logs
3. **Test LLM provider**: Verify API/CLI still responding

**Common Causes**:
- LLM provider rate limiting
- API key expiration (anthropic provider)
- Network issues
- Malformed question JSON
- NLP model loading failure

**Resolution**:
- Switch LLM provider if needed
- Wait for rate limit reset
- Skip problematic questions (note for manual review)

---

## Post-Processing

### After Completion

**1. Generate Final Evaluation Report**:
```bash
python3 << 'EOF'
import sys, json
sys.path.insert(0, "/Users/Mitchell/coding/projects/MKSAP/statement_generator")
from pathlib import Path
from tests.tools.phase3_evaluator import Phase3Evaluator

project_root = Path("/Users/Mitchell/coding/projects/MKSAP")
evaluator = Phase3Evaluator(project_root)

# Get all processed questions
checkpoint_file = project_root / "statement_generator/artifacts/checkpoints/processed_questions.json"
with open(checkpoint_file) as f:
    processed = json.load(f).get("processed_questions", [])

# Evaluate all (may take time if 2,198 questions)
print(f"Evaluating {len(processed)} questions...")
evaluations = evaluator.evaluate_batch(processed)

output_file = project_root / "statement_generator/artifacts/phase3_evaluation/phase4_final_report.md"
evaluator.generate_report(evaluations, output_file)

# Print summary
pass_count = sum(1 for e in evaluations if e.validation_pass)
print(f"\n✓ Phase 4 Complete!")
print(f"✓ Processed: {len(evaluations)}/2198")
print(f"✓ Validation pass rate: {pass_count}/{len(evaluations)} ({pass_count/len(evaluations)*100:.1f}%)")
print(f"✓ Report: {output_file}")
EOF
```

**2. Calculate Final Metrics**:
```bash
./scripts/python -c "
import json
from pathlib import Path
data_dir = Path('/Users/Mitchell/coding/projects/MKSAP/mksap_data')
passed = failed = 0
total_statements = 0
systems = {}

for qfile in data_dir.rglob('*.json'):
    try:
        data = json.load(open(qfile))
        if 'validation_pass' in data:
            if data['validation_pass']: passed += 1
            else: failed += 1

            # Count statements
            ts = data['true_statements']
            count = len(ts['from_critique']) + len(ts['from_key_points'])
            total_statements += count

            # By system
            system = data['question_id'][:2]
            if system not in systems: systems[system] = {'passed': 0, 'failed': 0}
            if data['validation_pass']: systems[system]['passed'] += 1
            else: systems[system]['failed'] += 1
    except: pass

total = passed + failed
print(f'Overall Metrics:')
print(f'  Questions processed: {total}/2198 ({total/2198*100:.1f}%)')
print(f'  Validation pass rate: {passed}/{total} ({passed/total*100:.1f}%)')
print(f'  Total statements: {total_statements} (avg {total_statements/total:.1f} per question)')
print(f'\nBy System:')
for sys, counts in sorted(systems.items()):
    sys_total = counts['passed'] + counts['failed']
    sys_rate = counts['passed'] / sys_total * 100 if sys_total > 0 else 0
    print(f'  {sys}: {counts[\"passed\"]}/{sys_total} ({sys_rate:.1f}%)')
"
```

**3. Create Phase 4 Completion Report**:
- Document final metrics
- Compare to Phase 3 results
- Analyze any patterns in failed validations
- Recommend next steps (Phase 5 or quality review)

---

## Timeline Estimates

### Option A: Staged Rollout (Recommended)

| Stage | Questions | Time | Cumulative |
|-------|-----------|------|------------|
| Stage 1: Scaled Test | 50 | 1-2 hours | 1-2 hours |
| Stage 2: Batch | 500 | 5-6 hours | 6-8 hours |
| Stage 3: Full | 2,198 | 20-24 hours | 26-32 hours |
| Evaluation | - | 2-3 hours | 28-35 hours |

**Total**: ~28-35 hours (1-1.5 days active monitoring)

### Option B: Full Deployment

| Phase | Questions | Time |
|-------|-----------|------|
| Full Processing | 2,198 | 20-24 hours |
| Evaluation | - | 2-3 hours |

**Total**: ~22-27 hours (1 day active monitoring)

### With Parallelization (MKSAP_CONCURRENCY=5)

| Phase | Questions | Time |
|-------|-----------|------|
| Full Processing | 2,198 | 4-6 hours |
| Evaluation | - | 2-3 hours |

**Total**: ~6-9 hours (same day completion)

---

## Risk Assessment

### Low Risk ✅
- Validation pass rate 90%+
- Processing failures <1%
- All Phase 3 success criteria met
- Systematic patterns analyzed

### Medium Risk ⚠️
- Validation pass rate 85-89%
- Processing failures 1-2%
- Some edge cases identified but not systematic
- Requires closer monitoring

### High Risk 🚨
- Validation pass rate <85%
- Processing failures >2%
- Systematic failures in specific systems/question types
- Should investigate before proceeding

**Current Assessment**: ✅ **LOW RISK** (Phase 3 results excellent)

---

## Decision Matrix

**Choose Option A (Staged) if**:
- First time deploying at scale
- Want maximum confidence before full run
- Can afford 28-35 hour timeline
- Prefer lower risk approach

**Choose Option B (Full) if**:
- Confident in Phase 3 results (92.9% pass rate)
- Need faster completion (22-27 hours)
- Willing to monitor closely
- Acceptable with slightly higher risk

**Recommendation**: **Option A (Staged Rollout)** - The incremental validation provides valuable confidence and allows early detection of any issues.

---

**Plan Created**: January 16, 2026
**Status**: 📋 Ready to Execute
**Next Action**: Choose deployment option and begin Stage 1
