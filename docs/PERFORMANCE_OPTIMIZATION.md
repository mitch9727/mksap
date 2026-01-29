# Performance Optimization Guide

**Last Updated**: January 23, 2026
**Category**: Living Documentation
**Audience**: Developers optimizing statement generator performance

---

## Overview

This guide covers performance optimization techniques implemented in the MKSAP statement generator, including profiling, caching, async patterns, and benchmarking.

**Related Documentation**:
- [ASYNC_IMPLEMENTATION.md](../statement_generator/docs/ASYNC_IMPLEMENTATION.md) - Async LLM infrastructure details
- [CODING_STANDARDS.md](CODING_STANDARDS.md) - Performance best practices
- [Audit Plan](.claude/plans/splendid-herding-sutherland.md) - Original audit findings

---

## Quick Reference: Optimization Status

| Optimization | Status | Speedup | Implementation |
|-------------|--------|---------|----------------|
| orjson JSON serialization | ✅ Enabled | 2-3% | Auto (replaces `json` module) |
| @lru_cache decorators | ✅ Enabled | 5% | Auto (text normalization, NLP) |
| LLM response caching | ✅ Enabled | 5-15% on re-runs | Configurable via env |
| NLP document caching | ✅ Enabled | 5-10% | Auto (spaCy Doc objects) |
| NLP analyzer singletons | ✅ Enabled | <1% | Auto (class-level instances) |
| pytest-xdist parallel tests | ✅ Available | 75% test time | Manual: `pytest -n auto` |
| Async LLM calls | ⚠️ Infrastructure only | 3-5x potential | Not operational (needs 4-8h work) |

**Combined Speedup** (enabled optimizations): ~12-18% overall + cache benefits

---

## Profiling with py-spy

### Installation

```bash
# Install py-spy (requires system permissions)
pip install py-spy

# macOS may require sudo
sudo pip install py-spy

# Or use pipx (recommended)
pipx install py-spy
```

### Basic Profiling

**Profile a batch run:**
```bash
# Profile 50-question batch
py-spy record -o /Users/Mitchell/coding/projects/MKSAP/profile.svg \
  -- ./scripts/python -m src.interface.cli process --limit 50

# Open flame graph in browser
open profile.svg
```

**Live top view:**
```bash
# Real-time function call monitoring
py-spy top -- ./scripts/python -m src.interface.cli process --limit 10
```

**Profile specific function:**
```bash
# Profile with function filter
py-spy record --function --format speedscope -o profile.json \
  -- ./scripts/python -m src.interface.cli process --limit 20
```

### Interpreting Flame Graphs

**What to look for:**
1. **Wide bars at bottom** = Functions consuming most time
2. **LLM API calls** = Should dominate (60-70% of total time is expected)
3. **JSON serialization** = Should be narrow (orjson optimization)
4. **NLP processing** = Should be 15-20% (spaCy model inference)
5. **Validation** = Should be <10% (fast checks)

**Expected Bottlenecks** (from audit predictions):
- `anthropic.messages.create()` or similar LLM calls: 60-70%
- `spacy.tokens.Doc.__call__()`: 15-20%
- `orjson.dumps()` / `orjson.loads()`: 2-3%
- Everything else: <10%

**Red Flags** (investigate if found):
- JSON operations >5% (orjson not working?)
- Validation >15% (inefficient validators?)
- File I/O >5% (should be cached)
- Regex compilation in hot path (should use @lru_cache)

---

## Caching Strategies

### 1. LLM Response Cache

**Location**: `statement_generator/src/infrastructure/cache/llm_cache.py`

**Configuration**:
```bash
# .env configuration
MKSAP_LLM_CACHE_ENABLED=1          # Enable/disable cache (1=enabled, 0=disabled)
MKSAP_LLM_CACHE_TTL=3600           # Time-to-live in seconds (default: 1 hour)
MKSAP_LLM_CACHE_MAXSIZE=10000      # Max cached responses
```

**How it works**:
- Cache key: MD5(prompt + model + temperature)
- TTL: 1 hour default (responses expire after 1 hour)
- Thread-safe: Uses `cachetools.TTLCache`
- Automatic: No code changes needed

**Expected impact**:
- First run: 0% benefit (cold cache)
- Re-run same questions: 5-15% speedup
- Similar questions: 3-8% speedup (partial cache hits)

**Cache statistics**:
```python
# View cache stats (if implemented)
from src.infrastructure.cache.llm_cache import LLMCache
cache = LLMCache()
print(f"Hits: {cache._hits}, Misses: {cache._misses}")
print(f"Hit rate: {cache._hits / (cache._hits + cache._misses) * 100:.1f}%")
```

### 2. NLP Document Cache

**Location**: `statement_generator/src/validation/nlp_utils.py`

**Implementation**:
```python
@lru_cache(maxsize=1000)
def nlp_cached(text: str) -> Optional["Doc"]:
    """Cache spaCy Doc objects by text hash."""
    nlp = get_nlp()
    if nlp is None:
        return None
    return nlp(text)
```

**How it works**:
- Caches parsed spaCy Doc objects
- Max 1000 documents (~10-20MB memory)
- LRU eviction (least recently used)
- Automatic: Validators use `nlp_cached()` instead of `nlp()`

**Expected impact**:
- 30-40% cache hit rate (many similar medical phrases)
- 5-10% overall speedup on validators

### 3. Text Normalization Cache

**Location**: `statement_generator/src/processing/normalization/text_normalizer.py`

**Implementation**:
```python
@lru_cache(maxsize=1000)
def normalize_text(text: str) -> str:
    """Cache normalized text results."""
    # Normalization logic
    return normalized
```

**Expected impact**: 3-5% speedup on repeated text patterns

### 4. Regex Pattern Cache

**Best Practice**: Compile regex patterns once and cache:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_pattern(pattern_str: str) -> re.Pattern:
    """Cache compiled regex patterns."""
    return re.compile(pattern_str)

# Usage
pattern = get_pattern(r'\b(medication|drug)\b')
matches = pattern.findall(text)
```

---

## Async LLM Implementation (Not Operational)

**Status**: Infrastructure exists but not integrated into pipeline.

**What exists**:
- `BaseLLMProvider.generate_async()` method
- `AnthropicProvider` async implementation
- `LLMCache` integration with async
- `aiohttp` dependency installed

**What's missing**:
- Pipeline is still synchronous (`process_question()` not `async def`)
- Extractors don't use async methods
- CLI doesn't use `asyncio.run()`
- No rate limit handling for concurrent requests

**Effort to enable**: 4-8 hours (convert pipeline, extractors, CLI to async)

**Expected speedup** (if enabled):
- With Anthropic API: 3-5x (concurrent LLM calls)
- With Codex CLI: Minimal (~1.2x, CLI has overhead)

**See**: [ASYNC_IMPLEMENTATION.md](../statement_generator/docs/ASYNC_IMPLEMENTATION.md) for full details.

---

## Parallel Testing with pytest-xdist

**Status**: ✅ Installed and available

**Usage**:
```bash
cd statement_generator

# Run tests on all CPU cores
pytest -n auto

# Run tests on 4 cores
pytest -n 4

# Run specific test file in parallel
pytest tests/processing/ -n auto
```

**Expected speedup**: 75% test time reduction on 4+ core machine

**Configuration** (optional):
```ini
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
addopts = "-n auto"  # Always use parallel by default
```

**Gotchas**:
- Tests must be independent (no shared state)
- Some fixtures may need `scope="session"` adjustments
- Output is less readable (use `-v` for better output)

---

## Benchmarking Guidelines

### Baseline Measurement

**Measure current performance before optimizations:**
```bash
cd /Users/Mitchell/coding/projects/MKSAP

# Baseline: 10 questions
time ./scripts/python -m src.interface.cli process --limit 10

# Record results:
# - Total time (seconds)
# - Time per question (total / 10)
# - Memory usage (Activity Monitor or `top`)
```

### A/B Testing

**Compare before/after for specific optimizations:**
```bash
# 1. Disable cache (baseline)
MKSAP_LLM_CACHE_ENABLED=0 time ./scripts/python -m src.interface.cli process --limit 10

# 2. Enable cache (optimized)
MKSAP_LLM_CACHE_ENABLED=1 time ./scripts/python -m src.interface.cli process --limit 10

# Calculate speedup
# Speedup = baseline_time / optimized_time
```

### Full Batch Projection

**Estimate time for 2,198 questions:**
```python
# Based on 10-question sample
sample_time = 870  # seconds for 10 questions
per_question = sample_time / 10  # 87 seconds/question
total_questions = 2198
estimated_total = per_question * total_questions / 3600  # hours

print(f"Estimated time: {estimated_total:.1f} hours")
# Example: 87 seconds/question × 2198 = 53.1 hours baseline
```

### Performance Targets

**Current Performance** (January 2026, with optimizations):
- ~87 seconds per question (sequential processing)
- ~53 hours for full 2,198 questions

**Target Performance** (with async enabled):
- ~20-30 seconds per question (3-5x speedup)
- ~12-18 hours for full 2,198 questions

---

## Memory Optimization

### Current Memory Usage

**Baseline** (per question):
- spaCy model: ~100MB (loaded once, shared)
- NLP cache: ~10-20MB (1000 documents)
- LLM cache: ~5-10MB (depends on usage)
- Working memory: ~50-100MB

**Total**: ~200-300MB for full pipeline

### Memory Monitoring

```bash
# macOS
/usr/bin/time -l ./scripts/python -m src.interface.cli process --limit 10
# Look for "maximum resident set size"

# Linux
/usr/bin/time -v ./scripts/python -m src.interface.cli process --limit 10
# Look for "Maximum resident set size"
```

### Memory Optimization Techniques

**1. NLP Model Selection**:
- ✅ Using `en_core_sci_sm` (13MB) - optimal choice
- Avoid `en_core_sci_lg` (800MB) - too large, minimal benefit

**2. Cache Tuning**:
```python
# Reduce cache sizes if memory constrained
NLP_CACHE_MAXSIZE = 500  # Down from 1000
LLM_CACHE_MAXSIZE = 5000  # Down from 10000
```

**3. Batch Processing**:
- Process questions in batches of 100-200
- Clear caches between batches if needed
- Restart process every 500 questions (prevent memory leaks)

---

## Performance Monitoring in Production

### Logging Performance Metrics

**Add timing to pipeline**:
```python
import time
import logging

logger = logging.getLogger(__name__)

def process_question(self, question_file):
    start = time.time()

    # Processing logic
    result = self._process(question_file)

    elapsed = time.time() - start
    logger.info(f"Processed {question_file.name} in {elapsed:.2f}s")

    return result
```

### Checkpoints for Long Runs

**Monitor progress every 100 questions**:
```python
if question_count % 100 == 0:
    logger.info(f"Progress: {question_count}/2198 ({question_count/2198*100:.1f}%)")
    logger.info(f"Average: {total_time/question_count:.2f}s per question")
    logger.info(f"ETA: {(2198-question_count) * (total_time/question_count) / 3600:.1f} hours")
```

### Alert on Performance Degradation

**Detect slowdowns**:
```python
# Alert if processing time exceeds 2x baseline
BASELINE_TIME = 87  # seconds per question
if elapsed > BASELINE_TIME * 2:
    logger.warning(f"Slow processing detected: {elapsed:.2f}s (baseline: {BASELINE_TIME}s)")
```

---

## Troubleshooting Performance Issues

### Symptom: Slower than expected

**Check**:
1. Is LLM cache enabled? `MKSAP_LLM_CACHE_ENABLED=1`
2. Is NLP model loaded? Check logs for "Loading NLP model"
3. Are optimizations enabled? Check `orjson` imported, not `json`
4. Profile with py-spy to identify bottleneck

### Symptom: Memory errors

**Check**:
1. NLP cache size (reduce `maxsize` if needed)
2. LLM cache size (reduce or disable)
3. Process in smaller batches
4. Restart every 500 questions

### Symptom: API rate limits

**Check**:
1. Are you using async? (Would cause burst requests)
2. Add rate limiting: `time.sleep(1)` between questions
3. Use exponential backoff in providers

---

## Future Optimization Opportunities

### Short-term (1-2 days)

1. **Batch LLM calls** (if provider supports):
   - Send multiple prompts in single API call
   - Expected: 20-30% speedup

2. **Optimize validators**:
   - Profile and optimize slow validators
   - Use fuzzy matching libraries (`rapidfuzz` instead of custom)
   - Expected: 5-10% speedup

3. **Persistent cache** (Redis or disk):
   - Cache survives process restarts
   - Share cache across multiple runs
   - Expected: 10-20% speedup on re-runs

### Medium-term (1-2 weeks)

1. **Enable async LLM calls**:
   - Convert pipeline to async
   - Use `asyncio.gather()` for concurrent calls
   - Expected: 3-5x speedup

2. **Multiprocessing**:
   - Process questions in parallel (different processes)
   - Use `multiprocessing.Pool` with 4-8 workers
   - Expected: 3-4x speedup (on multi-core)

3. **GPU acceleration** (if using transformers):
   - Use CUDA for NLP inference
   - Expected: 2-3x speedup on NLP portion

### Long-term (1+ months)

1. **Model distillation**:
   - Train smaller, faster models
   - Compress spaCy model for faster inference

2. **Incremental processing**:
   - Only process changed questions
   - Smart checkpoint/resume with change detection

3. **Distributed processing**:
   - Process across multiple machines
   - Use Celery or similar task queue

---

## Performance Testing Checklist

Before deploying to production:

- [ ] Profile with py-spy to confirm bottlenecks
- [ ] Measure baseline (10 questions, no optimizations)
- [ ] Measure with optimizations (10 questions, all enabled)
- [ ] Calculate speedup ratio (baseline / optimized)
- [ ] Test cache hit rates (run same questions twice)
- [ ] Verify memory usage acceptable (<500MB)
- [ ] Test parallel pytest execution works
- [ ] Document actual performance numbers
- [ ] Estimate time for full 2,198 questions
- [ ] Set up monitoring/alerting for production run

---

## Related Documentation

- [ASYNC_IMPLEMENTATION.md](../statement_generator/docs/ASYNC_IMPLEMENTATION.md) - Async infrastructure details
- [CODING_STANDARDS.md](CODING_STANDARDS.md) - Performance best practices section
- [Audit Summary](../statement_generator/artifacts/AUDIT_IMPLEMENTATION_SUMMARY.md) - What was optimized
- [Phase 4 Deployment Plan](../statement_generator/docs/deployment/PHASE4_DEPLOYMENT_PLAN.md) - Production strategy

---

**Last Updated**: January 23, 2026
**Next Review**: After Phase 4 production run completion
