# MKSAP Project Overview

## Overview

The MKSAP Question Bank Extractor uses a Rust-based API extraction system to download medical education questions from the ACP MKSAP online question bank into structured JSON format.

**Architecture**: Unified extractor with discovery-based validation
- **extractor**: Main extraction tool using direct API calls + integrated media pipeline

For historical extraction metrics, see [reports/](reports/) directory.

## Project Goal

Extract the full MKSAP question bank into structured JSON using the Rust API-based extractor, then use that data for downstream processing (Markdown/Anki generation).

## System Architecture

The extractor is configured to handle **16 question system codes** (see [config.rs](../../extractor/src/config.rs)):

**System Prefixes**:
- cv (Cardiovascular), en (Endocrinology), fc (Foundations), cs (Common Symptoms)
- gi (Gastroenterology), hp (Hepatology), hm (Hematology)
- id (Infectious Disease), in (Interdisciplinary), dm (Dermatology)
- np (Nephrology), nr (Neurology), on (Oncology)
- pm (Pulmonary), cc (Critical Care), rm (Rheumatology)

**Multi-Prefix Design**: Some ACP content areas combine multiple specialties (e.g., "Gastroenterology AND Hepatology" or "Foundations of Clinical Practice AND Common Symptoms"). The extractor separates these into individual systems with distinct prefixes (gi/hp, fc/cs) for accurate question ID discovery.

**Year Range**: Targets questions from 2023-2026 by default (override with `MKSAP_YEAR_START`/`MKSAP_YEAR_END`)

## Discovery-Based Extraction

The extractor uses **API HEAD request discovery** to determine which questions exist:

- **No hardcoded counts**: Discovers actual available questions via HTTP HEAD requests
- **Adapts to API changes**: Automatically accounts for retired/invalidated questions and new content
- **Metadata tracking**: Stores discovery statistics in `.checkpoints/discovery_metadata.json`
- **Validation**: Compares extracted count vs discovered count per system

This approach ensures extraction targets reflect the current API state, not outdated historical baselines.

## Primary Tool

**Rust MKSAP Extractor** (`extractor/`)
- Direct API access with rate limiting and resume support
- Output organized under `mksap_data/`
- Built-in discovery-based validation
- CLI commands for metadata inspection and media discovery/download

## Key Paths

- `extractor/src/` - Rust extractor source
- `mksap_data/` - Extracted JSON output by system
- `mksap_data/.checkpoints/discovery_metadata.json` - API discovery statistics
- `docs/reference/` - Setup, usage, and troubleshooting
- `docs/reference/EXTRACTION_OVERVIEW.md` - Extraction status and scope overview

## Discovery-Based Completion Tracking

### What Changed

Previously, completion percentages were based on hardcoded expected counts from MKSAP 2024:
```
Example (OLD):
CC: 55 extracted / 206 expected = 26.7% ❌ (misleading)
```

Now, percentages are based on actual API-discovered counts:
```
Example (NEW):
CC: 55 extracted / 54 discovered = 101.9% ✓ (accurate - fully extracted)
```

### How It Works

1. **Discovery Phase**: Each extraction run discovers available questions via HTTP HEAD requests
2. **Metadata Storage**: Statistics saved to `.checkpoints/discovery_metadata.json`:
   - Discovered count per system
   - Candidates tested (how many IDs were checked)
   - Hit rate (% of candidates that exist)
   - Question types found (mcq, qqq, vdx, cor, mqq, sq)
   - Discovery timestamp

3. **Validator Usage**: Completion metrics use discovered counts (required)
4. **Discovery Required**: Validation fails if discovery metadata is missing

### Viewing Discovery Statistics

```bash
# From extractor directory:
./target/release/mksap-extractor discovery-stats
```

Example output:
```
=== MKSAP Discovery Statistics ===

Overall:
  Total Discovered: 1,790 questions
  Total Candidates Tested: ~500,000
  Overall Hit Rate: 0.36%

Per-System Breakdown:
System Discovered      Candidates Hit Rate Types Found
cv         239           41958    0.57%    mcq,qqq,vdx,cor
en         159           41958    0.38%    mcq,qqq,vdx,cor
...
```

### Interpreting Results

- **100%+**: All discovered questions have been extracted (system complete)
- **90-99%**: Nearly complete - missing only a few questions
- **<90%**: Incomplete - extraction still in progress
- **⚠ Over-extracted**: More extracted than discovered (check for data issues)

### Why This Matters

The MKSAP API availability changes over time:
- Questions can be retired (marked as `invalidated`)
- New questions are added (2025 content)
- Historical baselines become stale

With API-driven metrics, the system automatically adapts to real API state without manual updates.

## Logging and Debugging

### Standard Output

The extractor produces clean, production-grade output by default:

```bash
# Run extraction or validation
./target/release/mksap-extractor

# Sample output (consolidated per-system results):
[1/16] Processing: Cardiovascular Medicine
✓ cv: Extracted 0 new, 240 already extracted

[2/16] Processing: Endocrinology and Metabolism
✓ en: Extracted 0 new, 160 already extracted
```

Output features:
- Discovery logs include candidate/tested counts and discovered IDs
- Extraction results: `✓ {system}: Extracted {new} new, {existing} already extracted`
- Errors and warnings are always displayed (independent of log level)
- No redundant category name repetition
- Silent directory creation (no per-file output)

### Debug Output

To see detailed phase-level logging (Phase 1, 2, 3 messages):

```bash
RUST_LOG=debug ./target/release/mksap-extractor
```

This enables:
- Discovery phase details: Which candidates are being tested, hit rate
- Directory creation logs: When question folders are created
- Extraction phase details: Concurrency level and progress
- All debug-level tracing information

Example debug output:
```
[DEBUG] Phase 1: Discovering valid questions for Cardiovascular Medicine...
[DEBUG] Phase 2: Creating directories for 240 questions...
[DEBUG] Phase 3: Extracting data for 240 questions (concurrency: 14)...
```

### Log Level Reference

| Level | Use Case |
|-------|----------|
| INFO (default) | Clean production output, discovery/extraction summaries |
| DEBUG | Detailed phase information, diagnostic details |
| WARN | Non-fatal issues (rate limiting, retries) |
| ERROR | Extraction failures, critical errors |

### Troubleshooting Output

If extraction appears to hang or produce unexpected results:

```bash
# Enable debug logging with timestamps
RUST_LOG=debug,html5ever=off ./target/release/mksap-extractor 2>&1 | tee extractor.log

# Search for error or warning messages
rg -i "error|warning|failed" extractor.log
```

## Next Steps

1. Run validation with new discovery-based metrics: `./target/release/mksap-extractor validate`
2. Review validation report for data integrity warnings
3. Monitor discovery hit rate to understand API question availability
4. Build downstream conversion pipeline (Markdown/Anki)
