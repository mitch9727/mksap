# Statement Generator Improvements - December 28, 2025

## Summary of Changes

This document tracks improvements made after initial testing with question `givdx24022`.

---

## 1. Anti-Hallucination Constraints ✅ COMPLETE

**Problem**: LLM added medical knowledge not present in source text
- Example: Generated "intersecting linear ulcers separated by edematous mucosa" when source only mentioned "cobblestone mucosal appearance"

**Solution**: Updated all 3 prompt templates with strict source-fidelity constraints

**Files Changed**:
- `prompts/critique_extraction.md`
- `prompts/keypoints_extraction.md`
- `prompts/cloze_identification.md` (no changes needed - doesn't generate statements)

**Changes Made**:
1. Added top-level warning in prompts:
   ```
   CRITICAL: Extract ONLY information explicitly stated in the source text below.
   Do NOT add medical knowledge from outside the text.
   Do NOT explain mechanisms unless the text provides them.
   Stay faithful to the source.
   ```

2. Updated INSTRUCTIONS section:
   - Added **SOURCE-FAITHFUL** constraint
   - Added **NO HALLUCINATION** constraint
   - Modified extra_field instruction: "using only information from the critique"
   - Added: "If the critique doesn't explain 'why' or 'how', don't add it"

**Testing**: Pending - need to re-run `givdx24022` to verify reduced hallucination

---

## 2. Provider Fallback Chain 🚧 IN PROGRESS

**Problem**: No fallback when hitting usage limits with primary provider

**Solution**: Multi-provider fallback system with user confirmation

**Architecture**:
```
Provider Priority:
1. claude-code (CLI, free with subscription) ← DEFAULT
2. anthropic (API, pay-per-use)
3. gemini (CLI, if available)
4. codex (CLI/API, if available)
```

**New Files Created**:
1. `src/provider_exceptions.py` - Custom exception types
   - `ProviderLimitError` - Rate limits, quota exceeded
   - `ProviderAuthError` - Authentication failures
   - `ProviderError` - General errors

2. `src/provider_manager.py` - Fallback orchestration
   - Manages provider initialization
   - Detects limit errors
   - Prompts user before switching providers
   - Provides cost warnings (e.g., "Anthropic API is pay-per-use")

**Files Modified**:
1. `src/providers/claude_code_provider.py`
   - Added error detection for rate limits, budgets, auth failures
   - Raises `ProviderLimitError` on quota errors
   - Raises `ProviderAuthError` on login failures

2. `src/providers/anthropic_provider.py`
   - Added error detection for `RateLimitError`, `AuthenticationError`
   - Raises custom exceptions for fallback system
   - Checks error messages for quota/budget keywords

**User Experience**:
```
⚠️  PROVIDER LIMIT REACHED: claude-code
   Next provider: anthropic
⚠️  Note: Anthropic API is pay-per-use (approximately $0.01-0.02 per question)

Switch to next provider? [y/N]:
```

**Integration**: Need to update `main.py` to use `ProviderManager` instead of `ClaudeClient` directly

**Status**: Core implementation complete, pending integration and testing

---

## 3. Prompt Template Fixes ✅ COMPLETE

**Problem**: Python `.format()` tried to interpret JSON braces as placeholders

**Solution**: Escaped all JSON braces in examples with `{{` and `}}`

**Files Changed**:
- `prompts/critique_extraction.md`
- `prompts/keypoints_extraction.md`
- `prompts/cloze_identification.md`

**Example**:
```markdown
# Before (caused KeyError)
{
  "statements": [...]
}

# After (works correctly)
{{
  "statements": [...]
}}
```

**Testing**: ✅ Verified working with `givdx24022`

---

## 4. Claude Code Provider Fixes ✅ COMPLETE

**Problem**: Used unsupported CLI flags (`--temperature`, `--file`, `--output`)

**Solution**: Updated to use correct Claude CLI syntax

**Changes**:
- Removed `--temperature` flag (not supported by Claude CLI)
- Removed temporary file approach
- Changed to: `claude --print --model sonnet "prompt"`
- Added documentation note about unsupported parameters
- Removed unused imports (`tempfile`, `Path`)

**Testing**: ✅ Verified working with `givdx24022`

---

## 5. Default Provider Change ⏳ PENDING

**Current State**: Defaults to `anthropic` (requires API key)

**Proposed Change**: Default to `claude-code` (free with subscription)

**Rationale**:
- Most users have Claude Code subscription
- Avoids immediate API key requirement
- Only uses paid API when needed (via fallback)

**Files to Change**:
- `src/config.py` - Change default provider from "anthropic" to "claude-code"
- `src/config.py` - Change default model from "claude-sonnet-4-20250514" to "sonnet"

**Status**: On hold pending provider manager integration

---

## 6. Checkpoint System Improvements ⏳ PENDING

**Problem 1**: Question marked as both processed AND failed
- Happened because earlier run failed, then succeeded
- `failed_questions` list never gets cleared

**Problem 2**: No way to re-process already-processed questions
- Useful for testing prompt changes
- Needed for regenerating statements with improved prompts

**Proposed Solutions**:

### 6.1 Clear Failed Status on Success
```python
def mark_processed(self, question_id: str, batch_save: bool = False) -> None:
    """Mark question as processed"""
    if question_id not in self._data.processed_questions:
        self._data.processed_questions.append(question_id)

    # NEW: Remove from failed list if present
    if question_id in self._data.failed_questions:
        self._data.failed_questions.remove(question_id)

    if not batch_save:
        self._save()
```

### 6.2 Add --force Flag
```python
@cli.command()
@click.option("--force", is_flag=True, help="Re-process even if already completed")
def process(force: bool, ...):
    # Skip checkpoint check if force=True
    if not force and skip_existing:
        if checkpoint.is_processed(question_file.stem):
            logger.info(f"Skipping {question_file.stem} - already processed")
            continue
```

**Status**: Pending implementation

---

## 7. Temperature Behavioral Hints ⏳ PENDING

**Problem**: Claude CLI doesn't support `--temperature` parameter

**Current Workaround**: Just removed the flag (not ideal)

**Proposed Solution**: Add behavioral hints in prompts

**Implementation**:
1. Add `TEMPERATURE=0.2` to `.env` file (global setting)
2. Update prompt templates to include temperature hint:
   ```
   RESPONSE STYLE:
   Generate responses with low variability (deterministic, factual).
   Prioritize consistency and accuracy over creativity.
   Temperature: {temperature} (0.0 = deterministic, 1.0 = creative)
   ```
3. Load temperature from env and inject into prompts via `.format()`

**Files to Change**:
- `.env` - Add `TEMPERATURE=0.2`
- `prompts/critique_extraction.md` - Add temperature hint
- `prompts/keypoints_extraction.md` - Add temperature hint
- `src/critique_processor.py` - Pass temperature to template
- `src/keypoints_processor.py` - Pass temperature to template

**Note**: This is a "soft" constraint - LLM may or may not respect it

**Status**: Pending implementation

---

## Testing Plan

### Phase 1: Anti-Hallucination Testing ⏳
1. Re-run `givdx24022` with updated prompts
2. Compare statements to original critique sentence-by-sentence
3. Verify no hallucinated mechanisms or facts
4. Check if extra_field stays within source bounds

### Phase 2: Provider Fallback Testing ⏳
1. Simulate rate limit error (mock or manual trigger)
2. Verify user prompt appears correctly
3. Test user declining fallback
4. Test user accepting fallback
5. Verify next provider initializes correctly

### Phase 3: Checkpoint Improvements ⏳
1. Test --force flag on already-processed question
2. Verify failed questions get cleared on success
3. Test resume behavior with mixed processed/failed states

### Phase 4: Integration Testing ⏳
1. Run on 5-10 questions from different systems
2. Verify consistent quality across questions
3. Check for any edge cases or errors
4. Validate checkpoint persistence

---

## Open Questions

1. **Hallucination Trade-off**: Should we allow *any* expansion, or strictly source-only?
   - Current decision: Strictly source-only
   - Rationale: Attribution, legal compliance, quality control

2. **Statement Validation**: Should we add post-generation validation?
   - Proposed: Add in Phase 2 (after basic extraction works well)
   - Simple keyword overlap check first
   - Advanced LLM validator later

3. **Multiple Statement Generation**: Generate multiple candidates, pick best?
   - Decision: No - too expensive, prompts should be good enough
   - Alternative: Single-shot with strict constraints

4. **Re-processing Strategy**: How to handle re-running with improved prompts?
   - Solution: Use --force flag for manual re-processing
   - Consider adding --regenerate-failed for failed questions only

---

## Next Steps (Priority Order)

1. ✅ **DONE**: Fix prompts to prevent hallucination
2. 🚧 **IN PROGRESS**: Complete provider fallback integration
3. ⏳ **TODO**: Test anti-hallucination with `givdx24022`
4. ⏳ **TODO**: Fix checkpoint system (clear failed on success)
5. ⏳ **TODO**: Add --force flag for re-processing
6. ⏳ **TODO**: Change default provider to claude-code
7. ⏳ **TODO**: Add temperature hints to prompts (optional)
8. ⏳ **TODO**: Run on 10 diverse questions for validation

---

## Metrics to Track

Once we start processing at scale:

- **Hallucination rate**: Manual review sample to check source fidelity
- **Statement count per question**: Average and distribution
- **Cloze candidates per statement**: Should average 2-5
- **Provider usage**: How often do we hit limits and fall back?
- **Processing time**: Average time per question
- **API costs**: Track spending on paid providers

---

**Last Updated**: December 28, 2025, 10:30 AM
**Status**: Anti-hallucination fixes complete, provider fallback in progress
