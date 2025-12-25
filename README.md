# MKSAP Question Bank Extractor

System for extracting medical education questions from the ACP MKSAP (Medical Knowledge Self-Assessment Program) online question bank.

## Current Status

- **754 questions extracted** (34% of 2,233 target)
- **8 of 16 systems** have partial data
- **Primary Tool**: Rust MKSAP Extractor (API-based, active)
- **Phase**: Phase 1 - Data Extraction (See [PHASE_1_PLAN.md](docs/project/PHASE_1_PLAN.md) for complete roadmap)

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

- **[PHASE_1_PLAN.md](docs/project/PHASE_1_PLAN.md)** - Complete Phase 1 roadmap (2,233 question extraction)
- **[Question ID Discovery](docs/Question%20ID%20Discovery.md)** - Understanding the 2,233 question count
- **[Project Index](docs/project/INDEX.md)** - Navigation guide for all documentation

### Getting Started with Extraction

- [Rust Extractor Overview](docs/rust/overview.md) - What it does and current status
- [Setup Guide](docs/rust/setup.md) - Installation and configuration
- [Usage Guide](docs/rust/usage.md) - How to run extraction

### Deep Dives

- [Validation Guide](docs/rust/validation.md) - Data quality checks
- [Architecture](docs/rust/architecture.md) - Technical implementation
- [Troubleshooting](docs/rust/troubleshooting.md) - Common issues and solutions

### Project Planning & Specifications

- [Project Overview](docs/project/README.md) - Project goals
- [MCQ Format Specification](docs/specifications/MCQ_FORMAT.md) - Anki card output format
- [Architecture Guide](docs/architecture/PROJECT_ORGANIZATION.md) - Codebase organization

## Data Structure

Extracted questions are organized by organ system. Target: 2,233 questions across 16 systems and 6 question types (mcq, cor, vdx, qqq, mqq, sq).

Current partial data (754 questions):
```
mksap_data/
├── cv/   (132 questions) - Cardiovascular Medicine
├── en/   (101 questions) - Endocrinology & Metabolism
├── hm/   (72 questions)  - Hematology
├── id/   (114 questions) - Infectious Disease
├── np/   (107 questions) - Nephrology
├── nr/   (78 questions)  - Neurology
├── on/   (72 questions)  - Oncology
└── rm/   (78 questions)  - Rheumatology
```

See [PHASE_1_PLAN.md](docs/project/PHASE_1_PLAN.md) for complete target breakdown across all 16 systems and 6 question types.

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
2. Check [Rust Architecture](docs/rust/architecture.md)
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

1. Read [Rust Overview](docs/rust/overview.md)
2. Follow [Setup Guide](docs/rust/setup.md)
3. Run [Usage Guide](docs/rust/usage.md)
4. Check [Validation Guide](docs/rust/validation.md)

### For Extraction

1. Build project: `cargo build --release`
2. Run extraction: `./target/release/mksap-extractor`
3. Validate results: `./target/release/mksap-extractor validate`
4. Check [Troubleshooting](docs/rust/troubleshooting.md) if issues

### For Development

1. Review [Architecture](docs/rust/architecture.md)
2. Understand [Project Structure](docs/architecture/PROJECT_ORGANIZATION.md)
3. Follow code patterns in existing modules
4. Write tests for new features

## Support

### Documentation

- Complete architecture documentation in `docs/`
- Modular guides for each major component
- Troubleshooting guide for common issues

### Troubleshooting

See [Troubleshooting Guide](docs/rust/troubleshooting.md) for:
- Authentication issues
- Network problems
- Data quality checks
- Compilation errors

### Project Status

**Last Updated**: December 25, 2025
**Current Phase**: Phase 1 - Data Extraction
**Extraction Coverage**: 34% (754/2,233 questions)
**Data Quality**: 100% validity
**Target**: 2,233 questions (16 systems, 6 question types)

**Active Development**:
- Implementing Question ID discovery algorithm (6 question types)
- Extracting all 16 systems (currently 8/16 with partial data)
- Preparing Phase 2 (Intelligent Fact Extraction via Claude)

See [PHASE_1_PLAN.md](docs/project/PHASE_1_PLAN.md) for detailed roadmap with timelines and success criteria.

## License

Medical education question extraction for personal study purposes.

## Questions?

Refer to documentation:
- [Quick Start](docs/rust/setup.md)
- [Common Issues](docs/rust/troubleshooting.md)
- [Architecture](docs/rust/architecture.md)
