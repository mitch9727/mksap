# MKSAP Extractor System Manual

**Last Updated**: January 29, 2026
**Component**: Rust Extractor (Phase 1)
**Binary**: `mksap-extractor`

---

## 1. System Overview

The **MKSAP Extractor** is a high-performance Rust application designed to discover, extract, and enrich medical questions from the ACP MKSAP platform. It serves as the data ingestion layer (Phase 1) for the statement generation pipeline.

### Core Capabilities
- **Discovery-Driven**: Automatically identifies valid question IDs via HTTP probes (no hardcoded lists).
- **Unified Pipeline**: Single binary handles text extraction, media downloading (images/tables), and validation.
- **Resumable**: Checkpoint system allows interruption and resumption without data loss.
- **Async & Concurrent**: Uses `tokio` runtime to process 14+ streams concurrently.
- **Browser Integration**: Automatic browser fallback for session authentication and SVG/Video extraction.

---

## 2. Architecture & Pipeline

The extraction process follows a strict **three-phase pipeline** to ensure data integrity.

### Phase 1: Discovery
1.  **Generation**: Generates candidate IDs based on patterns (e.g., `cvmcq24001`).
    *   System Codes: `cv`, `en`, `fc`, `cs`, `gi`, `hp`, `hm`, `id`, `in`, `dm`, `np`, `nr`, `on`, `pm`, `cc`, `rm` (16 total).
    *   Types: `mcq`, `qqq`, `vdx`, `cor`, `mqq`, `sq`.
2.  **Probing**: Sends HTTP HEAD requests to validate existence.
3.  **Checkpointing**: Saves valid IDs to `.checkpoints/{system}_ids.txt` and stats to `discovery_metadata.json`.

### Phase 2: Directory Setup
*   Creates the physical directory structure under `mksap_data/{system}/{question_id}/`.

### Phase 3: Extraction
*   **Concurrent Fetch**: 14 workers (default) fetch JSON from `/api/questions/{id}.json`.
*   **Deserialization**: Maps API response to the internal `QuestionData` struct.
*   **Normalization**: cleans HTML, standardizes option keys, and extracts metadata.
*   **Asset Pipeline**:
    *   Downloads referenced images to `figures/`.
    *   Extracts HTML tables to `tables/`.
    *   Uses browser automation to render and save SVGs to `svgs/`.

---

## 3. Codebase Guide

This section helps developers navigate the `extractor/` crate source code.

### Key Modules (`extractor/src/`)
| Module | Purpose |
|--------|---------|
| `main.rs` | CLI entry point and runtime bootstrap. |
| `cli.rs` | `clap` argument definitions and command routing. |
| `workflow.rs` | Orchestrates the 3-phase pipeline (Discovery → Setup → Extraction). |
| `extractor.rs` | Core logic for fetching, transforming, and saving question JSON. |
| `discovery.rs` | ID generation patterns and HTTP HEAD probing logic. |
| `asset_*.rs` | Suite of modules for handling media (discovery, download, SVG rendering). |
| `auth.rs` | Session cookie management and browser login fallback. |
| `models.rs` | Data structures for API responses and internal `QuestionData`. |

### Tracing Execution
1.  **Start**: `main.rs` initializes the logger and calls `cli::run()`.
2.  **Routing**: `cli::run()` matches the subcommand (e.g., `extract`, `validate`) and calls the handler in `commands.rs`.
3.  **Work**:
    *   `commands::extract()` initializes the `Workflow` strut.
    *   `Workflow::run()` drives the 3 phases sequentially.
2.  **Data**: Extracted data flows from `extractor.rs` (fetch) → `models.rs` (struct) → Disk (JSON).

---

## 4. CLI Reference

Build the release binary before running:
```bash
cd extractor
cargo build --release
```

### Core Commands

**1. Run Full Extraction**
Default mode. Runs discovery (if needed) and extracts all missing questions.
```bash
./target/release/mksap-extractor
```

**2. Validate Data**
Checks extracted JSON against discovery metadata and schema rules.
```bash
./target/release/mksap-extractor validate
```

**3. Discovery Statistics**
Shows hit rates and counts from the last discovery run.
```bash
./target/release/mksap-extractor discovery-stats
```

**4. Media Tools**
```bash
# Discover which questions have media assets
./target/release/mksap-extractor media-discover

# Download valid assets
./target/release/mksap-extractor media-download
```

---

## 5. Configuration

Configuration is managed via `.env` file or environment variables.

### Critical Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `MKSAP_SESSION` | Authenticated session cookie (`_mksap19_session`). | *None* (Triggers browser login if missing) |
| `MKSAP_CONCURRENCY` | Number of concurrent extraction workers. | `14` |
| `MKSAP_YEAR_START` | Start year for ID generation. | `24` (2024) |
| `MKSAP_YEAR_END` | End year for ID generation. | `25` (2025) |
| `RUST_LOG` | Logging verbosity. | `info` (Use `debug` for tracing) |

### Session Management
If `MKSAP_SESSION` is not set, the tool attempts to launch a browser (Chrome/Firefox) to capture the session cookie interactively.

---

## 6. Output Structure

All data is written to the `mksap_data/` directory.

```
mksap_data/
├── .checkpoints/               # Resume state & discovery stats
├── validation_report.txt       # QA report
├── cv/                         # System folder (Cardiovascular)
│   ├── cvmcq24001/
│   │   ├── cvmcq24001.json     # The Question Data
│   │   ├── figures/            # Images
│   │   ├── tables/             # HTML Tables
│   │   └── svgs/               # SVG Assets
│   └── ...
└── ...
```

**JSON Schema**:
The output JSON contains fields for `question_stem`, `options`, `critique`, `key_points`, and `related_content`. See `extractor/src/models.rs` for the exact type definitions.
