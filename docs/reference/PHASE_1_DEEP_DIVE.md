# Phase 1: Rust Extractor - Deep Technical Dive

> This is the detailed architecture guide for Phase 1. For quick commands, see [QUICKSTART.md](../project/QUICKSTART.md).

## Overview

Phase 1 extracts 2,198 MKSAP questions from the ACP API into structured JSON files with integrated media assets.

## Unified Extractor System

This project uses a **single Rust binary** that combines text extraction with media enrichment:

- Direct HTTPS API calls to `https://mksap.acponline.org/api/questions/<id>.json`
- Session cookie authentication with browser fallback
- Three-phase pipeline: discovery → directory setup → extraction
- Checkpoint-based resumable extraction
- Integrated media discovery/download (figures/tables), with browser automation for video/SVGs

## Extractor Module Organization

### CLI & Orchestration
- Initialization and environment setup
- CLI option parsing and command definitions
- Command routing and execution runners
- Shared utilities (env parsing, progress logging)

### Core Extraction Pipeline
- Core extraction type and concurrent processing
- Three-phase pipeline orchestration (discovery → setup → extraction)
- Question ID discovery using HTTP HEAD requests with checkpointing
- File I/O operations and checkpoint management
- Retry logic with exponential backoff for transient failures
- Data standardization utilities for schema consistency
- Duplicate question detection and removal

### Data Models & Configuration
- Data structures (QuestionData, ApiQuestionResponse, MediaFiles, etc.)
- System code definitions (discovery metadata is the source of truth)

### Authentication & API
- Session-based API authentication
- Browser-based fallback authentication (Chrome/Firefox)
- Session cookie helpers
- HTTP client configuration
- API endpoint construction

### Validation & Reporting
- Comprehensive data quality validation and reporting
- Discovery statistics and progress reporting

### Asset Subsystem
- Asset discovery and statistics
- Figure/table download pipeline
- SVG browser automation
- JSON/media updates and table rendering
- Asset metadata + content ID parsing
- Shared session cookie helpers

## Question System Codes

The extractor targets **16 question system codes** defined in the configuration module:

```rust
pub struct OrganSystem {
    pub id: String,                    // Two-letter system code (cv, en, fc, cs, etc.)
    pub name: String,                  // Display name
}
```

Discovery metadata in `.checkpoints/discovery_metadata.json` is the source of
truth for available counts and timestamps. Historical baselines are archived in
[docs/archive/DEPRECATED_BASELINE_COUNTS.md](../../archive/DEPRECATED_BASELINE_COUNTS.md).

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

## Question ID Pattern

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

## Three-Phase Extraction Pipeline

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

## Authentication Flow

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

## Resumable Extraction

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

## Output Structure

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

## JSON Schema

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

## Validation Framework

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

## Rate Limiting & Retry Logic

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

## Discovery-Based Metrics

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

## Technology Stack

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

## Key Design Principles

1. **Discovery-Driven** - Adapts to current API state, not hardcoded baselines
2. **Resumability** - Extraction can be interrupted and resumed without data loss
3. **Rate Limiting** - Respects server load with configurable delays and concurrency
4. **Validation** - Built-in data quality checks at multiple stages
5. **Modularity** - Clear separation of concerns across 19 modules
6. **Async-First** - Tokio runtime enables efficient concurrent operations
7. **Error Recovery** - Transient errors automatically retried; failed questions quarantined
8. **Observability** - Structured logging with tracing, debug mode for diagnostics

---

**Last Updated**: January 5, 2026
**Status**: ✅ Complete (2,198 questions extracted)
