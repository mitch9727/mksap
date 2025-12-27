# Extractor Code Audit (Cleanup Phase)

## Scope

- Inventory current execution paths for the unified extractor.
- Identify unused or legacy code to prune after consolidation.
- Call out duplication that can be collapsed without changing extraction behavior.

## Active Execution Paths

### extractor

- Entry point: `extractor/src/main.rs`.
- Commands: Run, Validate, DiscoveryStats, RetryMissing, ListMissing, Standardize,
  CleanupRetired, CleanupFlat, MediaDiscover, MediaDownload, SvgBrowser, ExtractAll.
- Core pipeline: `extractor/src/extractor.rs` with impls in:
  - `extractor/src/workflow.rs`
  - `extractor/src/discovery.rs`
  - `extractor/src/io.rs`
  - `extractor/src/retry.rs`
  - `extractor/src/cleanup.rs`
- Auth flow: `extractor/src/auth_flow.rs` -> `extractor/src/auth.rs` ->
  `extractor/src/login_browser.rs` (interactive fallback).
- Data model + parsing: `extractor/src/models.rs` (includes critique link extraction).
- Asset pipeline (integrated):
  - `extractor/src/asset_discovery.rs` + `extractor/src/asset_stats.rs` (API discovery + statistics)
  - `extractor/src/asset_download.rs` + `extractor/src/asset_api.rs` (figure/table downloads)
  - `extractor/src/svg_browser.rs` + `extractor/src/svg_download.rs`
    (SVG browser automation; videos manual)
  - `extractor/src/asset_store.rs` + `extractor/src/table_render.rs` (JSON/media updates)
  - `extractor/src/session.rs` (session cookie helpers)

## Unused Or Legacy Code Candidates

- Inline table metadata backfill helpers were removed during consolidation;
  reintroduce only if we need a dedicated backfill pass.
- `extractor/src/models.rs`: `RelatedContent` list field remains in the
  output schema even though related content extraction is out of scope. Decide
  whether to rename or remove this field to reduce confusion.

## Duplication And Consolidation Candidates

- Content ID extraction and type checks duplicated between
  `extractor/src/content_ids.rs` and `extractor/src/asset_download.rs`,
  plus inline table detection logic duplicated between
  `extractor/src/asset_discovery.rs` and `extractor/src/asset_download.rs`.
- Content metadata fetchers duplicated:
  `load_figure_metadata` exists in both `extractor/src/asset_discovery.rs`
  and `extractor/src/asset_download.rs`; similar patterns in
  `extractor/src/svg_download.rs` for SVGs.
- Media update merging in `extractor/src/asset_store.rs` overlaps with the
  refresh-merge behavior in `extractor/src/workflow.rs`.

## Unification Notes (Next Steps)

- Shared HTTP client/session cookie config is now consolidated in `extractor`.
- Target pipeline order remains: discover valid IDs -> fetch JSON -> parse text and
  critique links -> write question JSON -> derive media references -> download
  tables/images/svgs -> update JSON with media metadata (videos manual).
- Next cleanup pass should prune unused media file_store helpers and consider
  consolidating duplicated metadata fetchers.
