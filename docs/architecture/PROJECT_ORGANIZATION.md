# MKSAP Project Organization

**Last Updated:** December 25, 2025

## Overview

This project is a **4-phase pipeline** for generating MKSAP Anki flashcard decks:

1. **Phase 1**: Data Extraction (Rust) - Extract 2,233 questions from MKSAP API
2. **Phase 2**: Intelligent Fact Extraction (Claude Code) - Extract atomic facts via LLM
3. **Phase 3**: Card Generation (Rust) - Convert facts to Anki note format
4. **Phase 4**: Import & Validation - Generate .apkg deck and import

See [PHASE_1_PLAN.md](../project/PHASE_1_PLAN.md) for current phase details.

## Directory Structure

```
MKSAP/
│
├── Cargo.toml                # Rust workspace manifest
├── Cargo.lock                # Dependency lock file
│
├── text_extractor/           # Phase 1: Text extraction (Rust binary)
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs            # Entry point and orchestration
│       ├── extractor.rs       # Core extraction logic (3-phase pipeline)
│       ├── config.rs          # System definitions (12 organ systems)
│       ├── validator.rs       # Data quality validation
│       ├── models.rs          # Data structures (QuestionData, etc.)
│       ├── media.rs           # Media asset downloading
│       ├── browser.rs         # Browser-based auth fallback
│       └── utils.rs           # HTML parsing utilities
│
├── media_extractor/          # Phase 1: Media post-processing (Rust binary)
│   ├── Cargo.toml
│   └── src/
│       └── main.rs           # Standalone media downloader
│
├── mksap_data/               # Phase 1 Output: Extracted question data
│   ├── .checkpoints/         # Extraction progress checkpoints
│   ├── cv/, en/, hm/, ...    # Questions organized by organ system
│   │   └── {question_id}/
│   │       ├── {question_id}.json        # Complete question data
│   │       ├── {question_id}_metadata.txt # Human-readable summary
│   │       └── figures/                  # Downloaded media files
│   └── validation_report.txt # Quality assurance report
│
├── mksap_data_failed/        # Failed extraction records (for retry)
│
├── docs/                     # Documentation
│   ├── project/
│   │   ├── README.md         # Project overview
│   │   ├── PHASE_1_PLAN.md   # ⭐ Current phase roadmap (2,233 questions)
│   │   ├── QUICKSTART.md     # Quick start guide
│   │   └── INDEX.md          # Documentation index
│   ├── rust/
│   │   ├── overview.md       # Extractor status and next steps
│   │   ├── setup.md          # Installation and configuration
│   │   ├── usage.md          # How to run extraction
│   │   ├── validation.md     # Data quality checks
│   │   ├── architecture.md   # Technical implementation details
│   │   ├── troubleshooting.md
│   │   └── DESERIALIZATION_ISSUES.md
│   ├── specifications/
│   │   ├── MCQ_FORMAT.md     # Anki output format specification
│   │   └── examples/
│   │       └── CVMCQ24041.md # Example MCQ card
│   ├── architecture/
│   │   └── PROJECT_ORGANIZATION.md # This file
│   ├── Question ID Discovery.md      # Why 2,233 questions (not 1,810)
│   ├── syllubus_extraction.md        # Phase 2+ specification (future)
│   ├── video_svg_extraction.md       # Technical reference (future)
│   └── potential_syllubus_errors.md  # Risk analysis (future)
│
├── README.md                 # Project entry point
├── CLAUDE.md                 # Claude Code integration guide
├── AGENTS.md                 # Development guidelines and standards
├── .gitignore                # Git ignore patterns
└── .claude/                  # Claude Code project configuration
    └── (project-specific tools and skills)
```

## Primary Workflow

### Phase 1: Data Extraction (Current)

1. Review [PHASE_1_PLAN.md](../project/PHASE_1_PLAN.md) for complete roadmap
2. Authenticate to MKSAP (session cookie or browser fallback)
3. Run text extractor: `./target/release/mksap-extractor`
4. Run media extractor: `./target/release/media-extractor`
5. Validate extraction: `./target/release/mksap-extractor validate`
6. Add syllabus breadcrumb references to each question JSON

**Target:** 2,233 questions across 16 systems and 6 question types

### Phase 2: Intelligent Fact Extraction (Future)

1. Create Claude Code skill for batch LLM processing
2. For each question's `critique` field: Extract atomic facts
3. Append `true_statements` array to each question JSON

### Phase 3: Card Generation (Future)

1. Build modular Rust pipeline (separate modules per concern)
2. Convert `true_statements` to cloze cards
3. Associate media and HTML tables
4. Output to `anki_notes.jsonl`

### Phase 4: Import & Validation (Future)

1. Convert `anki_notes.jsonl` to `mksap.apkg` format
2. Test import into Anki
3. Validate card quality

## Project Architecture

### Rust Workspace

The project uses Cargo workspaces to organize multiple binaries:

```toml
[workspace]
members = ["text_extractor", "media_extractor"]
```

**text_extractor**: Primary extraction tool
- API-based question downloading
- Session authentication
- Checkpoint-based resumable extraction
- Built-in validation

**media_extractor**: Post-processing tool
- Downloads referenced media (images, videos, SVGs)
- Updates question JSON with media refs

Both binaries target the same `mksap_data/` output directory.

## Data Flow

```
MKSAP API
    ↓
text_extractor → mksap_data/{system}/{question_id}.json
    ↓
media_extractor → mksap_data/{system}/{question_id}/figures/
    ↓
validator → validation_report.txt
    ↓
[Phase 2] LLM processing → true_statements array (append to JSON)
    ↓
[Phase 3] Card generation → anki_notes.jsonl
    ↓
[Phase 4] Deck generation → mksap.apkg (Anki deck file)
```

## Key Design Decisions

1. **Question ID as persistent key**: Every artifact (original JSON, facts, cards) traces back to question_id
2. **Modular phases**: Each phase produces a stable output that can be handed off to the next
3. **Resumable extraction**: Checkpoints allow recovery from interruptions without data loss
4. **Validation at each stage**: Data quality verified before proceeding to next phase
5. **Syllabus as references only** (Phase 1): Breadcrumbs added but full syllabus extraction deferred to Phase 2+

## Notes

- The Rust extractor is the **only supported extraction method**
- Future processing steps (fact extraction, card generation) are **downstream of `mksap_data/`**
- See [PHASE_1_PLAN.md](../project/PHASE_1_PLAN.md) for current phase implementation details
- All documentation should be kept synchronized with actual directory structure
