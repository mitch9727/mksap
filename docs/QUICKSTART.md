# QUICKSTART - Essential Commands

> For detailed explanations, see [Extractor System Manual](../extractor/docs/EXTRACTOR_MANUAL.md),
> [Phase 2 Status](../statement_generator/docs/PHASE_2_STATUS.md), and
> [Troubleshooting](../extractor/docs/TROUBLESHOOTING.md).

## Phase 1: Rust Extractor

```bash
# Build
cd /Users/Mitchell/coding/projects/MKSAP/extractor
cargo build --release

# Run extraction (all systems)
./target/release/mksap-extractor

# Validate
./target/release/mksap-extractor validate

# Get stats
./target/release/mksap-extractor discovery-stats

# Media: discover → download → extract (SVG/video)
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download --all
./target/release/mksap-extractor svg-browser --all
```

## Phase 2: Statement Generator

Set `MKSAP_PYTHON_VERSION` in `.env` to the interpreter you expect (example: `3.11.9`).

```bash
cd /Users/Mitchell/coding/projects/MKSAP

# Test on 1 question
./scripts/python -m src.interface.cli process --question-id cvmcq24001

# Test on system
./scripts/python -m src.interface.cli process --mode test --system cv

# Production (all 2,198)
./scripts/python -m src.interface.cli process --mode production

# Stats & management
./scripts/python -m src.interface.cli stats
./scripts/python -m src.interface.cli reset
./scripts/python -m src.interface.cli clean-logs
```

## Progress Tracking

- **Todos**: See [TODO.md](../TODO.md)
- **Phase 1 Report**: See [Phase 1 Completion](../extractor/docs/PHASE_1_COMPLETION_REPORT.md)
- **Phase 2 Details**: See [Phase 2 Status](../statement_generator/docs/PHASE_2_STATUS.md)

## Need Help?

- **Architecture**: See [Extractor System Manual](../extractor/docs/EXTRACTOR_MANUAL.md)
- **Stuck on error?**: See [Troubleshooting](../extractor/docs/TROUBLESHOOTING.md)
- **Phase 2 details?**: See [Statement Generator Reference](../statement_generator/docs/STATEMENT_GENERATOR.md)
- **Flashcard design?**: See [Cloze Best Practices](../statement_generator/docs/CLOZE_FLASHCARD_BEST_PRACTICES.md)


---

**Last Updated**: January 20, 2026
