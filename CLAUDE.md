# CLAUDE.md - MKSAP Medical Education Pipeline

> **Last Updated**: January 15, 2026
> **Recent Changes**: Consolidated scripts to single `/scripts` directory, removed migration helpers (Jan 15, 2026)

This file provides guidance to Claude Code when working on the MKSAP medical education extraction pipeline.

## Project Overview

**MKSAP Medical Education Pipeline** - Multi-phase system for extracting, processing, and generating medical education flashcards from ACP MKSAP (Medical Knowledge Self-Assessment Program) question bank.

**Project Location**: `/Users/Mitchell/coding/projects/MKSAP/`

### Current Status

- **Phase 1 (Complete ✅)**: Rust extractor - 2,198 questions extracted to JSON
- **Phase 2 (Active 🔄)**: Python statement generator - LLM-based flashcard extraction
- **Phase 3 (Planned 📋)**: Cloze application - Apply fill-in-the-blank formatting
- **Phase 4 (Planned 📋)**: Anki export - Generate spaced repetition decks

### Quick Links

- **Working on Phase 1?** → See [QUICKSTART.md](docs/QUICKSTART.md) for commands
- **Working on Phase 2?** → See [Statement Generator Reference](docs/reference/STATEMENT_GENERATOR.md)
- **Stuck on a problem?** → See [Troubleshooting Guide](docs/reference/TROUBLESHOOTING.md)
- **Understanding architecture?** → See [Phase 1 Deep Dive](docs/reference/PHASE_1_DEEP_DIVE.md)
- **Planning Phase 2 work?** → See [Phase 2 Status](docs/PHASE_2_STATUS.md)

## Important: System Codes vs Browser Organization

This codebase works with **16 two-letter system codes** (cv, en, fc, cs, gi, hp, hm, id, in, dm, np, nr, on, pm, cc, rm) that appear in question IDs and API endpoints. These are NOT the same as the 12 content area groupings visible in the MKSAP browser interface.

**Browser shows 12 content areas**, but some contain multiple system codes. All extraction, validation, and reporting in this codebase is organized by these 16 system codes, not the 12 browser groupings.

## Todo & Progress Tracking

### Single Source of Truth

**All project todos are tracked in [TODO.md](TODO.md)** for active and planned work. Completed work is recorded in
git history and removed from TODO.md.

**When starting work:**
1. Open [TODO.md](TODO.md) and find the task you're starting
2. Check dependencies - is anything blocking this task?
3. Review file links in the task description for context

**When done:**
1. Remove the completed task from TODO.md
2. Update "Last Updated" at top of TODO.md
3. Commit with a short, descriptive message (example: `git commit -m "mark: [task name] complete"`)

## Essential Commands

### Phase 1: Rust Extractor

```bash
cd /path/to/MKSAP/extractor

# Build
cargo build --release

# Run extraction (all systems)
./target/release/mksap-extractor

# Validate output
./target/release/mksap-extractor validate

# Get stats
./target/release/mksap-extractor discovery-stats

# Media: discover → download → extract (SVG/video)
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download --all
./target/release/mksap-extractor svg-browser --all
```

### Phase 2: Statement Generator

```bash
cd /path/to/MKSAP

# Test on 1 question
./scripts/python -m src.interface.cli process --question-id cvmcq24001

# Test on system
./scripts/python -m src.interface.cli process --mode test --system cv

# Production (all 2,198)
./scripts/python -m src.interface.cli process --mode production

# Stats & management
./scripts/python -m src.interface.cli stats
./scripts/python -m src.interface.cli reset
./scripts/python -m src.interface.cli clean-logs
```

## Utility Scripts

All utility scripts are located in `/scripts/`:

- **`python`** - CLI wrapper that sets PYTHONPATH for statement_generator. Use this for all Phase 2 CLI commands.
  ```bash
  ./scripts/python -m src.interface.cli <command>
  ```

- **`setup_nlp_model.sh`** - One-time setup script to download and extract the scispacy NLP model (v0.5.4).
  ```bash
  ./scripts/setup_nlp_model.sh
  ```
  After running, set the environment variable:
  ```bash
  export MKSAP_NLP_MODEL=statement_generator/models/en_core_sci_sm-0.5.4/en_core_sci_sm/en_core_sci_sm-0.5.4
  ```

## Project Structure

```
MKSAP/
├── CLAUDE.md                          ← This file
├── TODO.md                            ← Task tracking
├── scripts/                           ← Utility scripts
│   ├── python                         ← CLI wrapper (sets PYTHONPATH)
│   └── setup_nlp_model.sh             ← One-time: download scispacy model
├── extractor/                         ← Phase 1: Rust
│   ├── Cargo.toml
│   ├── src/
│   └── target/release/mksap-extractor
├── statement_generator/               ← Phase 2: Python (reorganized Jan 2026)
│   ├── pyproject.toml                 ← Dependencies & tool configs
│   ├── src/
│   │   ├── interface/                 ← CLI entry point
│   │   │   └── cli.py                 ← Main CLI commands
│   │   ├── orchestration/             ← Pipeline & checkpoint management
│   │   │   ├── pipeline.py            ← Statement processing workflow
│   │   │   └── checkpoint.py          ← State management & resumability
│   │   ├── processing/                ← Feature modules
│   │   │   ├── statements/            ← Statement extraction & validation
│   │   │   │   ├── extractors/        ← Critique & keypoints extraction
│   │   │   │   └── validators/        ← Quality, structure, ambiguity checks
│   │   │   ├── cloze/                 ← Cloze identification
│   │   │   ├── tables/                ← Table processing
│   │   │   └── normalization/         ← Text normalization
│   │   ├── infrastructure/            ← Cross-cutting concerns
│   │   │   ├── llm/                   ← LLM providers & client
│   │   │   │   ├── providers/         ← Anthropic, Claude Code, Gemini, Codex
│   │   │   │   └── client.py          ← Multi-provider wrapper
│   │   │   ├── io/                    ← File I/O operations
│   │   │   ├── config/                ← Configuration management
│   │   │   └── models/                ← Data models (Pydantic)
│   │   └── validation/                ← Validation framework (orchestrator)
│   ├── tests/                         ← Tests mirror src/ structure
│   │   ├── processing/
│   │   ├── infrastructure/
│   │   └── tools/                     ← Developer utilities (debug, manual validation)
│   ├── prompts/                       ← LLM prompt templates
│   └── artifacts/                     ← Runtime outputs (logs, checkpoints, validation)
├── mksap_data/                        ← Extracted questions (2,198 JSON files)
└── docs/
    ├── INDEX.md                       ← Documentation entry point
    ├── PROJECT_OVERVIEW.md            ← Project goals and architecture
    ├── QUICKSTART.md                  ← Essential commands
    ├── PHASE_1_COMPLETION_REPORT.md
    ├── PHASE_2_STATUS.md              ← Phase 2 status and priorities
    ├── DOCUMENTATION_MAINTENANCE_GUIDE.md
    ├── EXTRACTION_SCOPE.md
    ├── architecture/
    ├── reference/
    │   ├── PHASE_1_DEEP_DIVE.md        ← Phase 1 architecture details
    │   ├── TROUBLESHOOTING.md          ← Debugging guide
    │   ├── STATEMENT_GENERATOR.md      ← Phase 2 reference
    │   ├── CLOZE_FLASHCARD_BEST_PRACTICES.md
    │   └── VALIDATION.md
    ├── specifications/
    └── scraper/
```

## Statement Generator Architecture (Phase 2)

**Reorganized**: January 15, 2026 - Migrated to layered architecture for better navigation and extensibility.

### Layer Structure

The statement_generator follows a **pipeline-focused, 4-layer architecture**:

1. **Interface** (`src/interface/`) - CLI entry point and user commands
2. **Orchestration** (`src/orchestration/`) - Pipeline control and checkpoint management
3. **Processing** (`src/processing/`) - Feature modules organized by domain:
   - `statements/` - Statement extraction and validation (critique, keypoints)
   - `cloze/` - Cloze candidate identification and validation
   - `tables/` - Table extraction and processing
   - `normalization/` - Text normalization
4. **Infrastructure** (`src/infrastructure/`) - Cross-cutting concerns:
   - `llm/` - LLM provider abstraction and client
   - `io/` - File operations
   - `config/` - Configuration management
   - `models/` - Data models (Pydantic)

### Import Paths

After reorganization, imports use new paths:
```python
# New imports (current):
from src.infrastructure.models.data_models import Statement
from src.orchestration.pipeline import StatementPipeline
from src.processing.statements.extractors.critique import CritiqueProcessor
from src.infrastructure.llm.client import ClaudeClient
```

All imports are relative within the `src/` package for clarity.

### Key Files

- **Entry point**: `src/interface/cli.py` (was `main.py`)
- **Pipeline**: `src/orchestration/pipeline.py`
- **Extractors**: `src/processing/statements/extractors/`
- **Validators**: `src/processing/statements/validators/`
- **LLM Client**: `src/infrastructure/llm/client.py`

## Documentation Output Policy (Claude/Codex)

- All documentation lives under `docs/`.
- Do not create module-level `docs/` folders (for example, `statement_generator/docs/`).
- When creating new docs, place them in the appropriate `docs/` subfolder and link them from `docs/INDEX.md`.
- If a tool generates docs elsewhere, relocate them into `docs/` before committing.

## Key Design Principles

1. **Discovery-Driven** - Adapts to current API state, not hardcoded baselines
2. **Resumability** - Extraction can be interrupted and resumed without data loss
3. **Non-Destructive** - Phase 2 only adds `true_statements` field, preserves all original data
4. **Modular Documentation** - Detailed docs linked from this file, not embedded
5. **Frequent Commits** - Small, atomic commits with clear messages

## When Starting Work

1. **Check status**: Open [TODO.md](TODO.md)
2. **Review context**: Check task description and linked docs
3. **Run QUICKSTART command**: See [docs/QUICKSTART.md](docs/QUICKSTART.md)
4. **If stuck**: See [Troubleshooting Guide](docs/reference/TROUBLESHOOTING.md)
5. **When done**: Remove completed task from TODO.md, add a change note, and commit

## Next Steps

- **Phase 1 Complete?** → Read [Phase 1 Completion Report](docs/PHASE_1_COMPLETION_REPORT.md)
- **Working on Phase 2?** → Read [Phase 2 Status](docs/PHASE_2_STATUS.md)
- **Need architecture details?** → Read [Phase 1 Deep Dive](docs/reference/PHASE_1_DEEP_DIVE.md)
- **Understanding validation?** → Read [Validation Guide](docs/reference/VALIDATION.md)


---

**Repository**: git@github.com:mitch9727/mksap.git
**Phase 1 Status**: ✅ Complete (2,198 questions)
**Phase 2 Status**: 🔄 Active
