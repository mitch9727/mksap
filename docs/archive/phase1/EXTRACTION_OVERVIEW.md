# Rust MKSAP Extractor - Overview

> **Phase 1 Status**: ✅ COMPLETE (December 27, 2025) - All 2,198 valid questions extracted. See
> [PHASE_1_COMPLETION_REPORT.md](../PHASE_1_COMPLETION_REPORT.md) for details.

## Purpose

The Rust MKSAP Extractor is the primary tool for extracting medical education questions from the ACP MKSAP (Medical
Knowledge Self-Assessment Program) question bank via direct API calls.

## Current Status

- **Implementation Status**: Phase 1 complete - All 2,198 questions extracted
- **System Coverage**: 16 system codes (cv, en, fc, cs, gi, hp, hm, id, in, dm, np, nr, on, pm, cc, rm)
- **Question Types**: 6 types supported (mcq, qqq, vdx, cor, mqq, sq)
- **Extraction Method**: Discovery-based validation using HTTP HEAD requests
- **Data Quality**: 100% coverage with comprehensive validation framework
- **Valid Questions**: 2,198 (invalidated questions excluded)

To view current counts and completion ratios:

```bash
./target/release/mksap-extractor discovery-stats
./target/release/mksap-extractor validate
```

## Extraction Approach

### API-Based Method
The Rust extractor uses direct HTTPS API calls to the MKSAP backend:

1. **Authentication** - Session-based cookie authentication
2. **Discovery** - Identifies all question IDs for each system
3. **Extraction** - Downloads complete question data as JSON
4. **Validation** - Verifies data quality and completeness

### Key Advantages

- **Speed** - Significantly faster than browser automation
- **Efficiency** - Minimal bandwidth overhead
- **Reliability** - Direct API access without UI rendering
- **Resumable** - Can continue from last successful extraction
- **Validated** - Built-in data quality checks

## Technology Stack

- **Language**: Rust 2021 Edition
- **Runtime**: Tokio (async/await)
- **HTTP Client**: reqwest
- **HTML Parsing**: scraper, select
- **Serialization**: serde, serde_json
- **Logging**: tracing, tracing-subscriber

## Data Output

### Directory Structure
```
mksap_data/
├── .checkpoints/
│   ├── discovery_metadata.json
│   └── {system}_ids.txt
├── cv/                              # Cardiovascular
│   ├── cvmcq24001/
│   │   └── cvmcq24001.json         # Complete question
│   └── ... (more questions)
├── en/ ├── hm/
├── id/
├── np/
├── nr/
├── on/
└── rm/
```

### JSON Schema
Each question contains:
- Question ID and category
- Clinical scenario (stimulus)
- Question stem (prompt)
- Multiple choice options (A, B, C, D)
- Correct answer (in `user_performance`)
- Detailed critique/explanation
- Key learning points
- Academic references (with PMIDs)
- Educational objectives
- Metadata (care types, high value care, update date)
- Media arrays (populated by integrated media commands)

## When to Use This Tool

**Use the Rust Extractor when:**
- You need bulk extraction of multiple questions
- You want fast, efficient API-based access
- You prefer direct validation and data quality checks
- You're automating large extraction runs
- You need to resume interrupted sessions

The Rust extractor is the only supported extraction path for this project.

## Known Issues

No known abbreviation mismatches in current extraction output. Interdisciplinary Medicine uses `in` for question IDs
while the web path remains `/dmin/`.

## Next Steps

1. Re-run validation after any extractor changes: `./target/release/mksap-extractor validate`
2. Use `media-discover` and `media-download` to fill missing figures/tables
3. Review `mksap_data/validation_report.txt` and `mksap_data_failed/` for issues
4. Move downstream into Phase 2 statement generation when data is clean

## Related Documentation

- [Setup Guide](RUST_SETUP.md) - Installation and configuration
- [Usage Guide](RUST_USAGE.md) - How to run the extractor
- [Validation](VALIDATION.md) - Data quality verification
- [Architecture](RUST_ARCHITECTURE.md) - Technical implementation details
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
