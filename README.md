# MKSAP Question Bank Extractor

> **Last updated: January 20, 2026**

System for extracting medical education questions from the ACP MKSAP (Medical Knowledge Self-Assessment Program) online question bank into structured JSON format.

## Current Status

- **Phase 1 Status**: ✅ **COMPLETE** (December 27, 2025) - All 2,198 valid questions extracted
- **Phase 2 Status**: ✅ **COMPLETE** (January 16, 2026) - Statement generator implementation finished
- **Phase 3 Status**: ✅ **COMPLETE** (January 16, 2026) - Validation framework deployed (92.9% pass rate)
- **Phase 4 Status**: ⚡ **IN PROGRESS** - Production deployment and optimization
- **Primary Tool**: Rust MKSAP Extractor (API-based extraction with discovery validation)
- **Architecture**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design

## Quick Start

### Rust Extractor (Recommended)

```bash
cd /path/to/MKSAP/extractor
cargo build --release
./target/release/mksap-extractor
```

Validate extracted data:

```bash
./target/release/mksap-extractor validate
```

Override session cookie (optional):

```bash
MKSAP_SESSION=... ./target/release/mksap-extractor
```

### Media Extraction (Integrated)

```bash
cd extractor
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download
```

Media commands:

```bash
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download --all
./target/release/mksap-extractor media-download --question-id cvmcq24001
```

Override session cookie (optional):

```bash
MKSAP_SESSION=... ./target/release/mksap-extractor media-download --all
```

### Statement Generator (Phase 2)

```bash
# From repo root, install dependencies (uses pyproject.toml)
cd statement_generator
pip install -e .
# OR using Poetry:
poetry install
```

Set the expected interpreter in `.env` so the CLI can enforce it (example: `MKSAP_PYTHON_VERSION=3.11.9`).

```bash
# Test on 1-2 questions
../scripts/python -m src.interface.cli process --limit 1 --system cv
```

Provider configuration and full CLI reference live in [STATEMENT_GENERATOR.md](statement_generator/docs/STATEMENT_GENERATOR.md).

## Documentation

### Critical - Start Here

- **[Documentation Index](docs/INDEX.md)** - Navigation guide for all documentation
- **[Project Overview](docs/PROJECT_OVERVIEW.md)** - Project goals and background
- **[System Architecture](docs/ARCHITECTURE.md)** - Core system design and components
- **[PHASE_1_COMPLETION_REPORT.md](extractor/docs/PHASE_1_COMPLETION_REPORT.md)** ✅ - Phase 1 results (100% complete)
- **[Phase 4 Deployment](statement_generator/docs/deployment/PHASE4_DEPLOYMENT_PLAN.md)** - Current production plan
- **[Project TODO](TODO.md)** - Global project status tracker

### Getting Started with Extraction

- [Extractor Docs Index](extractor/docs/INDEX.md) - Entry point for extraction docs
- [Extractor Manual](extractor/docs/EXTRACTOR_MANUAL.md) - Extractor architecture and usage
- [Setup (Archive)](extractor/docs/archive/phase1/RUST_SETUP.md) - Rust installation (Phase 1)
- [Usage Guide (Archive)](extractor/docs/archive/phase1/RUST_USAGE.md) - How to run the extractor (Phase 1)

### Deep Dives

- [Validation Guide](extractor/docs/VALIDATION.md) - Data quality checks

- [Troubleshooting](extractor/docs/TROUBLESHOOTING.md) - Common issues and solutions

### Project Planning & Specifications

- [Project Overview](README.md) - Project goals
- [System Architecture](docs/ARCHITECTURE.md) - Codebase organization
- [Scope & Completion](extractor/docs/PHASE_1_COMPLETION_REPORT.md) - Final scope and results

### Phase 2: Statement Generator

- [Statement Generator Reference](statement_generator/docs/STATEMENT_GENERATOR.md) - Usage, CLI, pipeline overview
- [Phase 2 Status](statement_generator/docs/PHASE_2_STATUS.md) - Current status and priorities
- [Cloze Flashcard Best Practices](statement_generator/docs/CLOZE_FLASHCARD_BEST_PRACTICES.md) - Evidence-based guidance

## Data Structure

Extracted questions are organized by organ system in the `mksap_data/` directory:

```
mksap_data/
├── .checkpoints/        # Extraction state and discovery metadata
├── cv/                  # Cardiovascular Medicine
├── en/                  # Endocrinology & Metabolism
├── fc/                  # Foundations of Clinical Practice
├── cs/                  # Common Symptoms
├── gi/                  # Gastroenterology
├── hp/                  # Hepatology
├── hm/                  # Hematology
├── id/                  # Infectious Disease
├── in/                  # Interdisciplinary Medicine
├── dm/                  # Dermatology
├── np/                  # Nephrology
├── nr/                  # Neurology
├── on/                  # Oncology
├── pm/                  # Pulmonary Medicine
├── cc/                  # Critical Care
└── rm/                  # Rheumatology
```

Checkpoints are stored in `mksap_data/.checkpoints/` (default output is `../mksap_data` when running from `extractor/`).

Each question directory contains:
- `{question_id}.json` - Complete structured data
- `figures/`, `tables/`, `videos/`, `svgs/` - Media assets (videos are manual downloads)

See the extractor configuration module for complete system definitions.

## Features

### Rust Extractor

✓ API-based direct extraction
✓ Session-based authentication
✓ Rate-limited requests (respects server)
✓ Data validation framework
✓ Resumable extraction
✓ Organized JSON output
✓ Discovery checkpoints

## Project Tools

### Rust Extractor

**Location**: `extractor/`

Primary tool for API-based extraction:
- Direct HTTPS API calls
- Efficient bulk extraction
- Data validation
- Organized output

**Core Components**:
- CLI entrypoint and command routing
- Extraction pipeline and discovery logic
- System configuration definitions
- Data validation and reporting
- `mksap_data/` - Extracted questions

## Technology Stack

### Rust Extractor
- **Language**: Rust 2021
- **Runtime**: Tokio (async)
- **HTTP**: reqwest
- **Parsing**: scraper, select
- **Serialization**: serde, serde_json

## Contributing

This project is actively maintained. To contribute:

1. Review [System Architecture](docs/ARCHITECTURE.md)
2. Check [Extractor Manual](extractor/docs/EXTRACTOR_MANUAL.md)
3. Follow existing code patterns
4. Test changes before submitting

## Project Configuration

The project includes Claude Code integration:

- **Claude Code config**: Global configuration in `~/.claude/` (project no longer ships a `.claude/` folder)
  - Custom commands for validation and organization
  - Documentation standards
  - File organization rules
  - Claude Code skills

## Next Steps

### For New Users

1. Start with the [Extractor Docs Index](extractor/docs/INDEX.md)
2. Check the [Extractor Manual](extractor/docs/EXTRACTOR_MANUAL.md)
3. Review the [Validation Guide](extractor/docs/VALIDATION.md)

### For Extraction

1. Build project: `cd extractor && cargo build --release`
2. Run extraction: `./target/release/mksap-extractor`
3. Validate results: `./target/release/mksap-extractor validate`
4. Check [Troubleshooting](extractor/docs/TROUBLESHOOTING.md) if issues

### For Phase 2 (Statement Generator)

1. Process the next 10-20 questions (start with `cv`) using `claude-code`
2. Triage validation false positives in `ambiguity_checks.py`
3. Add daily validation metrics reporting for `statement_generator/outputs/`

### For Development

1. Review [Architecture](docs/ARCHITECTURE.md)
2. Understand [Project Structure](docs/architecture/PROJECT_ORGANIZATION.md) (Note: Legacy reference)
3. Follow code patterns in existing modules
4. Write tests for new features

## Support

### Documentation

- Project-level docs in `docs/`; component docs in `extractor/docs/` and `statement_generator/docs/`
- Modular guides for each major component
- Troubleshooting guide for common issues

### Troubleshooting

See [Troubleshooting Guide](extractor/docs/TROUBLESHOOTING.md) for:
- Authentication issues
- Network problems
- Data quality checks
- Compilation errors

### Project Status

**Current Phase**: Phase 4 Active (Production Deployment)
**Completed**: Phase 1 (Extraction), Phase 2 (Statement Gen), Phase 3 (Validation)
**Architecture**: Discovery-based extraction, 4-layer Python pipeline
**Validation**: Run `./target/release/mksap-extractor validate` for metadata metrics

The extractor uses API discovery (HTTP HEAD requests) to determine available questions, ensuring metrics reflect current API state rather than outdated baselines.

See [PHASE_1_COMPLETION_REPORT.md](extractor/docs/PHASE_1_COMPLETION_REPORT.md) for final results and
[PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) for architecture details.

## License

Medical education question extraction for personal study purposes.

## Questions?

Refer to documentation:
- [Quick Start](docs/QUICKSTART.md)
- [Common Issues](extractor/docs/TROUBLESHOOTING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Statement Generator](statement_generator/docs/STATEMENT_GENERATOR.md)
