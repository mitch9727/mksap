# Statement Generator (Phase 2)

**Last Updated**: January 15, 2026

## Overview

The statement generator is the Phase 2 Python pipeline that extracts testable medical facts from MKSAP critiques and key
points. It reads from `mksap_data/` (2,198 questions), augments Phase 1 JSONs with a `true_statements` field, and
preserves all existing data.

## Features

- Multi-provider LLM support (Anthropic API, Claude Code CLI, Gemini CLI, Codex CLI)
- 4-step pipeline: critique extraction -> key points extraction -> cloze identification -> text normalization
- Non-destructive JSON updates (adds `true_statements` only)
- Checkpoint-based resumable processing
- CLI-first workflows with optional provider fallback
- Flashcard design aligned with `statement_generator/docs/CLOZE_FLASHCARD_BEST_PRACTICES.md`

## Quick Start

### 1) Install dependencies

```bash
# From repo root, using pyproject.toml
cd statement_generator
pip install -e .
# OR using Poetry:
poetry install
```

Optional: set the expected interpreter in `.env` so the CLI can enforce it (example: `MKSAP_PYTHON_VERSION=3.11.9`).

### 1b) Install scispaCy model (validation NLP)

Validation uses spaCy/scispaCy for lemma/entity matching. Install a model such as `en_core_sci_sm` per scispaCy
instructions.

Local model option (avoids system-wide install):

```bash
# Download and extract into the repo
./statement_generator/scripts/setup_nlp_model.sh
```

Optional environment settings:

```bash
# Enable/disable NLP validation
export MKSAP_USE_NLP=1

# Select model and performance knobs
export MKSAP_NLP_MODEL=en_core_sci_sm
export MKSAP_NLP_DISABLE=parser
export MKSAP_NLP_BATCH_SIZE=32
export MKSAP_NLP_N_PROCESS=1
```

If using a local model path:

```bash
export MKSAP_NLP_MODEL=statement_generator/models/en_core_sci_sm-0.5.4/en_core_sci_sm/en_core_sci_sm-0.5.4
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
# Copy questions into the test data root
./scripts/python -m src.interface.cli prepare-test --question-id cvmcq24001

# Test on 1-2 questions
./scripts/python -m src.interface.cli process --mode test --system cv

# Test specific question
./scripts/python -m src.interface.cli process --question-id cvmcq24001

# Production: process all questions
./scripts/python -m src.interface.cli process --mode production

# Use CLI providers
./scripts/python -m src.interface.cli process --provider claude-code --mode test
./scripts/python -m src.interface.cli process --provider gemini --mode test
./scripts/python -m src.interface.cli process --provider codex --mode test
```

Optional override for data root:

```bash
export MKSAP_DATA_ROOT=test_mksap_data
```

## CLI Reference

### Commands

```bash
# Process questions (main command)
./scripts/python -m src.interface.cli process [OPTIONS]

# Show statistics
./scripts/python -m src.interface.cli stats

# Reset checkpoints
./scripts/python -m src.interface.cli reset

# Copy selected questions into test_mksap_data
./scripts/python -m src.interface.cli prepare-test --question-id cvmcq24001

# Clean old log files (keeps last 7 days by default)
./scripts/python -m src.interface.cli clean-logs
./scripts/python -m src.interface.cli clean-logs --keep-days 3
./scripts/python -m src.interface.cli clean-logs --dry-run  # Preview what would be deleted

# Clean all logs and reset checkpoints (fresh start)
./scripts/python -m src.interface.cli clean-all
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
| `--data-root` | Override data root | Test: `test_mksap_data`, Prod: `mksap_data` |
| `--log-level` | DEBUG, INFO, WARNING, ERROR | INFO |
| `--batch-size` | Questions per checkpoint save | 10 |

### Examples

```bash
# Test with Claude Code CLI (uses your subscription)
./scripts/python -m src.interface.cli process --provider claude-code --mode test --system cv

# Production with Gemini
./scripts/python -m src.interface.cli process --provider gemini --mode production

# Test with higher temperature (more creative)
./scripts/python -m src.interface.cli process --temperature 0.5 --question-id cvmcq24001

# Dry run to preview
./scripts/python -m src.interface.cli process --dry-run --system cv

# Override data root (for full production runs)
./scripts/python -m src.interface.cli process --mode production --data-root mksap_data

# Debug logging
./scripts/python -m src.interface.cli process --log-level DEBUG --question-id cvmcq24001
```

## Provider Selection and Fallback

- Provider settings (model, temperature, keys) are loaded from `--provider` or `LLM_PROVIDER` (default is
  `anthropic`).
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
        "statement": "ACE inhibitors are first-line therapy for hypertension with chronic kidney disease.",
        "extra_field": "They reduce proteinuria and slow chronic kidney disease progression.",
        "cloze_candidates": ["ACE inhibitors", "chronic kidney disease", "proteinuria"]
      }
    ],
    "from_key_points": [
      {
        "statement": "Initial chronic cough management includes tobacco cessation and stopping ACE inhibitors.",
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
├── pyproject.toml              # Dependencies & tool configurations
├── src/                        # 4-layer pipeline architecture
│   ├── interface/              # CLI entry point
│   │   └── cli.py              # Main command interface
│   ├── orchestration/          # Pipeline control & state management
│   │   ├── pipeline.py         # Main processing workflow
│   │   └── checkpoint.py       # Resumable processing state
│   ├── processing/             # Feature modules
│   │   ├── statements/         # Statement extraction & validation
│   │   │   ├── extractors/     # Critique, keypoints extraction
│   │   │   └── validators/     # Quality, structure, ambiguity, enumeration checks
│   │   ├── cloze/              # Cloze identification & validation
│   │   ├── tables/             # Table extraction
│   │   └── normalization/      # Text symbol normalization
│   ├── infrastructure/         # Cross-cutting concerns
│   │   ├── llm/                # LLM providers (Anthropic, Claude Code, Gemini, Codex)
│   │   ├── io/                 # File I/O operations
│   │   ├── config/             # Configuration management
│   │   └── models/             # Data models (Pydantic)
│   └── validation/             # Validation orchestrator
├── tests/                      # Test suite (mirrors src/ structure)
│   ├── processing/
│   ├── infrastructure/
│   └── tools/                  # Developer utilities (debug, manual validation)
├── prompts/                    # LLM prompt templates
├── scripts/                    # Setup & migration scripts
└── artifacts/                  # Runtime outputs (logs, checkpoints, validation, pytest cache)
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

### Phase 2 Priorities (Active)

- Process the next 10-20 questions (start with `cv`) using `claude-code`
- Reduce ambiguity false positives in `ambiguity_checks.py`
- Add daily validation metrics reporting in `statement_generator/artifacts/validation/`

### After Statement Generation (Planned)

- Phase 3: Cloze application (apply [...] blanks to statements)
- Phase 4: Anki export (generate deck with media assets)

## References

- `statement_generator/docs/CLOZE_FLASHCARD_BEST_PRACTICES.md`
- `statement_generator/docs/LEGACY_STATEMENT_STYLE_GUIDE.md`
- `../PHASE_2_STATUS.md`
