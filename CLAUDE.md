# CLAUDE.md - MKSAP Medical Education Pipeline

> **Last Updated**: January 6, 2026

This file provides guidance to Claude Code when working on the MKSAP medical education extraction pipeline.

## Project Overview

**MKSAP Medical Education Pipeline** - Multi-phase system for extracting, processing, and generating medical education flashcards from ACP MKSAP (Medical Knowledge Self-Assessment Program) question bank.

**Project Location**: `/Users/Mitchell/coding/projects/MKSAP/`

### Current Status

- **Phase 1 (Complete ✅)**: Rust extractor - 2,198 questions extracted to JSON
- **Phase 2 (Active 🔄)**: Python statement generator - LLM-based flashcard extraction
- **Phase 3 (Planned 📋)**: Cloze application - Apply fill-in-the-blank formatting
- **Phase 4 (Planned 📋)**: Anki export - Generate spaced repetition decks

### Quick Links

- **Working on Phase 1?** → See [QUICKSTART.md](docs/QUICKSTART.md) for commands
- **Working on Phase 2?** → See [Statement Generator Reference](docs/reference/STATEMENT_GENERATOR.md)
- **Stuck on a problem?** → See [Troubleshooting Guide](docs/reference/TROUBLESHOOTING.md)
- **Understanding architecture?** → See [Phase 1 Deep Dive](docs/reference/PHASE_1_DEEP_DIVE.md)
- **Planning Phase 2 work?** → See [Phase 2 Status](docs/PHASE_2_STATUS.md)

## Important: System Codes vs Browser Organization

This codebase works with **16 two-letter system codes** (cv, en, fc, cs, gi, hp, hm, id, in, dm, np, nr, on, pm, cc, rm) that appear in question IDs and API endpoints. These are NOT the same as the 12 content area groupings visible in the MKSAP browser interface.

**Browser shows 12 content areas**, but some contain multiple system codes. All extraction, validation, and reporting in this codebase is organized by these 16 system codes, not the 12 browser groupings.

## Todo & Progress Tracking

### Single Source of Truth

**All project todos are tracked in [TODO.md](TODO.md)** for active and planned work. Completed work is recorded in
`docs/CHANGELOG.md` and removed from TODO.md.

**When starting work:**
1. Open [TODO.md](TODO.md) and find the task you're starting
2. Check dependencies - is anything blocking this task?
3. Review file links in the task description for context

**When done:**
1. Remove the completed task from TODO.md
2. Add a change note in `docs/CHANGELOG.md` (plain text, no checkboxes)
3. Update "Last Updated" at top of TODO.md
4. Commit with message: `git commit -m "mark: [task name] complete"`

## Essential Commands

### Phase 1: Rust Extractor

```bash
cd /path/to/MKSAP/extractor

# Build
cargo build --release

# Run extraction (all systems)
./target/release/mksap-extractor

# Validate output
./target/release/mksap-extractor validate

# Get stats
./target/release/mksap-extractor discovery-stats

# Media: discover → download → extract (SVG/video)
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download --all
./target/release/mksap-extractor svg-browser --all
```

### Phase 2: Statement Generator

```bash
cd /path/to/MKSAP

# Test on 1 question
./scripts/python -m src.main process --question-id cvmcq24001

# Test on system
./scripts/python -m src.main process --mode test --system cv

# Production (all 2,198)
./scripts/python -m src.main process --mode production

# Stats & management
./scripts/python -m src.main stats
./scripts/python -m src.main reset
./scripts/python -m src.main clean-logs
```

## Project Structure

```
MKSAP/
├── CLAUDE.md                          ← This file
├── TODO.md                            ← Task tracking
├── extractor/                         ← Phase 1: Rust
│   ├── Cargo.toml
│   ├── src/
│   └── target/release/mksap-extractor
├── statement_generator/               ← Phase 2: Python
│   ├── requirements.txt
│   ├── src/
│   └── scripts/python
├── mksap_data/                        ← Extracted questions (2,198 JSON files)
└── docs/
    ├── INDEX.md                       ← Documentation entry point
    ├── PROJECT_OVERVIEW.md            ← Project goals and architecture
    ├── QUICKSTART.md                  ← Essential commands
    ├── PHASE_1_COMPLETION_REPORT.md
    ├── PHASE_2_STATUS.md              ← Phase 2 status and priorities
    ├── CHANGELOG.md                   ← Documentation change notes
    ├── DOCUMENTATION_MAINTENANCE_GUIDE.md
    ├── architecture/
    ├── reference/
    │   ├── PHASE_1_DEEP_DIVE.md        ← Phase 1 architecture details
    │   ├── TROUBLESHOOTING.md          ← Debugging guide
    │   ├── STATEMENT_GENERATOR.md      ← Phase 2 reference
    │   ├── CLOZE_FLASHCARD_BEST_PRACTICES.md
    │   └── VALIDATION.md
    ├── specifications/
    └── archive/
```

## Key Design Principles

1. **Discovery-Driven** - Adapts to current API state, not hardcoded baselines
2. **Resumability** - Extraction can be interrupted and resumed without data loss
3. **Non-Destructive** - Phase 2 only adds `true_statements` field, preserves all original data
4. **Modular Documentation** - Detailed docs linked from this file, not embedded
5. **Frequent Commits** - Small, atomic commits with clear messages

## When Starting Work

1. **Check status**: Open [TODO.md](TODO.md)
2. **Review context**: Check task description and linked docs
3. **Run QUICKSTART command**: See [docs/QUICKSTART.md](docs/QUICKSTART.md)
4. **If stuck**: See [Troubleshooting Guide](docs/reference/TROUBLESHOOTING.md)
5. **When done**: Remove completed task from TODO.md, add a change note, and commit

## Next Steps

- **Phase 1 Complete?** → Read [Phase 1 Completion Report](docs/PHASE_1_COMPLETION_REPORT.md)
- **Working on Phase 2?** → Read [Phase 2 Status](docs/PHASE_2_STATUS.md)
- **Need architecture details?** → Read [Phase 1 Deep Dive](docs/reference/PHASE_1_DEEP_DIVE.md)
- **Understanding validation?** → Read [Validation Guide](docs/reference/VALIDATION.md)


---

**Repository**: git@github.com:mitch9727/mksap.git
**Phase 1 Status**: ✅ Complete (2,198 questions)
**Phase 2 Status**: 🔄 Active
