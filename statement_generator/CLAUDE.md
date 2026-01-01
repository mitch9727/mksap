# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**MKSAP Statement Generator** - Python-based LLM pipeline that extracts testable medical facts from MKSAP question critiques and key points, formatting them as cloze deletion flashcard statements following evidence-based spaced repetition best practices.

**Primary Language**: Python 3.9+
**Architecture**: 4-phase pipeline (critique extraction → key points extraction → cloze identification → text normalization)
**Status**: Phase 2 of 4-phase MKSAP project (Phase 1: Rust extractor complete, 2,198 questions)
**Design**: Multi-provider LLM abstraction (Anthropic API, Claude Code CLI, Gemini CLI, Codex CLI)

## Common Commands

### Running Statement Generation

```bash
# Test on 1-2 questions (default)
python -m src.main process --mode test --system cv

# Test specific question
python -m src.main process --question-id cvmcq24001

# Production: Process all 2,198 questions
python -m src.main process --mode production

# Use different provider (avoids API costs if you have subscription)
python -m src.main process --provider claude-code --mode test
python -m src.main process --provider gemini --mode test
python -m src.main process --provider codex --mode test

# Adjust creativity (default 0.2 minimizes hallucination)
python -m src.main process --temperature 0.5 --question-id cvmcq24001

# Re-process already completed questions
python -m src.main process --force --question-id cvmcq24001

# Preview without API calls
python -m src.main process --dry-run --system cv

# Debug logging
python -m src.main process --log-level DEBUG --question-id cvmcq24001
```

### Management Commands

```bash
# Show statistics
python -m src.main stats

# Reset checkpoints (fresh start)
python -m src.main reset

# Clean old log files (keeps last 7 days)
python -m src.main clean-logs
python -m src.main clean-logs --keep-days 3
python -m src.main clean-logs --dry-run

# Clean ALL logs and reset checkpoints
python -m src.main clean-all
```

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with debug logging
RUST_LOG=debug python -m src.main process --question-id cvmcq24001

# Test single question without saving
python -m src.main process --dry-run --question-id cvmcq24001
```

## High-Level Architecture

### 4-Phase Pipeline Design

The statement generator follows a **sequential, non-destructive pipeline** that augments existing question JSON files with `true_statements` field:

```
PHASE 1: Critique Extraction (critique_processor.py)
├─ Input: critique field (300-800 words of medical explanation)
├─ Prompt: prompts/critique_extraction.md
├─ Output: 3-7 atomic statements with optional extra_field (clinical context)
├─ Goal: Extract testable facts, maximize concept coverage
└─ Constraint: NO hallucination - extract ONLY what critique explicitly states

PHASE 2: Key Points Extraction (keypoints_processor.py)
├─ Input: key_points array (0-3 pre-formatted bullets)
├─ Prompt: prompts/keypoints_extraction.md
├─ Output: 1-3 refined statements
├─ Goal: Minimal rewriting (key_points are already high-quality)
└─ Constraint: Same anti-hallucination rules as Phase 1

PHASE 3: Cloze Identification (cloze_identifier.py)
├─ Input: All statements from Phase 1 + 2
├─ Prompt: prompts/cloze_identification.md
├─ Output: 2-5 cloze candidates per statement
├─ Goal: Identify testable terms for fill-in-the-blank flashcards
└─ Strategy: Modifier splitting (e.g., "mild" AND "hypercalcemia" as separate clozes)

PHASE 4: Text Normalization (text_normalizer.py)
├─ Input: All statements with cloze candidates
├─ Process: Convert verbose math to symbols
│   - "less than" → "<"
│   - "greater than" → ">"
│   - "approximately" → "~"
│   - "plus or minus" → "±"
├─ Output: Normalized statements
└─ Goal: Concise flashcards (less reading per review)

FINAL: JSON Augmentation (file_io.py)
├─ Add true_statements field to existing question JSON
├─ Preserve ALL original fields (non-destructive)
├─ Atomic write: read → augment → write
└─ Checkpoint: Mark question as processed
```

### Multi-Provider Abstraction

The system supports **4 LLM providers** via abstract base class pattern:

```
BaseLLMProvider (providers/base.py)
├─ Interface: generate(prompt, temperature, max_retries) -> str
├─ Interface: get_provider_name() -> str
└─ Implementations:
    ├─ AnthropicProvider (anthropic_provider.py)
    │   ├─ Uses: Anthropic API via anthropic Python SDK
    │   ├─ Requires: ANTHROPIC_API_KEY environment variable
    │   ├─ Features: Exponential backoff, retry on rate limit (429)
    │   └─ Best for: Production runs, reproducibility
    │
    ├─ ClaudeCodeProvider (claude_code_provider.py)
    │   ├─ Uses: Claude Code CLI via subprocess
    │   ├─ Requires: claude CLI installed
    │   ├─ Features: Uses existing Claude subscription (no API cost)
    │   └─ Best for: Development, testing, using existing subscription
    │
    ├─ GeminiProvider (gemini_provider.py)
    │   ├─ Uses: Gemini CLI via subprocess
    │   ├─ Requires: gemini CLI installed
    │   ├─ Features: Uses existing Google AI subscription
    │   └─ Best for: Alternative to Claude if rate limited
    │
    └─ CodexProvider (codex_provider.py)
        ├─ Uses: OpenAI CLI via subprocess
        ├─ Requires: openai CLI installed
        ├─ Features: Uses existing OpenAI subscription
        └─ Best for: Alternative provider, GPT-4 access
```

**Provider Selection Priority**:
1. CLI flag: `--provider <name>`
2. Environment variable: `LLM_PROVIDER=<name>`
3. Default: `anthropic`

**Why Multiple Providers**:
- Avoid API costs by using CLI-based subscriptions
- Fallback options if one provider rate limits
- Compare output quality across providers
- Use existing paid subscriptions instead of separate API keys

### Checkpoint/Resume System

**Design**: Atomic batch saves with resumability

```
CheckpointManager (checkpoint.py)
├─ File: outputs/checkpoints/processed_questions.json
├─ Format: {"processed_questions": [...], "failed_questions": [...]}
├─ Atomic writes: .tmp → rename (no partial state corruption)
├─ Batch saves: Every N questions (default: 10)
├─ Resume behavior:
│   ├─ Skip questions in processed_questions[] (unless --force)
│   ├─ Skip questions with existing true_statements (unless --overwrite)
│   └─ Retry questions in failed_questions[]
└─ Safe interrupt: Ctrl+C preserves last checkpoint
```

**Key Design Decision**: Checkpoints track question IDs, NOT JSON state. This allows:
- Manual JSON edits between runs (e.g., fix typos)
- Re-processing with `--force` flag
- Skipping questions that already have statements (faster resume)

### Non-Destructive JSON Updates

**Critical Principle**: NEVER modify existing fields, only add `true_statements`

```python
# file_io.py - augment_with_statements()
def augment_with_statements(data: dict, true_statements: TrueStatements) -> dict:
    """
    Add true_statements field without touching existing data.

    Preserves:
    - question_id, category, critique, key_points
    - All media metadata (figures, tables, videos, svgs)
    - All metadata (care_types, patient_types, etc.)
    - question_text, question_stem, options, user_performance
    - All other fields

    Adds:
    - true_statements: {
        "from_critique": [...],
        "from_key_points": [...]
      }
    """
    data["true_statements"] = true_statements.model_dump(exclude_none=True)
    return data
```

**Why This Matters**:
- Phase 1 (Rust extractor) output is sacred - never corrupt it
- Allows re-running statement generator without losing original data
- Multiple phases can augment same JSON sequentially
- Manual edits to questions won't be overwritten

### Evidence-Based Flashcard Design

All prompts follow research-backed principles from `best-practices-cloze-deletion-flashcards.md`:

1. **Atomic Facts** (Minimum Information Principle)
   - Each statement tests ONE concept
   - Simple cards scheduled farther apart (spaced repetition efficiency)
   - Example: "ACE inhibitors reduce proteinuria" (one mechanism)

2. **Anti-Hallucination Constraints**
   - Extract ONLY information explicitly stated in source
   - NO inference, NO external medical knowledge
   - Temperature 0.2 default (minimizes creativity)
   - Verification: extra_field = null when source doesn't explain WHY

3. **Modifier Splitting** (Innovative for Medical Learning)
   - "Mild hypercalcemia" → TWO cloze candidates: ["mild", "hypercalcemia"]
   - Tests both severity classification AND condition recognition
   - Example cards:
     - "[...] hypercalcemia is defined as..." → "mild"
     - "Mild [...] is defined as..." → "hypercalcemia"

4. **Clinical Context** (Extra Field)
   - ONLY add if source provides explanatory context
   - Explains WHY the fact matters clinically
   - Example: "ACE inhibitors cause cough" → extra: "via bradykinin accumulation"
   - If source only states fact without explanation, use null

5. **Concise Questions**
   - Strip unnecessary words
   - Remove patient-specific details ("this patient" → general principle)
   - Focus on essential trigger
   - Example: NOT "A 65-year-old male with...", YES "Low bone mass + hypercalcemia = [...]"

6. **Avoid Enumerations**
   - NO "List all 4 components of tetralogy of Fallot" in one card
   - YES: Overlapping chunked clozes (first 2 components, next 2 components)
   - Reduces card failure from forgetting one item

7. **Multiple Cloze Candidates**
   - 2-5 candidates per statement (maximizes learning efficiency)
   - Each candidate creates separate flashcard
   - Reduces total cards needed per concept

### Output Structure

Each question JSON gets augmented with:

```json
{
  "question_id": "cvmcq24001",
  "category": "cv",
  "critique": "...",
  "key_points": [...],
  "true_statements": {
    "from_critique": [
      {
        "statement": "ACE inhibitors are first-line therapy for hypertension in patients with chronic kidney disease.",
        "extra_field": "ACE inhibitors reduce proteinuria and slow CKD progression by reducing intraglomerular pressure.",
        "cloze_candidates": ["ACE inhibitors", "chronic kidney disease", "proteinuria"]
      }
    ],
    "from_key_points": [
      {
        "statement": "Initial management of chronic cough includes tobacco cessation and discontinuation of ACE inhibitor therapy.",
        "extra_field": null,
        "cloze_candidates": ["tobacco cessation", "ACE inhibitor"]
      }
    ]
  }
}
```

**Field Semantics**:
- `statement`: Complete sentence (NO [...] blanks yet - that's Phase 3 downstream)
- `extra_field`: Clinical context (why/how/significance) OR null if source doesn't provide
- `cloze_candidates`: List of terms to blank out in flashcards (2-5 per statement)

**Example Conversion to Flashcard** (happens in Phase 3 downstream):
```
Statement: "ACE inhibitors are first-line therapy for hypertension in patients with chronic kidney disease."
Cloze candidates: ["ACE inhibitors", "chronic kidney disease", "proteinuria"]

Generated flashcards:
1. "[...] are first-line therapy for hypertension in patients with CKD."
   Answer: ACE inhibitors
   Extra: ACE inhibitors reduce proteinuria and slow CKD progression

2. "ACE inhibitors are first-line therapy for hypertension in patients with [...]."
   Answer: chronic kidney disease
   Extra: (same)

3. "ACE inhibitors reduce [...] and slow CKD progression."
   Answer: proteinuria
   Extra: (same)
```

## Module Organization

### Core Pipeline Modules

**pipeline.py** - Orchestrates 4-phase workflow
- Coordinates: critique_processor → keypoints_processor → cloze_identifier → text_normalizer
- Reads question JSON, calls each processor, augments JSON, saves
- Returns: ProcessingResult with success/failure info

**critique_processor.py** - Step 1: Extract statements from critique
- Loads: prompts/critique_extraction.md
- Calls: LLM with critique + educational_objective
- Parses: JSON response → List[Statement]
- Validates: Each statement has required fields

**keypoints_processor.py** - Step 2: Extract statements from key_points
- Loads: prompts/keypoints_extraction.md
- Calls: LLM with key_points array
- Parses: JSON response → List[Statement]
- Handles: Empty key_points (returns empty list)

**cloze_identifier.py** - Step 3: Identify cloze candidates
- Loads: prompts/cloze_identification.md
- Calls: LLM with all statements from Steps 1+2
- Parses: JSON response → Updates Statement.cloze_candidates
- Validates: 2-5 candidates per statement

**text_normalizer.py** - Step 4: Normalize mathematical notation
- Pure Python transformation (no LLM call)
- Patterns: "less than" → "<", "greater than" → ">", etc.
- Preserves: Clinical language (e.g., "greater than normal" untouched)
- Operates on: Statement.statement and Statement.extra_field

### Infrastructure Modules

**main.py** - Click CLI entry point
- Commands: process, stats, reset, clean-logs, clean-all
- Coordinates: Config loading, provider setup, checkpoint management, batch processing
- Logging: Dual output (console + timestamped log file)

**config.py** - Pydantic configuration
- Loads: Project root .env file (../. env)
- Provides: LLMConfig, ProcessingConfig, PathsConfig
- Supports: Multi-provider configuration with CLI overrides

**file_io.py** - JSON file operations
- discover_all_questions() - Scan mksap_data/*/*.json
- discover_system_questions(system) - Filter by system code (cv, en, etc.)
- read_question() - Parse JSON with Pydantic validation
- write_question() - Atomic write with indentation
- augment_with_statements() - Non-destructive field addition
- has_true_statements() - Check if already processed

**checkpoint.py** - Resume state management
- Atomic writes: Write to .tmp, then rename
- Batch saves: Buffer writes, flush every N questions
- is_processed() - Check if question in checkpoint
- mark_processed() - Add to processed list (batch or immediate)
- mark_failed() - Track failures for retry
- reset() - Clear all checkpoint state

**llm_client.py** - Multi-provider client wrapper
- Wraps: Any BaseLLMProvider implementation
- Interface: generate(prompt, temperature) -> str
- Used by: All processor modules (critique, keypoints, cloze)

**provider_manager.py** - Provider fallback orchestration
- Primary provider with automatic fallback to alternatives
- Handles: ProviderLimitError, ProviderAuthError
- Logs: Provider switching for transparency

**models.py** - Pydantic data models
- Statement: {statement, extra_field, cloze_candidates}
- TrueStatements: {from_critique, from_key_points}
- ProcessingResult: {question_id, success, statements_extracted, error}
- CheckpointData: {processed_questions, failed_questions, last_updated}
- QuestionData: Validates input JSON (extra="allow" preserves all fields)

### Provider Implementations

**providers/base.py** - Abstract base class
- Interface: generate(prompt, temperature, max_retries) -> str
- Interface: get_provider_name() -> str

**providers/anthropic_provider.py** - Anthropic API
- SDK: anthropic Python package
- Auth: ANTHROPIC_API_KEY environment variable
- Retry: Exponential backoff on rate limit (429), server errors (5xx)
- Error handling: Non-retryable (401, 403, 404), retryable (429, 5xx, timeout)

**providers/claude_code_provider.py** - Claude Code CLI
- Command: subprocess.run(["claude", "ask", "--stateless", ...])
- Auth: Uses Claude subscription (no API key)
- Temperature: Passed as CLI argument (verify support)
- Stateless: Prevents context accumulation across calls

**providers/gemini_provider.py** - Gemini CLI
- Command: subprocess.run(["gemini", "ask", ...])
- Auth: Uses Google AI subscription
- Model: gemini-pro (configurable)

**providers/codex_provider.py** - OpenAI CLI
- Command: subprocess.run(["openai", "api", "completions.create", ...])
- Auth: Uses OpenAI subscription
- Model: gpt-4 (configurable)

## Critical Design Constraints

### Why Sequential Processing (No Concurrency)

**Decision**: Process one question at a time, no async/parallel processing

**Rationale**:
1. **LLM-bound workload**: Bottleneck is LLM response time (2-5 seconds), not CPU
2. **Simpler error handling**: No race conditions, easier to debug
3. **Checkpoint safety**: Atomic batch saves prevent state corruption
4. **Rate limit avoidance**: Sequential reduces chance of hitting provider limits
5. **Sufficient throughput**: 2,198 questions × 5 seconds/question = ~3 hours (acceptable)

**Trade-off**: Slower than parallel, but safer and simpler. If needed, run multiple instances with `--system` filter (e.g., one for cv, one for en).

### Why Low Temperature (0.2 Default)

**Decision**: Default temperature 0.2 (range 0.0-1.0)

**Rationale**:
1. **Minimize hallucination**: Higher temperature = more creative = more likely to add facts not in source
2. **Consistency**: Lower temperature = more deterministic = easier to validate
3. **Factual accuracy**: Medical flashcards must be precise, not creative
4. **Anti-hallucination constraint**: Prompts explicitly forbid adding external knowledge

**When to increase**:
- Testing different phrasing styles (0.3-0.5)
- Comparing provider creativity (0.5)
- Never go above 0.5 for production medical content

### Why Non-Destructive Updates

**Decision**: NEVER modify existing JSON fields, only add true_statements

**Rationale**:
1. **Phase 1 output is sacred**: Rust extractor (Phase 1) took hours to run
2. **Re-runnable**: Can re-generate statements without re-extracting questions
3. **Manual edits preserved**: Typo fixes in critique won't be overwritten
4. **Downstream safety**: Phase 3/4 can also augment same JSONs
5. **Debuggability**: Can compare before/after by checking for true_statements field

**Implementation**: Pydantic models use `extra="allow"` to preserve unknown fields.

### Why Checkpoint Batching

**Decision**: Save checkpoint every N questions (default: 10), not every question

**Rationale**:
1. **I/O efficiency**: Reduce disk writes (10x fewer writes)
2. **Atomic safety**: .tmp → rename ensures no partial checkpoint corruption
3. **Interrupt safety**: Ctrl+C during processing loses at most 9 questions of progress
4. **Resume speed**: Smaller checkpoint files load faster

**Trade-off**: Lose up to batch_size-1 questions of progress on crash. Acceptable for 2,198 question corpus.

## Troubleshooting

### Provider Issues

**"Claude CLI not found"**:
```bash
# Install Claude Code CLI
# https://docs.claude.com/en/docs/claude-code/

# Or set custom path
export CLAUDE_CLI_PATH=/path/to/claude
```

**"ANTHROPIC_API_KEY required"**:
```bash
# Create .env in project root
cd /Users/Mitchell/coding/projects/MKSAP
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

**Rate limiting**:
- Reduce batch size: `--batch-size 5`
- Switch provider: `--provider gemini`
- Use API with key: `--provider anthropic`

### Processing Issues

**Checkpoint corruption**:
```bash
# Reset checkpoint state
python -m src.main reset

# Verify reset
python -m src.main stats
```

**"Already has true_statements" but want to re-process**:
```bash
# Force re-processing
python -m src.main process --force --question-id cvmcq24001

# Or overwrite existing statements
python -m src.main process --overwrite --system cv
```

**Out of disk space** (logs accumulating):
```bash
# Clean old logs (keeps last 7 days)
python -m src.main clean-logs

# Clean everything
python -m src.main clean-all
```

### Data Quality Issues

**Hallucinated facts in statements**:
1. Check temperature (should be 0.2)
2. Review prompt - ensure anti-hallucination constraint is present
3. Compare against source critique - does statement match?
4. Switch provider - compare output quality

**Missing facts**:
1. Check if fact is in critique (not all facts are in every question)
2. Review prompt - may be filtered by atomic fact principle
3. Check if fact is in key_points instead of critique
4. Consider if fact is implied vs explicitly stated (prompts only extract explicit)

**Invalid JSON response**:
1. Check provider logs in outputs/logs/
2. Verify prompt doesn't have malformed JSON in examples
3. Retry: providers auto-retry on JSON parse errors
4. Switch provider if persistent

## Known Limitations

1. **CLI Provider Temperature Support**: Not all CLI providers support `--temperature` flag. Verify before using non-default temperatures.

2. **No Validation Framework**: No automated quality checking of extracted statements yet. Manual review recommended for first batch.

3. **No Wrong Answer Extraction**: Currently only extracts from critique (correct answer explanation) and key_points. Does NOT extract teaching points from wrong answer explanations.

4. **No Media Extraction**: Does NOT extract facts from figure captions or table data. Only processes text fields (critique, key_points).

5. **No Scenario Extraction**: Does NOT extract diagnostic patterns from question_text (clinical scenario). Only processes critique and key_points.

6. **Sequential Only**: No parallel processing. Maximum throughput limited by single-threaded execution.

## Next Steps for Development

After statement generation (Phase 2) is complete:

- **Phase 3**: Cloze Application - Apply [...] blanks to statements based on cloze_candidates
- **Phase 4**: Anki Export - Generate Anki deck with media assets (figures, tables, videos)

## References

- [Best Practices for Cloze Deletion Flashcards](best-practices-cloze-deletion-flashcards.md) - Research-backed SRS principles
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Current implementation status and testing checklist
- [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md) - Recent fixes and pending improvements
- [Phase 2 Implementation Plan](../.claude/plans/binary-weaving-stardust.md) - Original design document

---

**Last Updated**: December 31, 2025
**Project Phase**: Phase 2 of 4 (Statement Generation)
**Total Questions**: 2,198 MKSAP questions from Phase 1 Rust extractor
