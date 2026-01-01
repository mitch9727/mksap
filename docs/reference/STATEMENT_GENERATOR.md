# Statement Generator (Phase 2)

**Last Updated**: December 31, 2025

## Overview

The statement generator is the Phase 2 Python pipeline that extracts testable medical facts from MKSAP critiques and key points. It reads from `mksap_data/`, augments Phase 1 JSONs with a `true_statements` field, and preserves all existing data.

## Features

- Multi-provider LLM support (Anthropic API, Claude Code CLI, Gemini CLI, Codex CLI)
- 4-step pipeline: critique extraction -> key points extraction -> cloze identification -> text normalization
- Non-destructive JSON updates (adds `true_statements` only)
- Checkpoint-based resumable processing
- CLI-first workflows with optional provider fallback
- Flashcard design aligned with `docs/reference/CLOZE_FLASHCARD_BEST_PRACTICES.md`

## Quick Start

### 1) Install dependencies

```bash
cd statement_generator
pip install -r requirements.txt
```

### 2) Configure a provider

Option A: Anthropic API (default)

```bash
# Copy .env template
cp ../.env.template ../.env

# Edit .env and set:
ANTHROPIC_API_KEY=your_api_key_here
```

Option B: Claude Code CLI (subscription)

```bash
# Install Claude Code CLI
# https://docs.claude.com/en/docs/claude-code/

# In .env (optional):
LLM_PROVIDER=claude-code
CLAUDE_MODEL=sonnet
```

Option C: Google Gemini CLI (subscription)

```bash
# Install Gemini CLI
# https://ai.google.dev/

# In .env:
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-pro
```

Option D: OpenAI Codex CLI (subscription)

```bash
# Install OpenAI CLI
# https://platform.openai.com/docs/guides/cli

# In .env:
LLM_PROVIDER=codex
OPENAI_MODEL=gpt-4
```

### 3) Run statement generation

```bash
# Test on 1-2 questions
python -m src.main process --mode test --system cv

# Test specific question
python -m src.main process --question-id cvmcq24001

# Production: process all questions
python -m src.main process --mode production

# Use CLI providers
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
| `--provider` | LLM provider (claude-code, codex, anthropic, gemini) | `anthropic` |
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

## Provider Selection and Fallback

- Provider settings (model, temperature, keys) are loaded from `--provider` or `LLM_PROVIDER` (default is `anthropic`).
- Processing uses a provider manager with a fixed fallback order: `claude-code` -> `codex` -> `anthropic` -> `gemini`.
- When rate limits are detected, the CLI prompts before switching providers.

## Output Structure

Each question's JSON is augmented with:

```json
{
  "question_id": "cvmcq24001",
  "critique": "...",
  "key_points": ["..."],
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

## Pipeline Overview

```
PHASE 1: Critique Extraction
- Input: critique field (medical explanation)
- Output: 3-7 atomic statements

PHASE 2: Key Points Extraction
- Input: key_points array
- Output: 1-3 refined statements

PHASE 3: Cloze Identification
- Input: statements from phases 1-2
- Output: 2-5 cloze candidates per statement

PHASE 4: Text Normalization
- Input: statements with cloze candidates
- Output: normalized symbols (e.g., "less than" -> "<")
```

## File Structure

```
statement_generator/
├── src/        # Pipeline, providers, config, IO, and CLI entrypoint
├── prompts/    # Prompt templates
└── outputs/    # Checkpoints and logs
```

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

1. Reduce batch size: `--batch-size 5`
2. Switch providers: `--provider gemini`
3. Use API provider: `--provider anthropic` with API key

## Next Steps

After statement generation:

- Phase 3: Cloze application (apply [...] blanks to statements)
- Phase 4: Anki export (generate deck with media assets)

## References

- `docs/reference/CLOZE_FLASHCARD_BEST_PRACTICES.md`
- `docs/project/PHASE_2_STATUS.md`
