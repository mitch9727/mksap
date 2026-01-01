# CLAUDE.md

> **Last Updated**: December 27, 2025

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**MKSAP Medical Education Pipeline** - Multi-phase system for extracting, processing, and generating medical education flashcards from ACP MKSAP (Medical Knowledge Self-Assessment Program) question bank.

**Project Structure**:
- **Phase 1 (Complete ✅)**: Rust extractor - 2,198 questions extracted to JSON
- **Phase 2 (Active)**: Python statement generator - LLM-based flashcard extraction
- **Phase 3 (Planned)**: Cloze application - Apply fill-in-the-blank formatting
- **Phase 4 (Planned)**: Anki export - Generate spaced repetition decks

**Primary Languages**: Rust 2021 (extractor), Python 3.9+ (statement_generator)
**Current Status**: Phase 1 complete, Phase 2 in development
**Total Questions**: 2,198 questions across 16 medical specialties

## Important: System Codes vs Browser Organization

This codebase works with **16 two-letter system codes** (cv, en, fc, cs, gi, hp, hm, id, in, dm, np, nr, on, pm, cc, rm) that appear in question IDs and API endpoints. These are NOT the same as the 12 content area groupings visible in the MKSAP browser interface.

The browser shows 12 content areas, but some content areas contain multiple system codes:
- **"Gastroenterology AND Hepatology"** → gi (Gastroenterology) + hp (Hepatology)
- **"Pulmonary AND Critical Care"** → pm (Pulmonary Medicine) + cc (Critical Care Medicine)
- **"General Internal Medicine"** → in (Interdisciplinary Medicine) + dm (Dermatology)
- **"Foundations of Clinical Practice"** → fc (Foundations of Clinical Practice) + cs (Common Symptoms)

All extraction, validation, and reporting in this codebase is organized by these 16 system codes, not the 12 browser groupings.

## Quick Navigation

- **Phase 1 (Rust Extractor)**: See commands in [extractor section](#building) below
- **Phase 2 (Statement Generator)**: See [docs/reference/STATEMENT_GENERATOR.md](docs/reference/STATEMENT_GENERATOR.md)
- **Architecture**: [Project Architecture](#project-architecture) section
- **Troubleshooting**: [Common Issues](#common-issues) section

## Phase 1: Rust Extractor

### Building

```bash
# Build extractor (text + media)
cd /path/to/MKSAP/extractor
cargo build --release
```

### Running Extraction

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
./target/release/mksap-extractor cleanup-flat

# Retry missing JSON files
./target/release/mksap-extractor retry-missing

# List remaining question IDs
./target/release/mksap-extractor list-missing

# Inspect API response (debugging)
MKSAP_INSPECT_API=1 ./target/release/mksap-extractor
```

### Running Media Extraction (Integrated)

```bash
# Discover media references in all questions
./target/release/mksap-extractor media-discover

# Download all media assets
./target/release/mksap-extractor media-download --all

# Download media for specific question
./target/release/mksap-extractor media-download --question-id cvmcq24001

# Download with session override
MKSAP_SESSION=<cookie> ./target/release/mksap-extractor media-download --all

# Browser-based extraction (videos and SVGs)
./target/release/mksap-extractor svg-browser --all

# Browser extraction with options
./target/release/mksap-extractor svg-browser \
  --all \
  --headless \
  --interactive-login \
  --login-timeout-secs 600

# Skip specific media types
./target/release/mksap-extractor media-download --all --skip-figures
./target/release/mksap-extractor svg-browser --all --skip-videos
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

### Unified Extractor System

This project uses a **single Rust binary** that combines text extraction with media enrichment:

- Direct HTTPS API calls to `https://mksap.acponline.org/api/questions/<id>.json`
- Session cookie authentication with browser fallback
- Three-phase pipeline: discovery → directory setup → extraction
- Checkpoint-based resumable extraction
- Integrated media discovery/download (figures/tables), with browser automation for video/SVGs

### Extractor Module Organization

#### CLI & Orchestration
- Initialization and environment setup
- CLI option parsing and command definitions
- Command routing and execution runners
- Shared utilities (env parsing, progress logging)

#### Core Extraction Pipeline
- Core extraction type and concurrent processing
- Three-phase pipeline orchestration (discovery → setup → extraction)
- Question ID discovery using HTTP HEAD requests with checkpointing
- File I/O operations and checkpoint management
- Retry logic with exponential backoff for transient failures
- Data standardization utilities for schema consistency
- Duplicate question detection and removal

#### Data Models & Configuration
- Data structures (QuestionData, ApiQuestionResponse, MediaFiles, etc.)
- System code definitions (discovery metadata is the source of truth)

#### Authentication & API
- Session-based API authentication
- Browser-based fallback authentication (Chrome/Firefox)
- Session cookie helpers
- HTTP client configuration
- API endpoint construction

#### Validation & Reporting
- Comprehensive data quality validation and reporting
- Discovery statistics and progress reporting

#### Asset Subsystem
- Asset discovery and statistics
- Figure/table download pipeline
- SVG browser automation
- JSON/media updates and table rendering
- Asset metadata + content ID parsing
- Shared session cookie helpers

### Question System Codes

The extractor targets **16 question system codes** defined in the configuration module:

```rust
pub struct OrganSystem {
    pub id: String,                    // Two-letter system code (cv, en, fc, cs, etc.)
    pub name: String,                  // Display name
}
```

Discovery metadata in `.checkpoints/discovery_metadata.json` is the source of
truth for available counts and timestamps. Historical baselines are archived in
[docs/archive/DEPRECATED_BASELINE_COUNTS.md](docs/archive/DEPRECATED_BASELINE_COUNTS.md).

**System Code Inventory** (16 codes):

| Code | System |
|------|--------|
| cv   | Cardiovascular Medicine |
| en   | Endocrinology and Metabolism |
| fc   | Foundations of Clinical Practice |
| cs   | Common Symptoms |
| gi   | Gastroenterology |
| hp   | Hepatology |
| hm   | Hematology |
| id   | Infectious Disease |
| in   | Interdisciplinary Medicine |
| dm   | Dermatology |
| np   | Nephrology |
| nr   | Neurology |
| on   | Oncology |
| pm   | Pulmonary Medicine |
| cc   | Critical Care Medicine |
| rm   | Rheumatology |

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

The extraction follows a **three-phase async pipeline** orchestrated by the workflow component:

```
PHASE 1: DISCOVERY
├─ Generate question IDs using pattern: {code}{type}{year}{num}
├─ HTTP HEAD requests to check existence
├─ Collect valid IDs (200 OK responses)
├─ Save to checkpoint: .checkpoints/{system}_ids.txt
└─ Log: "✓ Found {count} valid questions"

PHASE 2: DIRECTORY SETUP
├─ Create question directories for all valid IDs
├─ Path: mksap_data/{system}/{question_id}/
└─ Silent operation (no debug logging unless RUST_LOG=debug)

PHASE 3: EXTRACTION
├─ Concurrent extraction (14 workers via buffer_unordered)
├─ GET /api/questions/{id}.json
├─ Deserialize ApiQuestionResponse
├─ Transform to QuestionData
├─ Save {question_id}.json
├─ Skip if already extracted (unless --refresh-existing)
├─ Progress logging every 10 questions
└─ Retry on transient errors

VALIDATION (on demand)
├─ Scan all extracted questions
├─ Check JSON structure and required fields
├─ Compare extracted vs discovered counts
└─ Generate validation_report.txt
```

### Authentication Flow

**Session Cookie Management** (auth subsystem with browser fallback):

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

**Checkpoint System** (I/O + discovery subsystems):

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

**QuestionData structure**:

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

**Built-in validator**:

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

**Server-friendly extraction**:

**Rate limiting**:
- **500ms delay** between discovery HEAD requests (configurable)
- **14 concurrent workers** for extraction (Tokio buffer_unordered)
- **60-second backoff** on HTTP 429 (rate limit) responses
- Respects server load by limiting concurrency

**Retry strategy**:
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

**API Discovery** (discovery subsystem):

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

**Core Dependencies** (extractor crate manifest):

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

## Phase 2: Statement Generator

Phase 2 extracts testable medical facts from MKSAP questions using LLM-powered analysis. It processes the JSON output from Phase 1 and augments each question with structured flashcard statements.

**Key Features**:
- 4-phase pipeline: critique extraction -> key points extraction -> cloze identification -> text normalization
- Multi-provider LLM support (Anthropic API, Claude Code CLI, Gemini CLI, Codex CLI)
- Evidence-based flashcard design aligned with spaced repetition best practices
- Non-destructive JSON updates (adds `true_statements` field only)
- Checkpoint-based resumable processing with atomic saves

### Common Commands

```bash
cd statement_generator

# Test on 1-2 questions
python -m src.main process --mode test --system cv

# Test specific question
python -m src.main process --question-id cvmcq24001

# Production: Process all 2,198 questions
python -m src.main process --mode production

# Use CLI providers (avoid API costs)
python -m src.main process --provider claude-code --mode test
python -m src.main process --provider gemini --mode test
python -m src.main process --provider codex --mode test

# Adjust temperature (default 0.2)
python -m src.main process --temperature 0.5 --question-id cvmcq24001

# Re-process already completed questions
python -m src.main process --force --question-id cvmcq24001

# Preview without API calls
python -m src.main process --dry-run --system cv

# Debug logging
python -m src.main process --log-level DEBUG --question-id cvmcq24001
```

### Management Commands

```bash
# Show statistics
python -m src.main stats

# Reset checkpoints
python -m src.main reset

# Clean old log files (keeps last 7 days)
python -m src.main clean-logs
python -m src.main clean-logs --keep-days 3
python -m src.main clean-logs --dry-run

# Clean all logs and reset checkpoints
python -m src.main clean-all
```

### Development

```bash
# Install dependencies
pip install -r statement_generator/requirements.txt

# Test a single question without saving
python -m src.main process --dry-run --question-id cvmcq24001
```

### High-Level Architecture

#### 4-Phase Pipeline Design

```
PHASE 1: Critique Extraction
- Input: critique field (300-800 words of medical explanation)
- Output: 3-7 atomic statements
- Constraint: Extract ONLY facts explicitly stated in the critique

PHASE 2: Key Points Extraction
- Input: key_points array (0-3 pre-formatted bullets)
- Output: 1-3 refined statements
- Constraint: Minimal rewriting, same anti-hallucination rules

PHASE 3: Cloze Identification
- Input: All statements from phases 1-2
- Output: 2-5 cloze candidates per statement
- Strategy: Modifier splitting (e.g., "mild" and "hypercalcemia")

PHASE 4: Text Normalization
- Input: Statements with cloze candidates
- Output: Normalized symbols ("less than" -> "<", "greater than" -> ">")

FINAL: JSON Augmentation
- Add true_statements field to existing question JSON
- Preserve all original fields (non-destructive)
- Checkpoint each processed question
```

#### Multi-Provider Abstraction

```
BaseLLMProvider
-> AnthropicProvider
-> ClaudeCodeProvider
-> GeminiProvider
-> CodexProvider
```

#### Provider Selection and Fallback

- Provider settings (model, temperature, keys) are loaded via `--provider` or `LLM_PROVIDER`.
- Processing uses a provider manager with fallback order: claude-code -> codex -> anthropic -> gemini.
- User confirmation is required before switching providers on rate limits.

#### Checkpoint/Resume System

- Checkpoint file: `statement_generator/outputs/checkpoints/processed_questions.json`
- Tracks processed and failed question IDs
- Atomic writes with batch saves (default: every 10 questions)
- Safe to interrupt and resume without data loss

#### Non-Destructive JSON Updates

- Adds `true_statements` without modifying any existing fields
- Preserves all media metadata, question text, and performance data
- Allows re-running Phase 2 without re-extracting data

### Evidence-Based Flashcard Design

Prompts follow research-backed principles from `docs/reference/CLOZE_FLASHCARD_BEST_PRACTICES.md`:

1. Atomic facts (one concept per statement)
2. Anti-hallucination constraints (source-only extraction)
3. Modifier splitting for clinically important qualifiers
4. Clinical context in `extra_field` only when source provides it
5. Concise phrasing (remove patient-specific fluff)
6. Avoid enumerations (chunk lists into overlapping clozes)
7. Multiple cloze candidates per statement (2-5)

### Output Structure

Each question JSON is augmented with:

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

Field semantics:
- `statement`: Full sentence without cloze blanks
- `extra_field`: Clinical context or null if not provided by source
- `cloze_candidates`: 2-5 terms to blank in Phase 3

### Module Organization

**Core Pipeline Modules**:
- Pipeline orchestration (critique → key points → cloze → normalization)
- Critique statement extraction
- Key points statement extraction
- Cloze candidate identification
- Text normalization

**Infrastructure Modules**:
- CLI entry point and orchestration
- Configuration and environment loading
- JSON read/write and augmentation helpers
- Resume/checkpoint management
- Multi-provider client wrapper
- Provider fallback orchestration
- Pydantic data models

**Provider Implementations**:
- Anthropic API (API key required)
- Claude Code CLI (subscription)
- Gemini CLI (subscription)
- OpenAI CLI (subscription)

### Critical Design Constraints

- Sequential processing only (LLM-bound, simpler error handling, avoids rate limits)
- Low temperature default (0.2) to minimize hallucination
- Non-destructive JSON updates (Phase 1 data is treated as immutable)
- Checkpoint batching for I/O efficiency and safe resume

### Troubleshooting (Statement Generator)

**Provider setup issues**:
- Claude CLI missing: install Claude Code CLI or set `CLAUDE_CLI_PATH`
- Gemini CLI missing: install `google-generativeai` or set `GEMINI_CLI_PATH`
- OpenAI CLI missing: install `openai` or set `OPENAI_CLI_PATH`
- Anthropic API key missing: set `ANTHROPIC_API_KEY` in project `.env`

**Processing issues**:
- Reset checkpoint: `python -m src.main reset`
- Re-process questions: `python -m src.main process --force --system cv`
- Remove logs: `python -m src.main clean-logs`

**Data quality issues**:
- Hallucinated facts: lower temperature, review prompts, compare to critique
- Missing facts: verify they appear in critique or key_points
- Invalid JSON response: inspect statement generator logs

### Known Limitations

1. Some CLI providers ignore temperature settings
2. No automated validation framework yet
3. No extraction from wrong-answer explanations
4. No extraction from media (figures/tables captions)
5. No scenario extraction from question_text
6. Sequential-only processing (no parallelism)

### References

- `docs/reference/STATEMENT_GENERATOR.md`
- `docs/reference/CLOZE_FLASHCARD_BEST_PRACTICES.md`
- `docs/project/PHASE_2_STATUS.md`

## Multi-Phase Pipeline Overview

The MKSAP project follows a **4-phase sequential pipeline**:

### Phase 1: Question Extraction (Complete ✅)
**Technology**: Rust
**Input**: MKSAP API (https://mksap.acponline.org)
**Output**: 2,198 structured JSON files (one per question)
**Documentation**: This file (CLAUDE.md)

**Key Outputs**:
- question_id, category, critique, key_points
- question_text, question_stem, options
- educational_objective, references
- media files (figures, tables, videos, SVGs)

### Phase 2: Statement Generation (Active 🔄)
**Technology**: Python 3.9+ with LLM providers
**Input**: Phase 1 JSON files
**Output**: Augmented JSONs with `true_statements` field
**Documentation**: [docs/reference/STATEMENT_GENERATOR.md](docs/reference/STATEMENT_GENERATOR.md)

**Process**:
- Extract testable facts from critique
- Extract facts from key_points
- Identify cloze deletion candidates (2-5 per statement)
- Normalize mathematical notation

### Phase 3: Cloze Application (Planned 📋)
**Technology**: TBD (likely Python)
**Input**: Phase 2 JSONs with true_statements
**Output**: Formatted flashcards with [...] blanks applied

**Process**:
- Apply cloze deletions based on cloze_candidates
- Generate multiple cards per statement (one per candidate)
- Preserve extra_field for context

### Phase 4: Anki Export (Planned 📋)
**Technology**: TBD (Python + genanki or similar)
**Input**: Phase 3 formatted flashcards
**Output**: Anki deck (.apkg) with media assets

**Process**:
- Generate Anki note types
- Link media files (figures, tables, videos, SVGs)
- Apply spaced repetition metadata
- Package into importable deck

## Common Issues

### Authentication

**Session expired**:
```bash
rm -f ~/.mksap_session  # Clear cached session (if exists)
MKSAP_SESSION=<new_cookie> ./target/release/mksap-extractor
```

**Browser timeout** (5 minutes):
- Increase the browser login timeout in the auth settings
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
- If persistent, increase the retry delay in the retry settings
- Run during off-peak hours (evenings, weekends)
- Only run one extractor instance at a time

**Timeouts**:
- Check network speed: `speedtest-cli`
- Increase timeout in the retry settings
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
./target/release/mksap-extractor cleanup-flat

# Verify cleanup
./target/release/mksap-extractor validate
```

**Missing media**:
```bash
# Run media discovery/download
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download --all

# For videos/SVGs (requires browser)
./target/release/mksap-extractor svg-browser --all
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
1. Run extraction on a single system: use configuration or CLI filtering
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
- **[PHASE_1_COMPLETION_REPORT.md](docs/project/PHASE_1_COMPLETION_REPORT.md)** ✅ - Phase 1 results (100% complete)
- **[PROJECT_ORGANIZATION.md](docs/architecture/PROJECT_ORGANIZATION.md)** - 4-phase pipeline overview
- **[EXTRACTION_SCOPE.md](docs/project/EXTRACTION_SCOPE.md)** - Extraction scope definition

### Reference
- **[QUESTION_ID_DISCOVERY.md](docs/project/archive/phase-1/QUESTION_ID_DISCOVERY.md)** - Historical question discovery analysis
- **[EXTRACTION_OVERVIEW.md](docs/reference/EXTRACTION_OVERVIEW.md)** - Extraction implementation overview
- **[DESERIALIZATION_ISSUES.md](docs/reference/DESERIALIZATION_ISSUES.md)** - API response variations

### Reports & History
- **[reports/](docs/project/reports/)** - Extraction summaries and gap analysis
- **[CHANGELOG.md](docs/project/CHANGELOG.md)** - Documentation changes
- **[archive/](docs/project/archive/)** - Archived planning documents (Phase 1, completed tasks, planning sessions)

## Development Workflow

### Making Changes

1. **Read relevant modules** - Architecture is modular and well-documented
2. **Test locally** - Run extraction on a single system (config or CLI filter)
3. **Validate output** - Use built-in validator
4. **Check conventions** - Follow Rust 2021 style (run `cargo fmt`)

### Code Organization Principles

**DRY (Don't Repeat Yourself)**:
- System codes defined once in the configuration module
- Authentication logic centralized in the auth subsystem
- Retry logic centralized for shared HTTP operations

**Separation of Concerns**:
- Discovery separate from extraction
- File I/O separate from business logic
- Validation separate from extraction

**Error Handling**:
- Use `anyhow::Result` for fallible operations
- Add context with `.context("description")`
- Log errors with `tracing::error!`
- Retry transient errors with retry helpers

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
1. Build project: `cd extractor && cargo build --release`
2. Run extraction: `./target/release/mksap-extractor`
3. Validate results: `./target/release/mksap-extractor validate`
4. Run media discovery: `./target/release/mksap-extractor media-discover`
5. Download media: `./target/release/mksap-extractor media-download --all`

## Current Status

**Overall Project**: Multi-phase medical education pipeline
**Phase 1 (Extractor)**: ✅ Complete - 2,198 questions extracted
**Phase 2 (Statements)**: 🔄 Active - LLM-based flashcard generation in development
**Phase 3 (Cloze)**: 📋 Planned - Flashcard formatting
**Phase 4 (Anki)**: 📋 Planned - Deck export

**Phase 1 Details**:
- **Completion Date**: December 27, 2025
- **Extraction Method**: Discovery-based API extraction
- **Total Questions**: 2,198 across 16 medical specialties
- **Validation**: Run `./target/release/mksap-extractor validate`
- **Report**: [PHASE_1_COMPLETION_REPORT.md](docs/project/PHASE_1_COMPLETION_REPORT.md)

**Phase 2 Status**:
- **Implementation**: ~90% complete (see [docs/project/PHASE_2_STATUS.md](docs/project/PHASE_2_STATUS.md))
- **Remaining**: Provider testing, validation framework
- **Documentation**: [docs/reference/STATEMENT_GENERATOR.md](docs/reference/STATEMENT_GENERATOR.md)

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

**Last Updated**: December 31, 2025
**Primary Maintainer**: Mitchell
**Repository**: git@github.com:mitch9727/mksap.git
**Phase 1 Status**: ✅ Complete (2,198 questions)
**Phase 2 Status**: 🔄 Active (statement generator in development)
