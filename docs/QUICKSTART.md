# QUICKSTART - Essential Commands

> For detailed explanations, see [Phase 1 Deep Dive](reference/PHASE_1_DEEP_DIVE.md),
> [Phase 2 Status](PHASE_2_STATUS.md), and
> [Troubleshooting](reference/TROUBLESHOOTING.md).

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

## Progress Tracking

- **Todos**: See [TODO.md](../TODO.md)
- **Phase 1 Report**: See [Phase 1 Completion](PHASE_1_COMPLETION_REPORT.md)
- **Phase 2 Details**: See [Phase 2 Status](PHASE_2_STATUS.md)

## Need Help?

- **Architecture**: See [Phase 1 Deep Dive](reference/PHASE_1_DEEP_DIVE.md)
- **Stuck on error?**: See [Troubleshooting](reference/TROUBLESHOOTING.md)
- **Phase 2 details?**: See [Statement Generator Reference](reference/STATEMENT_GENERATOR.md)
- **Flashcard design?**: See [Cloze Best Practices](reference/CLOZE_FLASHCARD_BEST_PRACTICES.md)


---

**Last Updated**: January 6, 2026
