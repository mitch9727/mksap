# Phase 2 Status - Statement Generator

**Last Updated**: December 31, 2025
**Plan Reference**: Internal Claude plan (archived)

This document consolidates Phase 2 status notes captured on December 27-28, 2025.
Sources: `statement_generator/IMPLEMENTATION_STATUS.md`, `statement_generator/IMPROVEMENTS_SUMMARY.md`,
`statement_generator/PARALLEL_EXECUTION_FIX.md` (now consolidated).

---

## Implementation Status (December 27, 2025 Snapshot)

### 1. Project Structure (Complete)

```
statement_generator/
├── src/        (complete) CLI, config, models, pipeline steps, providers, IO
├── prompts/    (complete) Phase prompt templates
└── outputs/    (complete) Checkpoints and logs (auto-created on first run)
```

**Component status**:
- CLI + orchestration: complete
- Config + models: complete
- IO + checkpointing: complete
- Pipeline steps (critique → key points → cloze → pipeline): complete
- Providers: Anthropic complete; CLI providers need testing

### 2. Key Features

| Feature | Status | Notes |
|---------|--------|-------|
| Non-destructive updates | Complete | Adds `true_statements` field only |
| Multi-provider support | Complete | All 4 providers implemented |
| Checkpoint/resume | Complete | Atomic saves with batch support |
| Sequential processing | Complete | One question at a time |
| Stateless LLM calls | Needs verification | Verify for CLI providers |
| Filter by system/type | Complete | Implemented in CLI |
| Atomic writes | Complete | .tmp -> rename pattern for checkpoints |
| Error handling | Needs improvement | Basic retry, needs classification |
| CLI interface | Complete | All required commands and options |

### 3. Data Models (Complete)

```python
class Statement(BaseModel):
    statement: str
    extra_field: str
    cloze_candidates: List[str] = []

class TrueStatements(BaseModel):
    from_critique: List[Statement] = []
    from_key_points: List[Statement] = []

class QuestionData(BaseModel):
    question_id: str
    category: str
    critique: str
    key_points: List[str]
    educational_objective: Optional[str] = None
    # extra = "allow" preserves other fields

class ProcessingResult(BaseModel):
    question_id: str
    success: bool
    statements_extracted: int
    error: Optional[str] = None
    api_calls: int = 0

class CheckpointData(BaseModel):
    processed_questions: List[str] = []
    failed_questions: List[str] = []
    last_updated: str
```

---

## Needs Testing/Verification

### 1. Provider Implementations

**Anthropic Provider**:
- Implementation complete
- Retry logic with exponential backoff
- Needs integration test with real API
- Error classification could be improved

**Claude Code Provider**:
- Basic implementation
- Verify `--stateless` flag exists in Claude CLI
- Test subprocess error handling
- Verify temperature parameter support

**Gemini Provider**:
- Basic implementation
- Test CLI integration
- Verify model parameter format

**Codex Provider**:
- Basic implementation
- Test OpenAI CLI integration
- Verify model parameter format

### 2. Error Handling

**Current State**:
- Basic try/except in all components
- Exponential backoff in Anthropic provider
- Logging of errors

**Needs Improvement**:
- Error classification (transient vs permanent)
- Specific error messages per provider
- Rate limit detection and handling
- Timeout handling for slow LLM calls

### 3. Prompts

**Status**:
- All 3 prompt templates exist
- Follow flashcard best practices
- Validate prompt effectiveness with real questions

---

## Required Fixes

### High Priority

1. Verify CLI Provider `--stateless` Flag
   - Location: Claude Code provider implementation
   - Test: `claude ask --help | rg stateless`

2. Test All Providers
   ```bash
   # Test Anthropic
   python -m src.main process --provider anthropic --question-id cvmcq24001 --dry-run

   # Test Claude Code
   python -m src.main process --provider claude-code --question-id cvmcq24001 --dry-run

   # Test Gemini
   python -m src.main process --provider gemini --question-id cvmcq24001 --dry-run

   # Test Codex
   python -m src.main process --provider codex --question-id cvmcq24001 --dry-run
   ```

3. Improve Error Classification
   - Add `_is_retryable(error)` per provider
   - Classify HTTP status codes (429, 500, 502, 503, 504 -> retryable)
   - Classify subprocess errors (timeout, connection reset -> retryable)

### Medium Priority

4. Add Validation Framework
   - Create a validation module
   - Check statement quality (atomicity, precision)
   - Detect vague language ("often", "usually", "may")
   - Validate cloze candidates (2-5 per statement)

5. Add Unit Tests
   - Model validation tests (Pydantic)
   - Provider tests (mock LLM calls)
   - Pipeline tests (end-to-end with mocks)

### Low Priority

6. Documentation
   - Add provider-specific troubleshooting to reference docs
   - Document expected costs per provider
   - Add example output to reference docs

7. Performance Monitoring
   - Track token usage per question
   - Estimate costs during dry-run
   - Log processing time per step

---

## Testing Checklist

### Unit Tests
- [ ] Test Statement model validation
- [ ] Test TrueStatements model validation
- [ ] Test QuestionData with extra fields
- [ ] Test CheckpointData serialization
- [ ] Mock Anthropic provider (no API calls)
- [ ] Mock Claude Code provider (no subprocess)
- [ ] Mock Gemini provider
- [ ] Mock Codex provider
- [ ] Test pipeline with mock LLM client

### Integration Tests
- [ ] Run single question with Anthropic (cvmcq24001)
- [ ] Verify JSON output structure
- [ ] Test checkpoint save/load
- [ ] Test resume after interrupt (Ctrl+C)
- [ ] Test skip-existing flag
- [ ] Test system filter (--system cv)
- [ ] Test dry-run mode

### Provider-Specific Tests
- [ ] Anthropic: Real API call with valid key
- [ ] Anthropic: Retry on rate limit (429)
- [ ] Claude Code: CLI availability check
- [ ] Claude Code: --stateless flag verification
- [ ] Gemini: CLI availability check
- [ ] Gemini: Model parameter format
- [ ] Codex: CLI availability check
- [ ] Codex: Model parameter format

### End-to-End Tests
- [ ] Process 10 questions from cv system
- [ ] Verify all have true_statements added
- [ ] Check no original data was lost
- [ ] Verify atomic writes (no .tmp files left)
- [ ] Check checkpoint accuracy
- [ ] Resume from checkpoint works

---

## Alignment with Original Plan

### Design Principles - All Preserved

| Principle | Original Rust Plan | Python Implementation |
|-----------|-------------------|----------------------|
| Non-destructive | Yes | Yes (`augment_with_statements`) |
| Sequential | Yes | Yes (no concurrency) |
| Multi-provider | Yes | Yes (anthropic, claude-code, gemini, codex) |
| Resumable | Yes | Yes (atomic saves with batch) |
| Stateless | Yes | Needs verification |
| Filters | Yes | Yes (CLI flags) |
| Atomic writes | Yes | Yes (checkpoints) |
| Error handling | Yes | Needs improvement |
| Validation | Yes | Not implemented yet |

### Architecture - Functionally Equivalent

| Component | Rust Plan | Python Reality |
|-----------|-----------|----------------|
| Provider abstraction | Trait | ABC |
| Config management | Structs | Pydantic |
| Error handling | anyhow::Result | try/except |
| Async | Tokio | Sync (simpler) |
| CLI | Clap | Click |
| Logging | tracing | logging |
| Testing | cargo test | pytest (pending) |

---

## Next Steps

### Immediate (Next Session)

1. Test provider implementations with a single question
2. Verify CLI flags for claude-code, gemini, codex
3. Run end-to-end test with cvmcq24001

### Short-term (Next 1-2 days)

4. Add error classification to all providers
5. Create unit tests for models and providers
6. Run small batch (10 questions) for quality check

### Medium-term (Next week)

7. Production run all 2,198 questions
8. Implement validation framework
9. Document provider comparisons

---

## Key Insights (December 27, 2025)

### Why Python vs Rust Worked

1. Faster development (no compile time)
2. Simpler CLI integration (subprocess for existing CLIs)
3. Pydantic validation for type safety
4. Click framework for CLI
5. Easier debugging

### Differences from Plan

1. No concurrency (sequential is sufficient)
2. Sync instead of async (Tokio not needed)
3. No path dependencies (pip install)
4. CLI providers prioritized (use existing subscriptions)

---

## Improvements Summary (December 28, 2025 Snapshot)

### 1. Anti-Hallucination Constraints (Complete)

**Problem**: LLM added medical knowledge not present in source text
- Example: Generated "intersecting linear ulcers separated by edematous mucosa" when source only mentioned "cobblestone mucosal appearance"

**Solution**: Updated all 3 prompt templates with strict source-fidelity constraints

**Files Changed**:
- `prompts/critique_extraction.md`
- `prompts/keypoints_extraction.md`
- `prompts/cloze_identification.md` (no changes needed - does not generate statements)

**Changes Made**:
1. Added top-level warning in prompts:
   ```
   CRITICAL: Extract ONLY information explicitly stated in the source text below.
   Do NOT add medical knowledge from outside the text.
   Do NOT explain mechanisms unless the text provides them.
   Stay faithful to the source.
   ```

2. Updated INSTRUCTIONS section:
   - Added SOURCE-FAITHFUL constraint
   - Added NO HALLUCINATION constraint
   - Modified extra_field instruction: "using only information from the critique"
   - Added: "If the critique doesn't explain 'why' or 'how', don't add it"

**Testing**: Pending - re-run `givdx24022` to verify reduced hallucination

---

### 2. Provider Fallback Chain (Integrated, Needs Testing)

**Problem**: No fallback when hitting usage limits with primary provider

**Solution**: Multi-provider fallback system with user confirmation

**Architecture**:
```
Provider Priority:
1. claude-code (CLI, free with subscription) - default
2. codex (CLI/API, if available)
3. anthropic (API, pay-per-use)
4. gemini (CLI, if available)
```

**New Components Created**:
1. Provider exception types
   - `ProviderLimitError` - Rate limits, quota exceeded
   - `ProviderAuthError` - Authentication failures
   - `ProviderError` - General errors

2. Provider manager (fallback orchestration)
   - Manages provider initialization
   - Detects limit errors
   - Prompts user before switching providers
   - Provides cost warnings

**Components Modified**:
1. Claude Code provider implementation
   - Added error detection for rate limits, budgets, auth failures
   - Raises `ProviderLimitError` on quota errors
   - Raises `ProviderAuthError` on login failures

2. Anthropic provider implementation
   - Added error detection for `RateLimitError`, `AuthenticationError`
   - Raises custom exceptions for fallback system
   - Checks error messages for quota/budget keywords

**User Experience**:
```
WARNING: PROVIDER LIMIT REACHED: claude-code
Next provider: anthropic
Note: Anthropic API is pay-per-use (approximately $0.01-0.02 per question)

Switch to next provider? [y/N]:
```

**Integration**: Statement generator CLI uses `ProviderManager` for processing

**Status**: Integrated, testing pending

---

### 3. Prompt Template Fixes (Complete)

**Problem**: Python `.format()` tried to interpret JSON braces as placeholders

**Solution**: Escaped all JSON braces in examples with `{{` and `}}`

**Files Changed**:
- `prompts/critique_extraction.md`
- `prompts/keypoints_extraction.md`
- `prompts/cloze_identification.md`

**Testing**: Verified working with `givdx24022`

---

### 4. Claude Code Provider Fixes (Complete)

**Problem**: Used unsupported CLI flags (`--temperature`, `--file`, `--output`)

**Solution**: Updated to use correct Claude CLI syntax

**Changes**:
- Removed `--temperature` flag (not supported by Claude CLI)
- Removed temporary file approach
- Changed to: `claude --print --model sonnet "prompt"`
- Added documentation note about unsupported parameters
- Removed unused imports (`tempfile`, `Path`)

**Testing**: Verified working with `givdx24022`

---

### 5. Default Provider Change (Pending)

**Current State**: Defaults to `anthropic` (requires API key)

**Proposed Change**: Default to `claude-code` (free with subscription)

**Rationale**:
- Most users have Claude Code subscription
- Avoids immediate API key requirement
- Only uses paid API when needed (via fallback)

**Configuration Updates**:
- Change default provider from "anthropic" to "claude-code"
- Change default model from "claude-sonnet-4-20250514" to "sonnet"

**Status**: On hold pending provider testing and decision

---

### 6. Checkpoint System Improvements (Complete, Needs Testing)

**Problem 1**: Previously marked as both processed AND failed
- Failed list never cleared

**Problem 2**: Previously no way to re-process already-processed questions
- Needed for testing prompt changes

**Implementation**:

#### 6.1 Clear Failed Status on Success
```python
def mark_processed(self, question_id: str, batch_save: bool = False) -> None:
    if question_id not in self._data.processed_questions:
        self._data.processed_questions.append(question_id)

    # Remove from failed list if present
    if question_id in self._data.failed_questions:
        self._data.failed_questions.remove(question_id)

    if not batch_save:
        self._save()
```

#### 6.2 Add --force Flag
```python
@click.option("--force", is_flag=True, help="Re-process even if already completed")
def process(force: bool, ...):
    if not force and skip_existing:
        if checkpoint.is_processed(question_file.stem):
            logger.info(f"Skipping {question_file.stem} - already processed")
            continue
```

**Status**: Implemented, testing pending

---

### 7. Temperature Behavioral Hints (Pending)

**Problem**: Claude CLI does not support `--temperature`

**Proposed Solution**: Add behavioral hints in prompts

**Implementation**:
1. Add `TEMPERATURE=0.2` to `.env` file
2. Update prompt templates to include temperature hint
3. Inject temperature via `.format()`

**Changes to Apply**:
- Environment configuration: add `TEMPERATURE=0.2`
- Prompt templates: add temperature hint for critique + key points
- Critique/key point processing steps: pass temperature into templates

**Status**: Pending implementation

---

## Testing Plan (December 28, 2025)

### Phase 1: Anti-Hallucination Testing
1. Re-run `givdx24022` with updated prompts
2. Compare statements to original critique sentence-by-sentence
3. Verify no hallucinated mechanisms or facts
4. Check if extra_field stays within source bounds

### Phase 2: Provider Fallback Testing
1. Simulate rate limit error (mock or manual trigger)
2. Verify user prompt appears correctly
3. Test user declining fallback
4. Test user accepting fallback
5. Verify next provider initializes correctly

### Phase 3: Checkpoint Improvements
1. Test --force flag on already-processed question
2. Verify failed questions get cleared on success
3. Test resume behavior with mixed processed/failed states

### Phase 4: Integration Testing
1. Run on 5-10 questions from different systems
2. Verify consistent quality across questions
3. Check for any edge cases or errors
4. Validate checkpoint persistence

---

## Open Questions (December 28, 2025)

1. Hallucination trade-off: allow any expansion, or strictly source-only?
   - Current decision: Strictly source-only
   - Rationale: Attribution, legal compliance, quality control

2. Statement validation: add post-generation validation?
   - Proposed: Add after basic extraction works well
   - Simple keyword overlap check first
   - Advanced LLM validator later

3. Multiple statement generation: generate multiple candidates, pick best?
   - Decision: No (too expensive)
   - Alternative: Single-shot with strict constraints

4. Re-processing strategy: how to handle re-running with improved prompts?
   - Solution: Use --force flag for manual re-processing
   - Consider adding --regenerate-failed for failed questions only

---

## Next Steps (Priority Order)

1. DONE: Fix prompts to prevent hallucination
2. IN PROGRESS: Complete provider fallback integration
3. TODO: Test anti-hallucination with `givdx24022`
4. TODO: Fix checkpoint system (clear failed on success)
5. TODO: Add --force flag for re-processing
6. TODO: Change default provider to claude-code
7. TODO: Add temperature hints to prompts (optional)
8. TODO: Run on 10 diverse questions for validation

---

## Metrics to Track

Once processing runs at scale:

- Hallucination rate (manual review sample)
- Statement count per question (average and distribution)
- Cloze candidates per statement (target 2-5)
- Provider usage (fallback frequency)
- Processing time per question
- API costs for paid providers

---

## Parallel Execution Fix - Provider-Specific Checkpoints

**Enables**: Running multiple providers in parallel on the same questions

### Changes Required

1) Modify the checkpoint manager

```python
class CheckpointManager:
    """Manage processing checkpoints for resumability"""

    def __init__(self, checkpoint_path: Path, provider: str = "default"):
        self.checkpoint_file = checkpoint_path / f"{provider}_processed.json"
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()
```

2) Modify the CLI process command

```python
@cli.command()
def process(...):
    checkpoint = CheckpointManager(
        config.paths.checkpoints,
        provider=config.llm.provider
    )
```

3) Test

```bash
# Terminal 1: Anthropic
python -m src.main process --provider anthropic --mode production

# Terminal 2: Claude Code
python -m src.main process --provider claude-code --mode production

# Each creates separate checkpoint:
# - outputs/checkpoints/anthropic_processed.json
# - outputs/checkpoints/claude-code_processed.json
```

### Result

- Safe parallel execution across providers
- Each provider tracks its own progress
- Can compare outputs across providers
- Minimal code changes (2 lines)
