# Rust MKSAP Extractor - Overview

## Purpose

The Rust MKSAP Extractor is the primary tool for extracting medical education questions from the ACP MKSAP (Medical Knowledge Self-Assessment Program) question bank via direct API calls.

## Current Status

- **Questions Extracted**: 754 / 2,233 (34% of target)
- **Systems with Data**: 8 of 16 organ systems (partial)
- **Question Types**: 1 of 6 types fully supported (mcq, cor, vdx, qqq, mqq, sq needed)
- **Implementation Status**: Phase 1 - Data Extraction (see [PHASE_1_PLAN.md](../project/PHASE_1_PLAN.md))
- **Last Updated**: December 25, 2025

**Note**: 1,810 question count was based on incomplete question type coverage. Complete count is 2,233 across 16 systems and 6 question types. See [Question ID Discovery](../Question%20ID%20Discovery.md) for details.

### Coverage by System

Current extraction covers only **mcq (multiple choice) questions**. Complete extraction requires all 6 question types per system.

| System | Extracted | Target | Status |
|--------|-----------|--------|--------|
| Cardiovascular Medicine | 132 | 240 | 55% ◐ |
| Endocrinology & Metabolism | 101 | 180 | 56% ◐ |
| Hematology | 72 | 200 | 36% ✗ |
| Infectious Disease | 114 | 240 | 48% ◐ |
| Nephrology | 107 | 200 | 54% ◐ |
| Neurology | 78 | 180 | 43% ◐ |
| Oncology | 72 | 160 | 45% ◐ |
| Rheumatology | 78 | 200 | 39% ◐ |
| **Missing Systems** | | | |
| Clinical Practice | 0 | 220 | 0% ✗ |
| Gastroenterology | 0 | 220 | 0% ✗ |
| Interdisciplinary Medicine | 0 | 220 | 0% ✗ |
| Pulmonary & Critical Care | 0 | 220 | 0% ✗ |
| Additional Systems (cs, dm, fc, hp) | 0 | 213 | 0% ✗ |

**Total Progress**: 754 / 2,233 (34%)

See [Question ID Discovery](../Question%20ID%20Discovery.md) for complete target breakdown.

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
├── cv/                              # Cardiovascular
│   ├── cvmcq24001/
│   │   ├── cvmcq24001.json         # Complete question
│   │   └── cvmcq24001_metadata.txt # Human-readable summary
│   └── ... (131 more questions)
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
- Correct answer
- Detailed critique/explanation
- Key learning points
- Academic references (with PMIDs)
- Educational objectives
- Metadata (care type, last updated, etc.)

## When to Use This Tool

**Use the Rust Extractor when:**
- You need bulk extraction of multiple questions
- You want fast, efficient API-based access
- You prefer direct validation and data quality checks
- You're automating large extraction runs
- You need to resume interrupted sessions

The Rust extractor is the only supported extraction path for this project.

## Known Issues

No known abbreviation mismatches in current extraction output. Interdisciplinary Medicine uses `in` for question IDs while the web path remains `/dmin/`.

## Next Steps (Phase 1 Plan)

See [PHASE_1_PLAN.md](../project/PHASE_1_PLAN.md) for complete implementation plan:

1. **Implement Question ID Discovery** - Extend to all 6 question types (cor, mcq, qqq, mqq, vdx, sq)
2. **Update Configuration** - Add all 16 systems with accurate target counts
3. **Complete All 16 Systems** - Extract remaining systems and fill partial extractions
4. **Validate & Breadcrumb** - Add syllabus reference fields to each question
5. **Reach 100%** - Extract all 2,233 questions

## Related Documentation

- [Setup Guide](setup.md) - Installation and configuration
- [Usage Guide](usage.md) - How to run the extractor
- [Validation](validation.md) - Data quality verification
- [Architecture](architecture.md) - Technical implementation details
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
