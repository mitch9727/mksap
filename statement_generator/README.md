# MKSAP Statement Generator - Phase 2

Extract testable medical facts from MKSAP question critiques and key points using LLM-powered analysis.

## Features

- **Multi-Provider LLM Support**: Use Anthropic API, Claude Code CLI, Gemini CLI, or Codex CLI
- **Evidence-Based Design**: Follows research-backed flashcard best practices
- **3-Step Pipeline**: Critique extraction → Key points extraction → Cloze identification
- **Resumable Processing**: Checkpoint-based workflow for 2,198 questions
- **Temperature Control**: Adjustable creativity vs. accuracy (default: 0.2)
- **CLI-First**: Use existing paid subscriptions instead of separate API keys

## Quick Start

### 1. Install Dependencies

```bash
cd statement_generator
pip install -r requirements.txt
```

### 2. Configure Provider

#### Option A: Anthropic API (Default)

```bash
# Copy .env template
cp ../.env.template ../.env

# Edit .env and set:
ANTHROPIC_API_KEY=your_api_key_here
```

#### Option B: Claude Code CLI (Subscription)

```bash
# Install Claude Code CLI
# https://docs.claude.com/en/docs/claude-code/

# In .env (optional):
LLM_PROVIDER=claude-code
```

#### Option C: Google Gemini CLI (Subscription)

```bash
# Install Gemini CLI
# https://ai.google.dev/

# In .env:
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-pro
```

#### Option D: OpenAI Codex CLI (Subscription)

```bash
# Install OpenAI CLI
# https://platform.openai.com/docs/guides/cli

# In .env:
LLM_PROVIDER=codex
OPENAI_MODEL=gpt-4
```

### 3. Run Statement Generation

```bash
# Test on 1-2 questions
python -m src.main process --mode test --system cv

# Test specific question
python -m src.main process --question-id cvmcq24001

# Production: Process all questions
python -m src.main process --mode production

# Use different provider via CLI
python -m src.main process --provider claude-code --mode test
python -m src.main process --provider gemini --mode test
python -m src.main process --provider codex --mode test
```

## CLI Reference

### Commands

```bash
# Process questions (main command)
python -m src.main process [OPTIONS]

# Show statistics
python -m src.main stats

# Reset checkpoints
python -m src.main reset

# Clean old log files (keeps last 7 days by default)
python -m src.main clean-logs
python -m src.main clean-logs --keep-days 3
python -m src.main clean-logs --dry-run  # Preview what would be deleted

# Clean all logs and reset checkpoints (fresh start)
python -m src.main clean-all
```

### Key Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mode` | `test` (1-2 questions) or `production` (all) | `test` |
| `--provider` | LLM provider (claude-code, codex, anthropic, gemini) | `claude-code` |
| `--question-id` | Process specific question by ID | None |
| `--system` | Process all questions in system (cv, en, etc.) | None |
| `--temperature` | LLM temperature (0.0-1.0) | 0.2 |
| `--model` | Model name (varies by provider) | Provider default |
| `--resume/--no-resume` | Resume from checkpoint | `--resume` |
| `--skip-existing/--overwrite` | Skip questions with true_statements | `--skip-existing` |
| `--force` | Re-process even if already completed (ignores checkpoint) | False |
| `--dry-run` | Preview without API calls | False |
| `--log-level` | DEBUG, INFO, WARNING, ERROR | INFO |
| `--batch-size` | Questions per checkpoint save | 10 |

### Examples

```bash
# Test with Claude Code CLI (uses your subscription)
python -m src.main process --provider claude-code --mode test --system cv

# Production with Gemini
python -m src.main process --provider gemini --mode production

# Test with higher temperature (more creative)
python -m src.main process --temperature 0.5 --question-id cvmcq24001

# Dry run to preview
python -m src.main process --dry-run --system cv

# Debug logging
python -m src.main process --log-level DEBUG --question-id cvmcq24001
```

## Provider Comparison

| Provider | API/CLI | Cost Model | Best For |
|----------|---------|------------|----------|
| **anthropic** | API | Pay-per-use | Production, reproducibility |
| **claude-code** | CLI | Subscription | Using existing Claude subscription |
| **gemini** | CLI | Subscription | Using existing Google AI subscription |
| **codex** | CLI | Subscription | Using existing OpenAI subscription |

**Recommendation**: Start with `claude-code`, `gemini`, or `codex` if you have existing subscriptions. This avoids separate API key costs. Use `anthropic` for production runs where you need guaranteed availability.

## Output Structure

Each question's JSON is augmented with:

```json
{
  "question_id": "cvmcq24001",
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
    "from_key_points": [...]
  }
}
```

## Evidence-Based Principles

Statements follow research-backed flashcard design:

1. **Atomic Facts**: Each statement tests ONE concept
2. **Unambiguous**: Only one possible answer per cloze
3. **Concise**: Essential words only, no fluff
4. **No Enumerations**: Lists broken into overlapping chunks
5. **Clinical Context**: Extra field explains WHY it matters
6. **Faithful**: Low temperature prevents hallucination
7. **Multiple Clozes**: 2-5 candidates per statement when appropriate

See [/docs/best-practices-cloze-deletion-flashcards.md](../docs/best-practices-cloze-deletion-flashcards.md) for full details.

## Troubleshooting

### "Claude CLI not found"

```bash
# Install Claude Code CLI
# https://docs.claude.com/en/docs/claude-code/

# Or set custom path
export CLAUDE_CLI_PATH=/path/to/claude
```

### "Gemini CLI not found"

```bash
# Install Gemini CLI
pip install google-generativeai

# Or set custom path
export GEMINI_CLI_PATH=/path/to/gemini
```

### "OpenAI CLI not found"

```bash
# Install OpenAI CLI
pip install openai

# Or set custom path
export OPENAI_CLI_PATH=/path/to/openai
```

### "ANTHROPIC_API_KEY required"

If using `--provider anthropic`:

```bash
# Set API key in .env
echo "ANTHROPIC_API_KEY=your_key_here" >> ../.env
```

### Rate Limiting

CLI providers use your subscription limits. If you hit rate limits:

1. **Reduce batch size**: `--batch-size 5`
2. **Switch providers**: Try different provider
3. **Use API**: Fall back to `--provider anthropic` with API key

## Architecture

### 3-Step Pipeline

```
PHASE 1: Critique Extraction
├─ Input: critique field (300-800 words)
├─ Output: 3-7 atomic statements with extra field
└─ Goal: Extract testable facts, maximize concept coverage

PHASE 2: Key Points Extraction
├─ Input: key_points array (0-3 pre-formatted bullets)
├─ Output: 1-3 refined statements
└─ Goal: Minimal rewriting, preserve quality

PHASE 3: Cloze Identification
├─ Input: All statements from Phase 1 + 2
├─ Output: 2-5 cloze candidates per statement
└─ Goal: Identify testable terms for cloze deletion
```

### Provider Abstraction

```
BaseLLMProvider (interface)
├─ AnthropicProvider (API)
├─ ClaudeCodeProvider (CLI)
├─ GeminiProvider (CLI)
└─ CodexProvider (CLI)
```

All providers implement:
- `generate(prompt, temperature, max_retries) -> str`
- `get_provider_name() -> str`

### File Structure

```
statement_generator/
├── src/
│   ├── providers/          # LLM provider implementations
│   │   ├── base.py
│   │   ├── anthropic_provider.py
│   │   ├── claude_code_provider.py
│   │   ├── gemini_provider.py
│   │   └── codex_provider.py
│   ├── config.py           # Configuration (loads from project .env)
│   ├── models.py           # Data models
│   ├── file_io.py          # JSON operations
│   ├── checkpoint.py       # Resume system
│   ├── llm_client.py       # Multi-provider client
│   ├── critique_processor.py    # Step 1
│   ├── keypoints_processor.py   # Step 2
│   ├── cloze_identifier.py      # Step 3
│   ├── pipeline.py         # Orchestrator
│   └── main.py             # CLI entry point
├── prompts/
│   ├── critique_extraction.md
│   ├── keypoints_extraction.md
│   └── cloze_identification.md
└── outputs/
    ├── checkpoints/        # Resume state
    └── logs/               # Execution logs
```

## Next Steps

After statement generation:

- **Phase 3**: Cloze Application - Apply cloze deletions to statements
- **Phase 4**: Anki Export - Generate Anki deck with media assets

## References

- [Best Practices for Cloze Deletion Flashcards](../docs/best-practices-cloze-deletion-flashcards.md)
- [Phase 2 Implementation Plan](../.claude/plans/binary-weaving-stardust.md)

## License

Private project for personal medical education.
