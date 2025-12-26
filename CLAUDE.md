# CLAUDE.md

> **Last Updated**: December 26, 2025

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**MKSAP Question Bank Extractor** - CLI data extraction tool for downloading medical education questions from the ACP MKSAP (Medical Knowledge Self-Assessment Program) online question bank into structured JSON format.

**Primary Language**: Rust 2021 Edition with Tokio async runtime
**Architecture**: Dual-extractor system (text + media post-processing)
**Validation**: Discovery-based extraction using API HEAD requests
**Check Progress**: Run `./target/release/mksap-extractor validate` for current metrics

## Common Commands

### Building

```bash
# Build text extractor (main tool)
cd /Users/Mitchell/coding/projects/MKSAP/text_extractor
cargo build --release

# Build media extractor (post-processing)
cd /Users/Mitchell/coding/projects/MKSAP/media_extractor
cargo build --release

# Note: Extractors are independent crates, not a workspace
# Each must be built separately from its own directory
```

### Running Extraction

```bash
# Run main text extractor
./target/release/mksap-extractor

# Validate extracted data
./target/release/mksap-extractor validate

# Override session cookie
MKSAP_SESSION=<cookie> ./target/release/mksap-extractor

# Media post-processing
cargo build --release -p media-extractor
./target/release/media-extractor
# Or with custom path:
./target/release/media-extractor /path/to/mksap_data
```

### Development

```bash
# Format code
cargo fmt

# Check compilation without building
cargo check

# Clean build artifacts (frees ~2GB)
cargo clean

# Update dependencies
cargo update
```

### Monitoring Progress

```bash
# Count extracted questions by system
for dir in mksap_data/*/; do echo "$(basename $dir): $(ls $dir | wc -l)"; done

# Watch extraction in real-time
watch -n 1 'ls mksap_data/cv | wc -l'

# View validation report
cat mksap_data/validation_report.txt
```

## Project Architecture

### Dual-Extractor System

This project uses **two separate Rust binaries** working in sequence:

1. **text_extractor** (`mksap-extractor`) - Main extraction tool
   - Direct HTTPS API calls to `https://mksap.acponline.org/api/questions/<id>.json`
   - Session cookie authentication
   - Rate-limited concurrent extraction
   - Checkpoint-based resumable extraction
   - Built-in data validation

2. **media_extractor** - Post-processing enrichment
   - Downloads embedded media (images, videos, SVGs, tables)
   - Updates JSON with media asset references
   - Runs after text extraction completes

### Module Organization (text_extractor)

**Critical modules** (2,458 total lines):

- **main.rs** (351 lines) - Entry point, CLI orchestration, authentication flow
- **extractor.rs** (1,062 lines) - Core extraction logic: discovery → download → media
- **validator.rs** (376 lines) - Data quality validation and reporting
- **models.rs** (311 lines) - Data structures (QuestionData, ApiQuestionResponse, etc.)
- **config.rs** (81 lines) - **12 organ systems** with codes and expected question counts
- **browser.rs** (107 lines) - Browser-based authentication fallback
- **media.rs** (83 lines) - Media asset downloading
- **utils.rs** (87 lines) - Text processing and HTML parsing

### Organ System Configuration

The extractor targets **15 medical organ systems** defined in [text_extractor/src/config.rs](text_extractor/src/config.rs):

```rust
pub struct OrganSystem {
    pub id: String,                    // Filesystem code (cv, en, cs, etc.)
    pub name: String,                  // Full name
    pub question_prefixes: Vec<String>, // Question ID prefixes
    pub baseline_2024_count: u32,      // Historical baseline (informational only)
}
```

**Configured System Prefixes** (15 total):
- **cv** - Cardiovascular Medicine
- **en** - Endocrinology and Metabolism
- **cs** - Foundations of Clinical Practice and Common Symptoms
- **gi** - Gastroenterology
- **hp** - Hepatology
- **hm** - Hematology
- **id** - Infectious Disease
- **in** - Interdisciplinary Medicine
- **dm** - Dermatology
- **np** - Nephrology
- **nr** - Neurology
- **on** - Oncology
- **pm** - Pulmonary Medicine
- **cc** - Critical Care Medicine
- **rm** - Rheumatology

**Note**: Baseline counts are informational only. Actual question availability is determined via API discovery (HTTP HEAD requests), stored in `.checkpoints/discovery_metadata.json`.

### Question ID Pattern

Question IDs follow a deterministic pattern:
```
{api_code}{type}{year}{sequential_number}

Examples:
- cvmcq24001  (Cardiovascular, MCQ, 2024, #1)
- enmcq25042  (Endocrinology, MCQ, 2025, #42)
- idvdx24003  (Infectious Disease, Video Diagnosis, 2024, #3)
```

**Supported question types**: mcq, qqq, vdx, cor, mqq, sq

### Extraction Pipeline

The extraction follows a **three-phase** async pipeline (see [docs/reference/RUST_ARCHITECTURE.md](docs/reference/RUST_ARCHITECTURE.md)):

```
1. AUTHENTICATE
   ├─ Check MKSAP_SESSION environment variable
   ├─ Try saved session cookie
   └─ Fallback to browser login (5 minute timeout)

2. FOR EACH SYSTEM
   ├─ DISCOVER PHASE
   │  ├─ Generate question IDs (pattern-based)
   │  ├─ HEAD requests to check existence
   │  └─ Collect valid IDs
   │
   ├─ EXTRACT PHASE
   │  ├─ GET /api/questions/{id}.json
   │  ├─ Deserialize and transform
   │  ├─ Save {question_id}.json
   │  ├─ Save {question_id}_metadata.txt
   │  └─ Write checkpoint
   │
   └─ MEDIA PHASE (optional)
      ├─ Extract media URLs from question
      ├─ Download files
      └─ Save to figures/ subdirectory

3. VALIDATE (on demand)
   ├─ Scan all extracted questions
   ├─ Check JSON structure and required fields
   └─ Generate validation_report.txt
```

### Authentication Flow

**Session Cookie Management** ([text_extractor/src/main.rs](text_extractor/src/main.rs)):

```rust
// Priority order:
1. MKSAP_SESSION environment variable  // Highest priority
2. Hardcoded SESSION_COOKIE in main.rs // Default (in source)
3. Browser fallback authentication     // Opens Chrome/Firefox
```

**Important**:
- Session cookies expire after ~24 hours
- Browser fallback has 5-minute timeout
- Cookie should be 100-200 characters, alphanumeric

### Resumable Extraction

**Checkpoint System** prevents re-downloading:
- Checkpoints stored in `mksap_data/.checkpoints/`
- Tracks successfully extracted questions per system
- Failed extractions moved to `mksap_data_failed/`
- Safe to Ctrl+C and resume

### Output Structure

Each question stored in its own directory:

```
mksap_data/
├── .checkpoints/          # Resume state
├── cv/                    # Cardiovascular system
│   └── cvmcq24001/
│       ├── cvmcq24001.json              # Complete structured data
│       ├── cvmcq24001_metadata.txt      # Human-readable summary
│       └── figures/                     # Downloaded media (if any)
│           ├── cvfig24201.<hash>.jpg
│           └── cvfig24202.<hash>.jpg
└── validation_report.txt  # Data quality report
```

### JSON Schema

**QuestionData structure** ([text_extractor/src/models.rs](text_extractor/src/models.rs)):

Key fields:
- `question_id` - Unique identifier (e.g., "cvmcq24001")
- `category` - Organ system code (e.g., "cv")
- `question_text` - Clinical scenario (nested JSON nodes)
- `question_stem` - Actual question being asked
- `options[]` - Answer choices with peer percentages
- `user_performance` - Correct answer and user results
- `critique` - Detailed explanation
- `educational_objective` - Learning goal
- `key_points[]` - Clinical takeaways
- `references` - Medical literature citations
- `metadata` - Care types, patient types, high-value care flags
- `media` - Images, SVGs, tables, videos
- `related_content` - Syllabus references
- `extracted_at` - ISO 8601 timestamp

### Validation Framework

**Built-in validator** ([text_extractor/src/validator.rs](text_extractor/src/validator.rs)):

```bash
./target/release/mksap-extractor validate
```

Checks:
- JSON structure validity
- Required field presence
- Expected vs. actual question counts per system
- Critique and educational objective completeness
- Missing media references

Generates: `mksap_data/validation_report.txt`

### Rate Limiting

**Server-friendly extraction** ([text_extractor/src/extractor.rs](text_extractor/src/extractor.rs)):

- **500ms delay** between requests (configurable)
- **60-second backoff** on HTTP 429 (rate limit)
- Automatic retry on transient errors
- Respects server load

### Technology Stack

**Core Dependencies** ([text_extractor/Cargo.toml](text_extractor/Cargo.toml)):

- **tokio** (1.x) - Async runtime with full features
- **reqwest** (0.11) - HTTP client with JSON support
- **scraper** (0.17) - CSS selector-based HTML parsing
- **serde** + **serde_json** (1.x) - JSON serialization
- **anyhow** (1.x) - Error handling
- **tracing** + **tracing-subscriber** - Structured logging
- **regex** (1.x) - Pattern matching
- **chrono** (0.4) - Date/time operations

## Downstream Processing

### MCQ Format Specification

Extracted JSON is designed for conversion to **Anki-ready Markdown flashcards** following a strict specification in [docs/specifications/MCQ_FORMAT.md](docs/specifications/MCQ_FORMAT.md).

**Key points**:
- Gold-standard markdown with machine-readable structure
- Stable heading order for CSV parsing
- System emojis for visual categorization
- True Statements (atomic, cloze-ready facts)
- Extra(s) for clarifications (numbered by parent statement)
- Supplemental materials (figures, videos, HTML tables)
- Hierarchical tagging for Anki deck organization

**Example output**: [docs/specifications/CVMCQ24041.md](docs/specifications/CVMCQ24041.md)

## Common Issues

### Authentication

**Session expired**:
```bash
rm -f ~/.mksap_session  # Clear cached session
MKSAP_SESSION=<new_cookie> ./target/release/mksap-extractor
```

**Browser timeout** (5 minutes):
- Increase `LOGIN_TIMEOUT_SECONDS` in [text_extractor/src/main.rs](text_extractor/src/main.rs)
- Or manually extract cookie from browser DevTools

### Network

**Rate limiting (429)**:
- Increase `REQUEST_DELAY_MS` in [text_extractor/src/extractor.rs](text_extractor/src/extractor.rs)
- Run during off-peak hours
- Only run one extractor instance

**Timeouts**:
- Check network speed: `speedtest-cli`
- Increase `REQUEST_TIMEOUT_SECS` in [text_extractor/src/main.rs](text_extractor/src/main.rs)

### Data Quality

**Invalid JSON**:
```bash
# Delete corrupted question
rm -rf mksap_data/cv/cvmcq24001/

# Re-extract (resumes from checkpoint)
./target/release/mksap-extractor
```

**Validation failures**:
```bash
# Check report
cat mksap_data/validation_report.txt

# Re-run validation
./target/release/mksap-extractor validate
```

## Testing

**Current approach**: Manual testing + validation framework

No automated test suite yet. Validation is performed via:
```bash
./target/release/mksap-extractor validate
```

Review `mksap_data/validation_report.txt` and `mksap_data_failed/` after changes.

## Documentation

**Comprehensive guides** in `docs/`:

- **Project Overview**: [docs/project/README.md](docs/project/README.md)
- **Quick Start**: [docs/project/QUICKSTART.md](docs/project/QUICKSTART.md)
- **Rust Setup**: [docs/reference/RUST_SETUP.md](docs/reference/RUST_SETUP.md)
- **Architecture**: [docs/reference/RUST_ARCHITECTURE.md](docs/reference/RUST_ARCHITECTURE.md)
- **Validation**: [docs/reference/VALIDATION.md](docs/reference/VALIDATION.md)
- **Troubleshooting**: [docs/reference/TROUBLESHOOTING.md](docs/reference/TROUBLESHOOTING.md)
- **MCQ Format**: [docs/specifications/MCQ_FORMAT.md](docs/specifications/MCQ_FORMAT.md)

## Development Workflow

### Making Changes

1. **Read relevant modules** - Architecture is modular and well-documented
2. **Test locally** - Run extraction on a single system
3. **Validate output** - Use built-in validator
4. **Check conventions** - Follow Rust 2021 style (run `cargo fmt`)

### Commit Guidelines

This project follows **Conventional Commits**:
- `feat: ...` - New features
- `chore: ...` - Maintenance tasks
- `fix: ...` - Bug fixes
- `docs: ...` - Documentation changes

### Security Considerations

**Never commit**:
- Session cookies (`_mksap19_session`)
- Authentication tokens
- User credentials

**Prefer**:
- Environment variables (`MKSAP_SESSION`)
- Prompting for credentials at runtime
- Browser-based authentication fallback

## Key Design Principles

1. **Resumability** - Extraction can be interrupted and resumed without data loss
2. **Rate Limiting** - Respects server load with configurable delays
3. **Validation** - Built-in data quality checks before downstream processing
4. **Modularity** - Clear separation between text extraction and media enrichment
5. **Async-First** - Tokio runtime enables efficient concurrent operations
6. **Error Recovery** - Transient errors automatically retried; failed questions quarantined

## Next Steps for Contributors

1. Review [docs/reference/RUST_ARCHITECTURE.md](docs/reference/RUST_ARCHITECTURE.md) for technical details
2. Understand the [MCQ Format Specification](docs/specifications/MCQ_FORMAT.md) for output format
3. Check [docs/project/README.md](docs/project/README.md) for current extraction progress and status
4. See [docs/reference/TROUBLESHOOTING.md](docs/reference/TROUBLESHOOTING.md) for common issues

---

**Last Updated**: December 26, 2025
**Project Status**: Active development - Phase 1 (Data Extraction)
**Check Progress**: Run `./target/release/mksap-extractor validate`
**Repository**: git@github.com:mitch9727/mksap.git
