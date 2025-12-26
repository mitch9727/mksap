# MKSAP Project Overview

## ⚠️ CRITICAL FIX (December 25, 2025)

**Question ID Prefix Mismatch Corrected**: The "Foundations of Clinical Practice and Common Symptoms" (CS) section was configured with wrong prefix "cc" instead of correct "cs". This has been fixed in config.rs. Next extraction run should discover ~206 questions instead of 55. See [EXTRACTION_GAPS_ANALYSIS.md](../../EXTRACTION_GAPS_ANALYSIS.md#critical-update-december-25-2025---evening-question-id-prefix-mismatch-discovery) for details.

## Project Goal

Extract the full MKSAP question bank into structured JSON using the Rust API-based extractor, then use that data for downstream processing (Markdown/Anki generation).

## Current Status

- Rust extractor is the primary and only supported extraction method.
- **1,802 questions extracted across 11 systems + 55 with incorrect prefix** (1,539 from 2024 + 289 from 2025)
- **Expected improvement**: CS section expected to increase from 55 to ~206 questions after re-extraction with correct prefix
- **Overall completion: 100.7%** (based on API-discovered question count: 1,790) - will improve after CS fix

## Completion Metrics (December 2025 Update)

The system now uses **API-discovered question counts** as the source of truth instead of hardcoded expectations. This means:

- **Accurate completion reporting**: Based on what actually exists in the API via discovery, not historical baselines
- **Dynamic adaptation**: Automatically accounts for retired/invalidated questions and new 2025 content
- **Data integrity checking**: Warns when extracted > discovered (possible checkpoint issues)

For detailed information, see [Discovery-Based Completion Tracking](#discovery-based-completion-tracking) below.

## Primary Tool

**Rust MKSAP Extractor** (project root)
- Direct API access with rate limiting and resume support
- Output organized under `mksap_data/`
- Built-in discovery-based validation
- CLI commands for metadata inspection

## Key Paths

- `text_extractor/src/` - Rust extractor source
- `mksap_data/` - Extracted JSON output by system
- `mksap_data/.checkpoints/discovery_metadata.json` - API discovery statistics
- `docs/reference/` - Setup, usage, and troubleshooting
- `docs/specifications/` - MCQ output format reference

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
   - Question types found (mcq, qqq, vdx, cor)
   - Discovery timestamp

3. **Validator Usage**: Completion metrics now use discovered counts when available
4. **Fallback**: Uses historical baseline if discovery metadata not found

### Viewing Discovery Statistics

```bash
# From text_extractor directory:
cargo run --release -- discovery-stats
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

## Next Steps

1. Run validation with new discovery-based metrics: `cargo run --release -- validate`
2. Review validation report for data integrity warnings
3. Monitor discovery hit rate to understand API question availability
4. Build downstream conversion pipeline (Markdown/Anki)
