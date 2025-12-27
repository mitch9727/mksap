# CLAUDE.md

> **Last Updated**: December 27, 2025

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**MKSAP Question Bank Extractor** - Production-grade CLI data extraction system for downloading medical education questions from the ACP MKSAP (Medical Knowledge Self-Assessment Program) online question bank into structured JSON format.

**Primary Language**: Rust 2021 Edition with Tokio async runtime
**Architecture**: Dual-extractor system (text + media post-processing)
**Extraction Status**: 2,198 questions extracted (98.4% complete)
**Validation**: Discovery-based extraction using API HEAD requests
**Check Progress**: Run `./target/release/mksap-extractor validate` for current metrics

## Important: System Codes vs Browser Organization

This codebase works with **16 two-letter system codes** (cv, en, fc, cs, gi, hp, hm, id, in, dm, np, nr, on, pm, cc, rm) that appear in question IDs and API endpoints. These are NOT the same as the 12 content area groupings visible in the MKSAP browser interface.

The browser shows 12 content areas, but some content areas contain multiple system codes:
- **"Gastroenterology AND Hepatology"** → gi (Gastroenterology) + hp (Hepatology)
- **"Pulmonary AND Critical Care"** → pm (Pulmonary Medicine) + cc (Critical Care Medicine)
- **"General Internal Medicine"** → in (Interdisciplinary Medicine) + dm (Dermatology)
- **"Foundations of Clinical Practice"** → fc (Foundations of Clinical Practice) + cs (Common Symptoms)

All extraction, validation, and reporting in this codebase is organized by these 16 system codes, not the 12 browser groupings.

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

### Running Text Extraction

```bash
# Run main text extractor (default command)
./target/release/mksap-extractor

# Run with session cookie override
MKSAP_SESSION=<cookie> ./target/release/mksap-extractor

# Validate extracted data
./target/release/mksap-extractor validate

# Show discovery statistics (API availability metrics)
./target/release/mksap-extractor discovery-stats

# Standardize existing JSON data (updates to latest schema)
./target/release/mksap-extractor standardize

# Standardize with dry-run (preview changes)
./target/release/mksap-extractor standardize --dry-run

# Standardize specific system only
./target/release/mksap-extractor standardize --system cv

# Clean up duplicate questions
./target/release/mksap-extractor cleanup-duplicates

# Retry missing JSON files
./target/release/mksap-extractor retry-missing

# List remaining question IDs
./target/release/mksap-extractor list-missing

# Inspect API response for a question (debugging)
INSPECT_API=cvmcq24001 ./target/release/mksap-extractor
```

### Running Media Extraction

```bash
cd /Users/Mitchell/coding/projects/MKSAP/media_extractor

# Discover media references in all questions
./target/release/media-extractor discover --discovery-file media_discovery.json

# Download all media assets
./target/release/media-extractor download --all --data-dir ../mksap_data --discovery-file media_discovery.json

# Download media for specific question
./target/release/media-extractor download --question-id cvmcq24001 --data-dir ../mksap_data --discovery-file media_discovery.json

# Download with session override
MKSAP_SESSION=<cookie> ./target/release/media-extractor download --all --data-dir ../mksap_data --discovery-file media_discovery.json

# Browser-based extraction (videos and SVGs)
./target/release/media-extractor browser --all --data-dir ../mksap_data --discovery-file media_discovery.json

# Browser extraction with options
./target/release/media-extractor browser \
  --all \
  --data-dir ../mksap_data \
  --discovery-file media_discovery.json \
  --headless \
  --interactive-login \
  --login-timeout-secs 600

# Skip specific media types
./target/release/media-extractor download --all --skip-figures --data-dir ../mksap_data
./target/release/media-extractor browser --all --skip-videos --data-dir ../mksap_data

# Backfill inline table metadata
./target/release/media-extractor backfill-inline-tables --data-dir ../mksap_data
```

### Development

```bash
# Format code
cargo fmt

# Check compilation without building
cargo check

# Run with debug logging
RUST_LOG=debug ./target/release/mksap-extractor

# Filter out HTML parser noise
RUST_LOG=debug,html5ever=off ./target/release/mksap-extractor

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

# View discovery statistics
./target/release/mksap-extractor discovery-stats
```

## Project Architecture

### Dual-Extractor System

This project uses **two separate Rust binaries** working in sequence:

1. **text_extractor** (`mksap-extractor`) - Main extraction tool
   - Direct HTTPS API calls to `https://mksap.acponline.org/api/questions/<id>.json`
   - Session cookie authentication with browser fallback
   - Three-phase pipeline: discovery → directory setup → extraction
   - Rate-limited concurrent extraction (14 concurrent workers)
   - Checkpoint-based resumable extraction
   - Built-in data validation and standardization

2. **media_extractor** - Post-processing enrichment
   - Downloads embedded media (images, videos, SVGs, tables)
   - Updates JSON with media asset references
   - Browser automation for video/SVG extraction
   - Runs after text extraction completes

### Text Extractor Module Organization

**Total: 19 modules, 3,667 lines of code**

#### Core Extraction Pipeline (1,816 lines)
- **main.rs** (241 lines) - CLI entry point and command dispatch
- **workflow.rs** (208 lines) - Three-phase pipeline orchestration (discovery → setup → extraction)
- **discovery.rs** (282 lines) - Question ID discovery using HTTP HEAD requests with checkpointing
- **extractor.rs** (97 lines) - Core extraction type and concurrent processing
- **io.rs** (291 lines) - File I/O operations and checkpoint management
- **retry.rs** (232 lines) - Retry logic with exponential backoff for transient failures
- **standardize.rs** (334 lines) - Data standardization utilities for schema consistency
- **cleanup.rs** (131 lines) - Duplicate question detection and removal

#### Data Models & Configuration (699 lines)
- **models.rs** (499 lines) - Data structures (QuestionData, ApiQuestionResponse, MediaFiles, etc.)
- **config.rs** (200 lines) - 16 system code definitions with baselines and year ranges

#### Authentication & API (413 lines)
- **auth.rs** (108 lines) - Session-based API authentication
- **browser.rs** (198 lines) - Browser-based fallback authentication (Chrome/Firefox)
- **auth_flow.rs** (70 lines) - Authentication flow coordination
- **api.rs** (37 lines) - API interaction helpers

#### Validation & Reporting (626 lines)
- **validator.rs** (530 lines) - Comprehensive data quality validation and reporting
- **reporting.rs** (96 lines) - Discovery statistics and progress reporting

#### Utilities & CLI (113 lines)
- **diagnostics.rs** (55 lines) - Diagnostic utilities
- **categories.rs** (30 lines) - Category/system code helpers
- **commands.rs** (28 lines) - CLI command definitions

### Media Extractor Module Organization

**Total: 9 modules, 3,361 lines of code**

#### Core Components (2,007 lines)
- **main.rs** (212 lines) - CLI entry point with subcommand routing
- **cli.rs** (112 lines) - Command-line argument parsing using Clap
- **file_store.rs** (643 lines) - Question metadata and media file management
- **download.rs** (511 lines) - Figure and table downloading with retry logic
- **api.rs** (172 lines) - API interaction helpers
- **session.rs** (357 lines) - Session management and authentication

#### Browser Automation (1,354 lines)
- **browser.rs** (800 lines) - Browser-based video/SVG extraction
- **browser_download.rs** (729 lines) - Browser automation for media download
- **browser_media/** (subdirectory) - Browser media handling modules
  - `mod.rs` - Module organization
  - `videos.rs` - Video extraction logic
  - `svgs.rs` - SVG extraction logic

#### Discovery Management
- **discovery/** (subdirectory) - Discovery result management
  - `mod.rs` - Module organization
  - `helpers.rs` - Discovery utilities
  - `scanner.rs` - Media reference scanning
  - `statistics.rs` - Discovery statistics tracking

### Question System Codes

The extractor targets **16 question system codes** defined in [text_extractor/src/config.rs](text_extractor/src/config.rs):

```rust
pub struct OrganSystem {
    pub id: String,                    // Two-letter system code (cv, en, fc, cs, etc.)
    pub name: String,                  // Display name
    pub baseline_2024_count: u32,      // Historical baseline (informational only)
}
```

**System Code Inventory** (16 codes):

| Code | System | Baseline 2024 | Current Extracted |
|------|--------|---------------|-------------------|
| cv   | Cardiovascular Medicine | 216 | 240 |
| en   | Endocrinology and Metabolism | 136 | 160 |
| fc   | Foundations of Clinical Practice | 0 | 36 |
| cs   | Common Symptoms | 0 | 98 |
| gi   | Gastroenterology | 77 | 77 |
| hp   | Hepatology | 77 | 0 (combined with gi) |
| hm   | Hematology | 125 | 130 |
| id   | Infectious Disease | 205 | 215 |
| in   | Interdisciplinary Medicine | 100 | 0 (combined with dm) |
| dm   | Dermatology | 99 | 104 |
| np   | Nephrology | 155 | 160 |
| nr   | Neurology | 118 | 125 |
| on   | Oncology | 103 | 108 |
| pm   | Pulmonary Medicine | 131 | 140 |
| cc   | Critical Care Medicine | 55 | 54 |
| rm   | Rheumatology | 131 | 135 |

**Note**: Baseline counts are informational only. Actual question availability is determined via API discovery (HTTP HEAD requests), stored in `.checkpoints/discovery_metadata.json`.

### Question ID Pattern

Question IDs follow a deterministic pattern using system codes:

```
{system_code}{type}{year}{sequential_number}

Examples:
- cvmcq24001  (cv = Cardiovascular Medicine, MCQ, 2024, #1)
- enmcq25042  (en = Endocrinology, MCQ, 2025, #42)
- idvdx24003  (id = Infectious Disease, Video Diagnosis, 2024, #3)
- fcmcq24001  (fc = Foundations of Clinical Practice, MCQ, 2024, #1)
- cscor25001  (cs = Common Symptoms, Correlation, 2025, #1)
```

**Supported question types**: mcq, qqq, vdx, cor, mqq, sq

### Three-Phase Extraction Pipeline

The extraction follows a **three-phase async pipeline** orchestrated by [workflow.rs](text_extractor/src/workflow.rs):

```
PHASE 1: DISCOVERY (discovery.rs)
├─ Generate question IDs using pattern: {code}{type}{year}{num}
├─ HTTP HEAD requests to check existence
├─ Collect valid IDs (200 OK responses)
├─ Save to checkpoint: .checkpoints/{system}_ids.txt
└─ Log: "✓ Found {count} valid questions"

PHASE 2: DIRECTORY SETUP (workflow.rs)
├─ Create question directories for all valid IDs
├─ Path: mksap_data/{system}/{question_id}/
└─ Silent operation (no debug logging unless RUST_LOG=debug)

PHASE 3: EXTRACTION (extractor.rs)
├─ Concurrent extraction (14 workers via buffer_unordered)
├─ GET /api/questions/{id}.json
├─ Deserialize ApiQuestionResponse
├─ Transform to QuestionData
├─ Save {question_id}.json
├─ Skip if already extracted (unless --refresh-existing)
├─ Progress logging every 10 questions
└─ Retry on transient errors (retry.rs)

VALIDATION (on demand)
├─ Scan all extracted questions (validator.rs)
├─ Check JSON structure and required fields
├─ Compare extracted vs discovered counts
└─ Generate validation_report.txt
```

### Authentication Flow

**Session Cookie Management** ([auth.rs](text_extractor/src/auth.rs), [browser.rs](text_extractor/src/browser.rs)):

```rust
// Priority order:
1. MKSAP_SESSION environment variable  // Highest priority
2. Browser fallback authentication     // Interactive login
```

**Authentication Steps**:
1. Check for `MKSAP_SESSION` environment variable
2. If not found, launch browser (Chrome/Firefox)
3. Navigate to MKSAP login page
4. Wait for user to complete login (5-minute timeout)
5. Extract `_mksap19_session` cookie from browser
6. Configure HTTP client with authenticated session

**Important**:
- Session cookies expire after ~24 hours
- Browser fallback has 5-minute timeout (configurable)
- Cookie should be 100-200 characters, alphanumeric
- Supports Chrome and Firefox (automatic detection)

### Resumable Extraction

**Checkpoint System** ([io.rs](text_extractor/src/io.rs), [discovery.rs](text_extractor/src/discovery.rs)):

**Checkpoint types**:
1. **Discovery checkpoints** - `.checkpoints/{system}_ids.txt`
   - List of discovered valid question IDs
   - Prevents re-running expensive HEAD requests
   - One checkpoint per system code

2. **Discovery metadata** - `.checkpoints/discovery_metadata.json`
   - Statistics: discovered count, candidates tested, hit rate
   - Question types found per system
   - Discovery timestamp

3. **Extraction state** - Tracked via existing JSON files
   - Each extracted question has `{question_id}.json`
   - Extractor skips questions with existing JSON (unless `--refresh-existing`)

**Behavior**:
- Safe to Ctrl+C and resume at any time
- Discovery phase uses cached IDs if available
- Extraction phase skips completed questions
- Failed extractions moved to `mksap_data_failed/`
- No data loss on interruption

### Output Structure

Each question stored in its own directory:

```
mksap_data/
├── .checkpoints/                    # Resume state
│   ├── discovery_metadata.json     # API discovery statistics
│   ├── cv_ids.txt                  # Discovered IDs per system
│   ├── en_ids.txt
│   └── ...
├── cv/                              # Cardiovascular system
│   ├── cvmcq24001/
│   │   ├── cvmcq24001.json         # Complete structured data
│   │   ├── figures/                # Downloaded images
│   │   │   ├── cvfig24201.<hash>.jpg
│   │   │   └── cvfig24202.<hash>.jpg
│   │   ├── tables/                 # HTML tables
│   │   ├── videos/                 # MP4 videos
│   │   └── svgs/                   # SVG graphics
│   ├── cvmcq24002/
│   └── ...
├── en/                              # Endocrinology system
├── fc/                              # Foundations system
└── validation_report.txt            # Data quality report
```

### JSON Schema

**QuestionData structure** ([text_extractor/src/models.rs](text_extractor/src/models.rs)):

```rust
pub struct QuestionData {
    pub question_id: String,              // Unique ID (e.g., "cvmcq24001")
    pub category: String,                 // System code (e.g., "cv")
    pub educational_objective: String,    // Learning goal
    pub metadata: QuestionMetadata,       // Care types, patient types, HVC flags
    pub question_text: String,            // Clinical scenario (HTML)
    pub question_stem: String,            // Question being asked
    pub options: Vec<QuestionOption>,     // Answer choices with peer %
    pub user_performance: UserPerformance, // Correct answer and user results
    pub critique: String,                 // Detailed explanation
    pub critique_links: Vec<Value>,       // External references
    pub key_points: Vec<String>,          // Clinical takeaways
    pub references: String,               // Medical literature citations
    pub related_content: RelatedContent,  // Syllabus and learning plan refs
    pub media: MediaFiles,                // Images, SVGs, tables, videos
    pub media_metadata: MediaMetadata,    // Detailed media information
    pub extracted_at: String,             // ISO 8601 timestamp
}
```

**Key fields**:
- `question_id` - Unique identifier (e.g., "cvmcq24001")
- `category` - Organ system code (e.g., "cv")
- `question_text` - Clinical scenario (HTML with nested JSON nodes)
- `question_stem` - Actual question being asked
- `options[]` - Answer choices with peer percentages
- `user_performance` - Correct answer and user results
- `critique` - Detailed explanation (HTML)
- `educational_objective` - Learning goal
- `key_points[]` - Clinical takeaways (bullets)
- `references` - Medical literature citations
- `metadata` - Care types, patient types, high-value care flags, update timestamp
- `media` - Simple file paths (images, svgs, tables, videos)
- `media_metadata` - Detailed metadata (IDs, types, captions)
- `related_content` - Syllabus references and learning plan topics
- `extracted_at` - ISO 8601 timestamp

### Validation Framework

**Built-in validator** ([text_extractor/src/validator.rs](text_extractor/src/validator.rs)):

```bash
./target/release/mksap-extractor validate
```

**Validation checks**:
1. **JSON structure validity** - Parseable and well-formed
2. **Required field presence** - All mandatory fields exist
3. **Field completeness** - Critique, educational objective, key points
4. **Extraction counts** - Extracted vs discovered per system
5. **Media references** - Images/videos referenced but not downloaded
6. **Duplicate detection** - Questions extracted multiple times

**Output**: `mksap_data/validation_report.txt`

**Report sections**:
- Per-system extraction statistics (count, percentage)
- Missing questions (discovered but not extracted)
- Over-extracted systems (more than discovered)
- Field completeness analysis
- Data quality warnings

### Rate Limiting & Retry Logic

**Server-friendly extraction** ([retry.rs](text_extractor/src/retry.rs), [extractor.rs](text_extractor/src/extractor.rs)):

**Rate limiting**:
- **500ms delay** between discovery HEAD requests (configurable)
- **14 concurrent workers** for extraction (Tokio buffer_unordered)
- **60-second backoff** on HTTP 429 (rate limit) responses
- Respects server load by limiting concurrency

**Retry strategy** (retry.rs):
- **Exponential backoff** for transient errors
- **Max 3 retries** per request
- Retryable errors:
  - HTTP 429 (rate limit)
  - HTTP 5xx (server errors)
  - Connection timeouts
  - Connection resets
  - DNS failures
- Non-retryable errors:
  - HTTP 404 (not found)
  - HTTP 401/403 (auth errors)
  - Invalid JSON responses

**Concurrency**:
```rust
// Auto-detected from system (max 16)
let concurrency = num_cpus::get().min(16);
```

### Discovery-Based Metrics

**API Discovery** ([discovery.rs](text_extractor/src/discovery.rs)):

The extractor **doesn't use hardcoded question counts**. Instead, it:

1. **Generates candidate IDs** using patterns:
   - System codes: cv, en, fc, cs, etc.
   - Question types: mcq, qqq, vdx, cor, mqq, sq
   - Years: 2024-2025 (configurable via `MKSAP_YEAR_START`, `MKSAP_YEAR_END`)
   - Numbers: 1-150 per combination

2. **Tests candidates** via HTTP HEAD requests:
   - 200 OK → question exists
   - 404 Not Found → skip
   - Other errors → skip (invalidated questions)

3. **Saves results** to `.checkpoints/`:
   - `{system}_ids.txt` - List of valid IDs
   - `discovery_metadata.json` - Statistics

4. **Reports metrics**:
   ```bash
   ./target/release/mksap-extractor discovery-stats
   ```

**Discovery metadata** (example):
```json
{
  "systems": {
    "cv": {
      "discovered": 240,
      "candidates_tested": 41958,
      "hit_rate": 0.0057,
      "types_found": ["mcq", "qqq", "vdx", "cor"]
    }
  },
  "total_discovered": 2198,
  "discovery_timestamp": "2025-12-27T00:00:00Z"
}
```

### Technology Stack

**Core Dependencies** ([text_extractor/Cargo.toml](text_extractor/Cargo.toml)):

**Async Runtime & HTTP**:
- **tokio** (1.x) - Async runtime with full features (rt-multi-thread, macros)
- **reqwest** (0.11) - HTTP client with JSON support, cookies, gzip
- **futures** (0.3) - Stream combinators for concurrent processing

**Parsing & Serialization**:
- **scraper** (0.17) - CSS selector-based HTML parsing
- **serde** + **serde_json** (1.x) - JSON serialization/deserialization
- **regex** (1.x) - Pattern matching for ID generation

**Error Handling & Logging**:
- **anyhow** (1.x) - Simplified error handling with context
- **tracing** + **tracing-subscriber** (0.3) - Structured logging with levels

**Utilities**:
- **chrono** (0.4) - Date/time operations for timestamps
- **dotenv** (0.15) - Environment variable loading from .env files
- **num_cpus** (1.x) - CPU count detection for concurrency
- **walkdir** (2.x) - Recursive directory traversal

**Media Extractor Additional Dependencies**:
- **clap** (4.x) - Command-line argument parsing with derive macros
- **thirtyfour** (0.31) - WebDriver protocol for browser automation
- **image** (0.24) - Image processing and format detection
- **blake3** (1.x) - Fast hashing for media deduplication

## Downstream Processing

Downstream formatting (fact extraction, card generation) is outside the current extraction scope.

## Common Issues

### Authentication

**Session expired**:
```bash
rm -f ~/.mksap_session  # Clear cached session (if exists)
MKSAP_SESSION=<new_cookie> ./target/release/mksap-extractor
```

**Browser timeout** (5 minutes):
- Increase timeout in [text_extractor/src/browser.rs](text_extractor/src/browser.rs)
- Or manually extract cookie from browser DevTools:
  1. Login to MKSAP in browser
  2. Open DevTools (F12)
  3. Application tab → Cookies → `_mksap19_session`
  4. Copy value
  5. `MKSAP_SESSION=<value> ./target/release/mksap-extractor`

**Browser not found**:
- Install Chrome or Firefox
- Ensure browser is in PATH
- Check browser driver compatibility

### Network

**Rate limiting (429)**:
- Extractor automatically retries with 60-second backoff
- If persistent, increase delay in [retry.rs](text_extractor/src/retry.rs)
- Run during off-peak hours (evenings, weekends)
- Only run one extractor instance at a time

**Timeouts**:
- Check network speed: `speedtest-cli`
- Increase timeout in [retry.rs](text_extractor/src/retry.rs)
- Enable debug logging: `RUST_LOG=debug ./target/release/mksap-extractor`

**Connection resets**:
- Automatically retried by retry logic
- If frequent, check firewall/VPN settings
- Try different network connection

### Data Quality

**Invalid JSON**:
```bash
# Identify corrupted question
./target/release/mksap-extractor validate

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

# Fix schema inconsistencies
./target/release/mksap-extractor standardize
```

**Duplicate questions**:
```bash
# Find and remove duplicates
./target/release/mksap-extractor cleanup-duplicates

# Verify cleanup
./target/release/mksap-extractor validate
```

**Missing media**:
```bash
# Run media extractor
cd ../media_extractor
./target/release/media-extractor discover --discovery-file media_discovery.json
./target/release/media-extractor download --all --data-dir ../mksap_data --discovery-file media_discovery.json

# For videos/SVGs (requires browser)
./target/release/media-extractor browser --all --data-dir ../mksap_data --discovery-file media_discovery.json
```

### Compilation

**Build errors**:
```bash
# Clean and rebuild
cargo clean
cargo build --release

# Check for dependency issues
cargo update
cargo check
```

**Outdated toolchain**:
```bash
# Update Rust
rustup update stable

# Verify version (Rust 2021 edition requires 1.56+)
rustc --version
```

## Testing

**Current approach**: Manual testing + validation framework

No automated test suite yet. Validation is performed via:

```bash
# Run extraction
./target/release/mksap-extractor

# Validate output
./target/release/mksap-extractor validate

# Check discovery statistics
./target/release/mksap-extractor discovery-stats

# Review reports
cat mksap_data/validation_report.txt
```

**Manual testing checklist**:
1. Run extraction on single system: modify config.rs
2. Validate JSON structure: check validation_report.txt
3. Verify media downloads: check figures/ directories
4. Test resume functionality: Ctrl+C during extraction, re-run
5. Check discovery metrics: discovery-stats command

## Documentation

**Comprehensive guides** in `docs/`:

### Getting Started
- **[QUICKSTART.md](docs/project/QUICKSTART.md)** - Fast command reference
- **[RUST_SETUP.md](docs/reference/RUST_SETUP.md)** - Installation and configuration
- **[RUST_USAGE.md](docs/reference/RUST_USAGE.md)** - How to run extraction

### Technical Deep Dives
- **[RUST_ARCHITECTURE.md](docs/reference/RUST_ARCHITECTURE.md)** - Implementation details
- **[VALIDATION.md](docs/reference/VALIDATION.md)** - Data quality framework
- **[TROUBLESHOOTING.md](docs/reference/TROUBLESHOOTING.md)** - Common issues and solutions

### Project Planning
- **[README.md](docs/project/README.md)** - Project overview and status
- **[PHASE_1_PLAN.md](docs/project/PHASE_1_PLAN.md)** - Phase 1 execution roadmap
- **[PROJECT_ORGANIZATION.md](docs/architecture/PROJECT_ORGANIZATION.md)** - 4-phase pipeline overview
- **[PROJECT_TODOS.md](docs/project/PROJECT_TODOS.md)** - Master todo list

### Reference
- **[QUESTION_ID_DISCOVERY.md](docs/reference/QUESTION_ID_DISCOVERY.md)** - Understanding question counts
- **[EXTRACTOR_STATUS.md](docs/reference/EXTRACTOR_STATUS.md)** - Current extraction progress
- **[DESERIALIZATION_ISSUES.md](docs/reference/DESERIALIZATION_ISSUES.md)** - API response variations

### Reports & History
- **[reports/](docs/project/reports/)** - Extraction summaries and gap analysis
- **[CHANGELOG.md](docs/project/CHANGELOG.md)** - Documentation changes

## Development Workflow

### Making Changes

1. **Read relevant modules** - Architecture is modular and well-documented
2. **Test locally** - Run extraction on a single system (modify config.rs)
3. **Validate output** - Use built-in validator
4. **Check conventions** - Follow Rust 2021 style (run `cargo fmt`)

### Code Organization Principles

**DRY (Don't Repeat Yourself)**:
- System codes defined once in config.rs
- Authentication logic in auth.rs, used by both extractors
- Retry logic in retry.rs, shared across HTTP operations

**Separation of Concerns**:
- Discovery (discovery.rs) separate from extraction (extractor.rs)
- File I/O (io.rs) separate from business logic
- Validation (validator.rs) separate from extraction

**Error Handling**:
- Use `anyhow::Result` for fallible operations
- Add context with `.context("description")`
- Log errors with `tracing::error!`
- Retry transient errors with retry.rs helpers

### Commit Guidelines

This project follows **Conventional Commits**:

- `feat: ...` - New features (e.g., "feat: add standardize command")
- `fix: ...` - Bug fixes (e.g., "fix: handle invalidated questions")
- `chore: ...` - Maintenance tasks (e.g., "chore: update dependencies")
- `docs: ...` - Documentation changes (e.g., "docs: update CLAUDE.md")
- `refactor: ...` - Code restructuring (e.g., "refactor: extract auth flow")

**Example commits**:
```bash
git commit -m "feat: add discovery-stats command for API metrics"
git commit -m "fix: retry on connection reset errors"
git commit -m "docs: update module organization in CLAUDE.md"
```

### Security Considerations

**Never commit**:
- Session cookies (`_mksap19_session`)
- Authentication tokens
- User credentials
- Environment files with secrets (.env)

**Prefer**:
- Environment variables (`MKSAP_SESSION`)
- Browser-based authentication fallback
- Prompting for credentials at runtime
- .env.example templates (no actual secrets)

**Best practices**:
- Add sensitive files to .gitignore
- Use dotenv for local development
- Document required environment variables
- Never log sensitive data

## Key Design Principles

1. **Discovery-Driven** - Adapts to current API state, not hardcoded baselines
2. **Resumability** - Extraction can be interrupted and resumed without data loss
3. **Rate Limiting** - Respects server load with configurable delays and concurrency
4. **Validation** - Built-in data quality checks at multiple stages
5. **Modularity** - Clear separation of concerns across 19 modules
6. **Async-First** - Tokio runtime enables efficient concurrent operations
7. **Error Recovery** - Transient errors automatically retried; failed questions quarantined
8. **Observability** - Structured logging with tracing, debug mode for diagnostics

## Next Steps for Contributors

### For New Users
1. Follow [RUST_SETUP.md](docs/reference/RUST_SETUP.md) for installation
2. Review [QUICKSTART.md](docs/project/QUICKSTART.md) for basic commands
3. Run validation to understand current state: `./target/release/mksap-extractor validate`

### For Development
1. Read [RUST_ARCHITECTURE.md](docs/reference/RUST_ARCHITECTURE.md) for technical details
2. Check [TROUBLESHOOTING.md](docs/reference/TROUBLESHOOTING.md) for common issues
3. Review module organization above to understand codebase structure

### For Extraction
1. Build project: `cd text_extractor && cargo build --release`
2. Run extraction: `./target/release/mksap-extractor`
3. Validate results: `./target/release/mksap-extractor validate`
4. Run media extraction: `cd ../media_extractor && cargo build --release`
5. Download media: `./target/release/media-extractor download --all --data-dir ../mksap_data`

## Current Status

**Project Phase**: Phase 1 - Data Extraction (100% complete)
**Extraction Method**: Discovery-based API extraction
**Total Questions**: 2,198 valid questions extracted from 16 system codes (invalidated excluded)
**Validation Status**: Run `./target/release/mksap-extractor validate` for latest metrics
**Next Phase**: Phase 2 - Fact Extraction (LLM-based processing)

**Check Progress**:
```bash
# Validation report
./target/release/mksap-extractor validate

# Discovery statistics
./target/release/mksap-extractor discovery-stats

# Per-system counts
for dir in mksap_data/*/; do echo "$(basename $dir): $(ls $dir | wc -l)"; done
```

---

**Last Updated**: December 27, 2025
**Project Status**: Active development - Phase 1 (Data Extraction)
**Repository**: git@github.com:mitch9727/mksap.git
**Extraction Progress**: 2,198 questions (100% complete)
