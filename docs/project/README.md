# MKSAP Project Overview

## Project Goal

Extract the full MKSAP question bank into structured JSON using the Rust API-based extractor, then use that data for downstream processing (Markdown/Anki generation).

## Current Status

- Rust extractor is the primary and only supported extraction method.
- 754 / 1,810 questions extracted across 8 systems.
- Remaining systems: cc, gi, in, pm.

## Primary Tool

**Rust MKSAP Extractor** (project root)
- Direct API access with rate limiting and resume support
- Output organized under `mksap_data/`
- Built-in data validation

## Key Paths

- `src/` - Rust extractor source
- `mksap_data/` - Extracted JSON output by system
- `docs/rust/` - Setup, usage, and troubleshooting
- `docs/specifications/` - MCQ output format reference

## Next Steps

1. Complete extraction for missing systems.
2. Run validation reports.
3. Build downstream conversion pipeline (Markdown/Anki).
