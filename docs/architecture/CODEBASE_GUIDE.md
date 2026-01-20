# Codebase Guide

This guide explains how the repository is structured and how to trace the main
execution paths in the Rust extractor.

## Architecture

The project centers on a Rust CLI that discovers and extracts MKSAP questions
into structured JSON. Supporting tooling lives alongside it:

- `extractor/` - Rust crate that builds the `mksap-extractor` binary
- `statement_generator/` - Phase 2 statement generation tooling
- `mksap_data/` - Extracted JSON output organized by system
- `mksap_data_failed/` - Quarantined extraction artifacts
- `docs/` - Project-level documentation (component docs live under extractor/docs and statement_generator/docs)

For a system-level overview, see
[PROJECT_ORGANIZATION.md](PROJECT_ORGANIZATION.md).

## Code Structure

Key Rust entry points:

- `extractor/src/main.rs` - CLI entry point
- `extractor/src/cli.rs` - Argument parsing and command wiring
- `extractor/src/commands.rs` - Command implementations
- `extractor/src/workflow.rs` - High-level extraction orchestration
- `extractor/src/discovery.rs` - ID discovery logic
- `extractor/src/extractor.rs` - Fetch/transform pipeline
- `extractor/src/validator.rs` - Validation against discovery metadata
- `extractor/src/asset_*.rs` - Media discovery, metadata, and downloads
- `extractor/src/config.rs` - Configuration defaults and env overrides

## How to Understand Code

1. Start at `extractor/src/main.rs` to see the CLI bootstrap sequence.
2. Follow `extractor/src/cli.rs` into `extractor/src/commands.rs` to locate the
   command handlers (`extract`, `validate`, `media-discover`, `media-download`).
3. Trace `extractor/src/workflow.rs` and `extractor/src/extractor.rs` to see how
   discovery feeds extraction and how output is written to `mksap_data/`.
4. Review `extractor/src/validator.rs` to understand how discovery metadata is
   used to gate completeness.
5. For media handling, inspect `extractor/src/asset_discovery.rs` and
   `extractor/src/asset_download.rs`.

If you need usage details, see
[TECHNICAL_SPEC.md](../../extractor/docs/TECHNICAL_SPEC.md).
