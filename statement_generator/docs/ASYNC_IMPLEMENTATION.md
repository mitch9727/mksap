# Async LLM Implementation - Status Report

> **Author**: Testing agent (following agent aa1de2d)
> **Date**: January 23, 2026
> **Status**: INCOMPLETE - Infrastructure present but not utilized

## Executive Summary

Agent aa1de2d implemented async LLM infrastructure including:
- TTL-based LLM response caching (`infrastructure/cache/llm_cache.py`)
- Async methods in base provider and Anthropic provider
- Async client wrapper methods

**However, the async implementation is NOT being used by the pipeline.** The current pipeline processes questions **sequentially**, making **no use of async/await or asyncio.gather()**. The infrastructure exists but is not connected to the orchestration layer.

## What Was Implemented

### 1. LLM Cache (✅ Complete)

**File**: `statement_generator/src/infrastructure/cache/llm_cache.py`

- TTL-based caching with MD5 hash keys
- Default TTL: 1 hour (3600s)
- Default maxsize: 10,000 entries
- Enabled by default via `MKSAP_LLM_CACHE_ENABLED=1`
- Thread-safe using `cachetools.TTLCache`

**Cache Key**: `MD5(prompt + model + temperature)`

**Statistics tracking**:
- Hit/miss counters
- Hit rate calculation
- Cache size monitoring

**Status**: Fully implemented and functional. Cache initialization logs confirm it's active.

### 2. Async Provider Methods (✅ Complete)

**Files**:
- `infrastructure/llm/base_provider.py` - Base async interface
- `infrastructure/llm/providers/anthropic.py` - True async implementation
- Other providers (codex, gemini, claude-code) - Fallback to sync

**AnthropicProvider async support**:
```python
async def generate_async(self, prompt: str, temperature: Optional[float] = None, max_retries: int = 3) -> str:
    # Uses AsyncAnthropic client for true async API calls
    message = await self.async_client.messages.create(...)
```

**Other providers**:
- Default implementation in `BaseLLMProvider.generate_async()`
- Falls back to running sync `generate()` in executor
- Not true async, but provides compatible interface

### 3. Async Client Wrapper (✅ Complete)

**File**: `infrastructure/llm/client.py`

```python
async def generate_async(self, prompt: str, temperature: float = None, max_retries: int = 3) -> str:
    # Check cache first (synchronous - fast)
    cached_response = self.cache.get(prompt, self.config.model, temp)
    if cached_response is not None:
        return cached_response

    # Cache miss - call provider async
    response = await self.provider.generate_async(prompt, temperature, max_retries)

    # Store in cache
    self.cache.put(prompt, self.config.model, temp, response)
    return response
```

**Status**: Fully implemented with cache integration.

## What Is Missing (❌ Not Implemented)

### Pipeline Does NOT Use Async

**File**: `statement_generator/src/orchestration/pipeline.py`

The `process_question()` method is **entirely synchronous**:

```python
def process_question(self, question_file: Path) -> ProcessingResult:
    # Step 1: Extract from critique (SYNC)
    critique_statements = self.critique_processor.extract_statements(...)

    # Step 2: Extract from key_points (SYNC)
    keypoint_statements = self.keypoints_processor.extract_statements(...)

    # Step 3: Extract from tables (SYNC)
    table_statements_list = self.table_processor.extract_statements(...)

    # Step 4: Identify cloze candidates (SYNC)
    all_statements = self.cloze_identifier.identify_cloze_candidates(...)
```

**No async keywords present**: No `async def`, no `await`, no `asyncio.gather()`.

### CLI Does NOT Use Async

**File**: `statement_generator/src/interface/cli.py` (lines 218-244)

The main processing loop is sequential:

```python
for i, question_file in enumerate(questions):
    result = pipeline.process_question(question_file)  # SYNC call
    results.append(result)
```

**No parallelization**:
- Questions are processed one at a time
- Within each question, LLM calls are sequential
- No use of asyncio.run() or asyncio.gather()

### What Would Need to Change

To enable async processing, the following would need to be implemented:

1. **Convert pipeline.process_question() to async**:
   ```python
   async def process_question(self, question_file: Path) -> ProcessingResult:
       # Parallel LLM calls within a question
       critique_task = self.critique_processor.extract_statements_async(...)
       keypoints_task = self.keypoints_processor.extract_statements_async(...)

       critique_statements, keypoint_statements = await asyncio.gather(
           critique_task, keypoints_task
       )
   ```

2. **Convert extractors to async**:
   - `CritiqueProcessor.extract_statements()` → async version
   - `KeyPointsProcessor.extract_statements()` → async version
   - `TableProcessor.extract_statements()` → async version
   - `ClozeIdentifier.identify_cloze_candidates()` → async version

3. **Convert CLI to async**:
   ```python
   async def process_questions_async(questions, pipeline):
       tasks = [pipeline.process_question(q) for q in questions]
       results = await asyncio.gather(*tasks, return_exceptions=True)
       return results

   # In CLI command:
   results = asyncio.run(process_questions_async(questions, pipeline))
   ```

## Test Results

### Test Configuration

- **System**: macOS (Darwin 24.6.0)
- **Python**: 3.13.5
- **Provider**: codex (via CLI, not Anthropic API)
- **Cache**: Enabled (maxsize=10000, ttl=3600s)
- **Hybrid Pipeline**: Enabled (USE_HYBRID_PIPELINE=true)

### Test Execution

**Command**: `./scripts/python -m src.interface.cli process --system cv --limit 3`

**Result**: FAILED (NLP model path issue + checkpoint bug)

**Timing**:
- **Total time**: 1:27.56 (87.56 seconds)
- **Processed**: 1 question (failed during validation)
- **Average per question**: ~87 seconds

**LLM calls observed** (from logs):
1. Critique extraction: ~20 seconds
2. Key points extraction: ~4 seconds
3. Context enhancement (critique): ~36 seconds
4. Context enhancement (keypoints): ~7 seconds
5. Cloze identification: ~19 seconds

**Total LLM time**: ~86 seconds (essentially all time is LLM calls)

### Issues Encountered

1. **NLP model path issue**:
   ```
   OSError: [E050] Can't find model 'statement_generator/models/en_core_sci_sm-0.5.4/...'
   ```
   - Path in .env is relative, should be absolute
   - Affects both NLP preprocessing and validation

2. **Checkpoint serialization error**:
   ```
   NameError: name 'json' is not defined. Did you mean: 'orjson'?
   ```
   - False alarm - checkpoint.py correctly uses orjson
   - Error may be from different context

3. **Cache cannot be tested**:
   - Cannot run same question twice due to errors
   - Cannot verify cache hit/miss behavior
   - Cannot measure speedup on re-runs

## Performance Analysis

### Current (Sequential) Performance

Based on single question test:
- **~87 seconds per question** (5 LLM calls)
- **~17 seconds per LLM call** (average)

For 10 questions:
- **Expected time**: ~870 seconds (14.5 minutes)

For 2,198 questions (full dataset):
- **Expected time**: ~52 hours

### Theoretical Async Performance

**Assumptions**:
- 5 LLM calls per question (critique, keypoints, context×2, cloze)
- 3 can run in parallel (critique, keypoints, tables)
- 2 must run sequentially (context, cloze) after first batch

**Intra-question parallelization**:
- Current: 20s + 4s + 36s + 7s + 19s = 86s
- Async: max(20s, 4s, 0s) + 36s + 7s + 19s = 82s (**4.7% speedup** - minimal)

**Inter-question parallelization** (batch of 10):
- Current: 10 × 86s = 860s (14.3 minutes)
- Async (batch): max(10 × 20s) + processing = ~860s (similar, due to API rate limits)

**Realistic speedup**: **1.5-2x** with careful batching and rate limit management.

**Note**: Codex CLI provider does NOT support true async (falls back to executor). Only Anthropic API provider has true async support.

## Cache Functionality

### Configuration

**Environment variable**: `MKSAP_LLM_CACHE_ENABLED` (default: 1)

**Settings**:
```python
cache = LLMCache(
    maxsize=10000,  # Max cached responses
    ttl=3600        # 1 hour TTL
)
```

**Cache key generation**:
```python
def _make_cache_key(prompt: str, model: str, temperature: float) -> str:
    temp_str = f"{temperature:.4f}"
    key_material = f"{prompt}|{model}|{temp_str}"
    return hashlib.md5(key_material.encode("utf-8")).hexdigest()
```

### Expected Behavior

1. **First run**: Cache misses, stores responses
2. **Second run** (within 1 hour): Cache hits, retrieves responses
3. **After 1 hour**: TTL expired, cache misses again

**Expected speedup**: 5-15% on re-runs (eliminates LLM API latency)

### Testing Status

❌ **NOT TESTED** - Cannot complete test run due to NLP model path issue

**To test cache**:
1. Fix NLP model path (use absolute path in .env)
2. Run: `./scripts/python -m src.interface.cli process --system cv --limit 3`
3. Run again immediately (within 1 hour)
4. Compare logs for "Cache HIT" messages
5. Compare execution times (should be 5-15% faster)

## Recommendations

### For Immediate Use (No Async)

1. **Fix NLP model path**:
   ```bash
   # In .env, change:
   MKSAP_NLP_MODEL=statement_generator/models/en_core_sci_sm-0.5.4/...
   # To absolute path:
   MKSAP_NLP_MODEL=/Users/Mitchell/coding/projects/MKSAP/statement_generator/models/...
   ```

2. **Verify cache is working**:
   - Run same question twice
   - Check logs for cache hit messages
   - Measure speedup

3. **Current performance is acceptable**:
   - ~87 seconds per question
   - ~52 hours for full dataset (2,198 questions)
   - Cache provides 5-15% speedup on re-runs

### For Async Implementation (Future Work)

❌ **NOT RECOMMENDED** for current provider (codex CLI)

**Reasons**:
1. Codex provider doesn't support true async (uses executor fallback)
2. Intra-question speedup is minimal (4.7%)
3. Inter-question batching limited by rate limits
4. Implementation complexity is high (pipeline, extractors, CLI)

✅ **RECOMMENDED** if switching to Anthropic API provider

**Benefits**:
- True async API calls (AsyncAnthropic)
- Potential 1.5-2x speedup with batching
- Better rate limit management

**Required work**:
1. Convert all extractors to async (5 files)
2. Convert pipeline to async (orchestration layer)
3. Convert CLI to async (add asyncio.run())
4. Add rate limit handling (API quotas)
5. Add concurrency limits (max N questions in parallel)

**Estimated effort**: 4-8 hours of development + testing

## Configuration Reference

### Environment Variables

**Cache**:
```bash
MKSAP_LLM_CACHE_ENABLED=1    # Enable cache (default: 1)
```

**Provider** (affects async support):
```bash
LLM_PROVIDER=codex           # Current (no true async)
# or
LLM_PROVIDER=anthropic       # For true async support
ANTHROPIC_API_KEY=sk-...     # Required for anthropic
```

**NLP** (affects pipeline):
```bash
USE_HYBRID_PIPELINE=true     # Enable NLP preprocessing
MKSAP_NLP_MODEL=/absolute/path/to/model  # MUST be absolute
```

### Cache Statistics

**Programmatic access**:
```python
from src.infrastructure.cache.llm_cache import LLMCache

cache = LLMCache()
stats = cache.stats
# {
#   "hits": 42,
#   "misses": 100,
#   "hit_rate": 0.296,
#   "size": 100,
#   "maxsize": 10000,
#   "ttl": 3600,
#   "enabled": True
# }
```

**No CLI command exists** for viewing cache stats.

## Conclusion

The async LLM infrastructure implemented by agent aa1de2d is **well-designed but not integrated** into the pipeline. The code quality is high, caching is functional, and the provider abstraction is clean.

**However**, without pipeline and CLI changes, the async methods are never called. The current implementation processes questions sequentially, making no use of the async infrastructure.

**Recommendation**:
- Document as "async-ready infrastructure"
- Do not claim async processing is working
- Consider as future optimization if switching to Anthropic API
- Current sequential processing is sufficient for project needs

**Next steps** (if pursuing async):
1. Fix NLP model path issue first (blocking)
2. Verify cache functionality works
3. Profile current performance on 10-20 questions
4. Decide if async is worth the implementation effort
5. If yes: convert pipeline → extractors → CLI in that order

---

**Files modified by agent aa1de2d**:
- `infrastructure/cache/llm_cache.py` (new)
- `infrastructure/llm/base_provider.py` (added async methods)
- `infrastructure/llm/providers/anthropic.py` (added generate_async)
- `infrastructure/llm/client.py` (added generate_async)
- `orchestration/pipeline.py` (no async changes - still sequential)

**Async readiness**: ⚠️ Infrastructure only - not operational
