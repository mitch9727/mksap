# MKSAP Question Bank Extractor

> **Last updated: December 26, 2025**

System for extracting medical education questions from the ACP MKSAP (Medical Knowledge Self-Assessment Program) online question bank into structured JSON format.

## Current Status

- **Primary Tool**: Rust MKSAP Extractor (API-based extraction with discovery validation)
- **Architecture**: 15 organ system prefixes configured (see [config.rs](text_extractor/src/config.rs))
- **Extraction Progress**: Run `./target/release/mksap-extractor validate` for current metrics
- **Historical Data**: See [docs/project/reports/](docs/project/reports/) for past extraction summaries

## Quick Start

### Rust Extractor (Recommended)

```bash
cd /Users/Mitchell/coding/projects/MKSAP
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

### Media Extraction (Post-Processing)

```bash
cargo build --release -p media-extractor
./target/release/media-extractor
```

Media extractor arguments:

```bash
./target/release/media-extractor /path/to/mksap_data
./target/release/media-extractor /path/to/mksap_data https://mksap.acponline.org
```

Override session cookie (optional):

```bash
MKSAP_SESSION=... ./target/release/media-extractor
```

## Documentation

### Critical - Start Here

- **[PHASE_1_PLAN.md](docs/project/PHASE_1_PLAN.md)** - Complete Phase 1 roadmap
- **[Question ID Discovery](docs/reference/QUESTION_ID_DISCOVERY.md)** - Understanding question discovery
- **[Project Index](docs/project/INDEX.md)** - Navigation guide for all documentation

### Getting Started with Extraction

- [Rust Extractor Setup](docs/reference/RUST_SETUP.md) - Installation and configuration
- [Usage Guide](docs/reference/RUST_ARCHITECTURE.md) - How extraction works

### Deep Dives

- [Validation Guide](docs/reference/VALIDATION.md) - Data quality checks
- [Architecture](docs/reference/RUST_ARCHITECTURE.md) - Technical implementation
- [Troubleshooting](docs/reference/TROUBLESHOOTING.md) - Common issues and solutions

### Project Planning & Specifications

- [Project Overview](docs/project/README.md) - Project goals
- [MCQ Format Specification](docs/specifications/MCQ_FORMAT.md) - Anki card output format
- [Architecture Guide](docs/architecture/PROJECT_ORGANIZATION.md) - Codebase organization

## Data Structure

Extracted questions are organized by organ system in the `mksap_data/` directory:

```
mksap_data/
├── .checkpoints/        # Extraction state and discovery metadata
├── cv/                  # Cardiovascular Medicine
├── en/                  # Endocrinology & Metabolism
├── cs/                  # Clinical Practice
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

Each question directory contains:
- `{question_id}.json` - Complete structured data
- `{question_id}_metadata.txt` - Human-readable summary
- `figures/` - Downloaded media assets (if any)

See [config.rs](text_extractor/src/config.rs) for complete system definitions.

## Features

### Rust Extractor

✓ API-based direct extraction
✓ Session-based authentication
✓ Rate-limited requests (respects server)
✓ Data validation framework
✓ Resumable extraction
✓ Organized JSON output
✓ Metadata files for each question

## Project Tools

### Rust Extractor

**Location**: Project root directory

Primary tool for API-based extraction:
- Direct HTTPS API calls
- Efficient bulk extraction
- Data validation
- Organized output

**Key Files**:
- `src/main.rs` - Entry point
- `src/extractor.rs` - Extraction logic
- `src/config.rs` - System definitions
- `src/validator.rs` - Data quality checks
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

- **`.claude/` folder**: Project-specific configuration
  - Custom commands for validation and organization
  - Documentation standards
  - File organization rules
  - Claude Code skills

## Next Steps

### For New Users

1. Follow [Setup Guide](docs/reference/RUST_SETUP.md)
2. Check [Usage Guide](docs/reference/RUST_ARCHITECTURE.md)
3. Review [Validation Guide](docs/reference/VALIDATION.md)

### For Extraction

1. Build project: `cd text_extractor && cargo build --release`
2. Run extraction: `./target/release/mksap-extractor`
3. Validate results: `./target/release/mksap-extractor validate`
4. Check [Troubleshooting](docs/reference/TROUBLESHOOTING.md) if issues

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

**Current Phase**: Phase 1 - Data Extraction
**Architecture**: Discovery-based extraction with API validation
**Check Progress**: Run `./target/release/mksap-extractor validate`

The extractor uses API discovery (HTTP HEAD requests) to determine available questions, ensuring metrics reflect current API state rather than outdated baselines.

See [docs/project/README.md](docs/project/README.md) for architecture details and [docs/project/reports/](docs/project/reports/) for historical extraction data.

## License

Medical education question extraction for personal study purposes.

## Questions?

Refer to documentation:
- [Quick Start](docs/reference/RUST_SETUP.md)
- [Common Issues](docs/reference/TROUBLESHOOTING.md)
- [Architecture](docs/reference/RUST_ARCHITECTURE.md)
