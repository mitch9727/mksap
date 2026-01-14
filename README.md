# MKSAP Question Bank Extractor

> **Last updated: January 6, 2026**

System for extracting medical education questions from the ACP MKSAP (Medical Knowledge Self-Assessment Program) online question bank into structured JSON format.

## Current Status

- **Phase 1 Status**: ✅ **COMPLETE** (December 27, 2025) - All 2,198 valid questions extracted
- **Phase 2 Status**: Statement generator active (see [PHASE_2_STATUS.md](docs/PHASE_2_STATUS.md))
- **Primary Tool**: Rust MKSAP Extractor (API-based extraction with discovery validation)
- **Architecture**: 16 system codes configured via the extractor configuration module
- **Extraction Results**: See [PHASE_1_COMPLETION_REPORT.md](docs/PHASE_1_COMPLETION_REPORT.md) for final metrics
- **Historical Data**: See [docs/archive/reports/](docs/archive/reports/) for past extraction summaries

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
# From repo root
pip install -r statement_generator/requirements.txt
```

Set the expected interpreter in `.env` so the CLI can enforce it (example: `MKSAP_PYTHON_VERSION=3.11.9`).

```bash
# Test on 1-2 questions
./scripts/python -m src.main process --mode test --system cv
```

Provider configuration and full CLI reference live in [STATEMENT_GENERATOR.md](docs/reference/STATEMENT_GENERATOR.md).

## Documentation

### Critical - Start Here

- **[PHASE_1_COMPLETION_REPORT.md](docs/PHASE_1_COMPLETION_REPORT.md)** ✅ - Phase 1 results (100% complete)
- **[Question ID Discovery](docs/archive/phase-1/QUESTION_ID_DISCOVERY.md)** - Historical discovery analysis
- **[Documentation Index](docs/INDEX.md)** - Navigation guide for all documentation
- **[PHASE_1_PLAN.md](docs/archive/phase-1/PHASE_1_PLAN.md)** - Archived Phase 1 roadmap
- **[Project TODO](TODO.md)** - Global project status tracker

### Getting Started with Extraction

- [Rust Extractor Setup](docs/reference/RUST_SETUP.md) - Installation and configuration
- [Usage Guide](docs/reference/RUST_USAGE.md) - How to run the extractor

### Deep Dives

- [Validation Guide](docs/reference/VALIDATION.md) - Data quality checks
- [Architecture](docs/reference/RUST_ARCHITECTURE.md) - Technical implementation
- [Troubleshooting](docs/reference/TROUBLESHOOTING.md) - Common issues and solutions

### Project Planning & Specifications

- [Project Overview](docs/PROJECT_OVERVIEW.md) - Project goals
- [Architecture Guide](docs/architecture/PROJECT_ORGANIZATION.md) - Codebase organization

### Phase 2: Statement Generator

- [Statement Generator Reference](docs/reference/STATEMENT_GENERATOR.md) - Usage, CLI, pipeline overview
- [Phase 2 Status](docs/PHASE_2_STATUS.md) - Current status and priorities
- [Cloze Flashcard Best Practices](docs/reference/CLOZE_FLASHCARD_BEST_PRACTICES.md) - Evidence-based guidance

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

1. Review [Architecture Guide](docs/architecture/PROJECT_ORGANIZATION.md)
2. Check [Rust Architecture](docs/reference/RUST_ARCHITECTURE.md)
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

1. Follow [Setup Guide](docs/reference/RUST_SETUP.md)
2. Check [Usage Guide](docs/reference/RUST_USAGE.md)
3. Review [Validation Guide](docs/reference/VALIDATION.md)

### For Extraction

1. Build project: `cd extractor && cargo build --release`
2. Run extraction: `./target/release/mksap-extractor`
3. Validate results: `./target/release/mksap-extractor validate`
4. Check [Troubleshooting](docs/reference/TROUBLESHOOTING.md) if issues

### For Phase 2 (Statement Generator)

1. Process the next 10-20 questions (start with `cv`) using `claude-code`
2. Triage validation false positives in `ambiguity_checks.py`
3. Add daily validation metrics reporting for `statement_generator/outputs/`

### For Development

1. Review [Architecture](docs/reference/RUST_ARCHITECTURE.md)
2. Understand [Project Structure](docs/architecture/PROJECT_ORGANIZATION.md)
3. Follow code patterns in existing modules
4. Write tests for new features

## Support

### Documentation

- Complete architecture documentation in `docs/`
- Modular guides for each major component
- Troubleshooting guide for common issues

### Troubleshooting

See [Troubleshooting Guide](docs/reference/TROUBLESHOOTING.md) for:
- Authentication issues
- Network problems
- Data quality checks
- Compilation errors

### Project Status

**Current Phase**: Phase 2 Active (statement generator)
**Completed**: All 2,198 valid questions extracted (December 27, 2025)
**Architecture**: Discovery-based extraction with API validation
**Validation**: Run `./target/release/mksap-extractor validate` for current metrics

The extractor uses API discovery (HTTP HEAD requests) to determine available questions, ensuring metrics reflect current API state rather than outdated baselines.

See [PHASE_1_COMPLETION_REPORT.md](docs/PHASE_1_COMPLETION_REPORT.md) for final results,
[PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) for architecture details, and [docs/archive/reports/](docs/archive/reports/)
for historical extraction data.

## License

Medical education question extraction for personal study purposes.

## Questions?

Refer to documentation:
- [Quick Start](docs/reference/RUST_SETUP.md)
- [Common Issues](docs/reference/TROUBLESHOOTING.md)
- [Architecture](docs/reference/RUST_ARCHITECTURE.md)
- [Statement Generator](docs/reference/STATEMENT_GENERATOR.md)
