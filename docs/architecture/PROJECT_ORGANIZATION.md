# MKSAP Project Organization

**Last Updated:** December 25, 2025

## Overview

This project is a **4-phase pipeline** for generating MKSAP Anki flashcard decks:

1. **Phase 1**: Data Extraction (Rust) - Extract 2,198 valid questions from the MKSAP API (invalidated questions excluded)
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
│       ├── main.rs            # Entry point and CLI dispatch
│       ├── commands.rs        # Command parsing
│       ├── config.rs          # System definitions (16 system codes)
│       ├── categories.rs      # Category build helpers
│       ├── extractor.rs       # Core extractor type
│       ├── workflow.rs        # Discovery + extraction pipeline
│       ├── discovery.rs       # ID discovery + checkpoints
│       ├── io.rs              # File IO + checkpoints
│       ├── retry.rs           # Retry helpers
│       ├── cleanup.rs         # Cleanup helpers
│       ├── reporting.rs       # Validation/discovery reports
│       ├── validator.rs       # Data quality validation
│       ├── auth.rs            # API login helpers
│       ├── auth_flow.rs       # Authentication flow
│       ├── browser.rs         # Browser-based auth fallback
│       ├── diagnostics.rs     # API inspection helper
│       └── models.rs          # Data structures (QuestionData, etc.)
│
├── media_extractor/          # Phase 1: Media post-processing (Rust binary)
│   ├── Cargo.toml
│   └── src/
│       └── main.rs           # Standalone media downloader
│
├── mksap_data/               # Phase 1 Output: Extracted question data
│   ├── .checkpoints/         # Extraction progress checkpoints
│   ├── cv/, en/, hm/, ...    # Questions organized by system code
│   │   └── {question_id}/
│   │       ├── {question_id}.json        # Complete question data
│   │       ├── figures/                  # Media extractor output
│   │       ├── tables/                   # Media extractor output
│   │       ├── videos/                   # Media extractor output
│   │       └── svgs/                     # Media extractor output
│   └── validation_report.txt # Quality assurance report
│
├── mksap_data_failed/        # Failed extraction records (for retry)
│   ├── deserialize/          # Failed JSON payloads
│   ├── invalid/              # Quarantined invalid questions
│   └── retired/              # Retired questions moved by cleanup
│
├── docs/                     # Documentation
│   ├── architecture/
│   │   └── PROJECT_ORGANIZATION.md # This file
│   ├── project/
│   │   ├── README.md         # Project overview
│   │   ├── QUICKSTART.md     # Quick start guide
│   │   └── INDEX.md          # Documentation index
│   ├── reference/
│   │   ├── RUST_SETUP.md
│   │   ├── RUST_USAGE.md
│   │   ├── RUST_ARCHITECTURE.md
│   │   ├── VALIDATION.md
│   │   ├── TROUBLESHOOTING.md
│   │   └── QUESTION_ID_DISCOVERY.md
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

1. Authenticate to MKSAP (prefer `MKSAP_SESSION`)
2. Run text extractor from `text_extractor/`: `./target/release/mksap-extractor`
3. Validate extraction: `./target/release/mksap-extractor validate`
4. Run media extractor (optional): `./target/release/media-extractor --all --data-dir ../mksap_data`
5. Review `.checkpoints/discovery_metadata.json` and `validation_report.txt`

**Target:** 2,198 valid questions across 16 systems and 6 question types (invalidated questions excluded)

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
media_extractor → mksap_data/{system}/{question_id}/(figures|tables|videos|svgs)
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

## Notes

- The Rust extractor is the **only supported extraction method**
- Future processing steps (fact extraction, card generation) are **downstream of `mksap_data/`**
- See [PHASE_1_PLAN.md](../project/PHASE_1_PLAN.md) for current phase implementation details
- All documentation should be kept synchronized with actual directory structure
