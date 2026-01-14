# MKSAP Extractor Technical Spec

This document describes the technical behavior and interfaces for the Rust-based
MKSAP extractor. The standards refer to this folder as "scraper," but the
current implementation is the `extractor/` crate.

## Architecture

- **Discovery**: Uses HTTP HEAD requests to determine which question IDs exist.
- **Extraction**: Fetches question JSON, normalizes responses, and writes per
  system code under `mksap_data/`.
- **Validation**: Compares extracted counts against discovery metadata stored in
  `mksap_data/.checkpoints/discovery_metadata.json`.
- **Media pipeline**: Optional discovery and download of associated media
  (images, SVG/video) via integrated commands.

Related documentation:
- [RUST_ARCHITECTURE.md](../reference/RUST_ARCHITECTURE.md)
- [EXTRACTION_OVERVIEW.md](../reference/EXTRACTION_OVERVIEW.md)

## API Reference

CLI entry points are provided by the `mksap-extractor` binary:

```bash
cd extractor
cargo build --release
./target/release/mksap-extractor
./target/release/mksap-extractor validate
```

Optional media commands:

```bash
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download
```

For detailed usage and flags, see [RUST_USAGE.md](../reference/RUST_USAGE.md).

## Configuration

Supported environment overrides:

- `MKSAP_SESSION` - Override the session cookie used for API calls.
- `MKSAP_CONCURRENCY` - Tune request concurrency when extracting.
- `MKSAP_YEAR_START` and `MKSAP_YEAR_END` - Adjust the target year range.

Operational notes:
- Output lives under `mksap_data/` and failed artifacts go to
  `mksap_data_failed/`.
- Validation uses discovery metadata; run discovery before `validate` when
  starting from a clean workspace.
