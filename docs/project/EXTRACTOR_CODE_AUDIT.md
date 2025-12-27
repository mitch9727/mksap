# Extractor Code Audit (Cleanup Phase)

## Scope

- Inventory current execution paths for text_extractor and media_extractor.
- Identify unused or legacy code to prune before unifying extractors.
- Call out duplication that can be collapsed without changing extraction behavior.

## Active Execution Paths

### text_extractor

- Entry point: `text_extractor/src/main.rs`.
- Commands: Run, Validate, DiscoveryStats, RetryMissing, ListMissing, Standardize,
  CleanupRetired, CleanupFlat.
- Core pipeline: `text_extractor/src/extractor.rs` with impls in:
  - `text_extractor/src/workflow.rs`
  - `text_extractor/src/discovery.rs`
  - `text_extractor/src/io.rs`
  - `text_extractor/src/retry.rs`
  - `text_extractor/src/cleanup.rs`
- Auth flow: `text_extractor/src/auth_flow.rs` -> `text_extractor/src/auth.rs` ->
  `text_extractor/src/browser.rs` (interactive fallback).
- Data model + parsing: `text_extractor/src/models.rs` (includes critique link extraction).

### media_extractor

- Entry point: `media_extractor/src/main.rs`.
- Commands: Discover (API media discovery), Download (figures/tables), Browser
  (videos/svgs), BackfillInlineTables.
- Core discovery: `media_extractor/src/discovery/mod.rs` +
  `media_extractor/src/discovery/statistics.rs` +
  `media_extractor/src/discovery/types.rs` +
  `media_extractor/src/discovery/helpers.rs` (only `extract_content_ids` used).
- API download: `media_extractor/src/api.rs` + `media_extractor/src/download.rs`.
- Browser download: `media_extractor/src/browser.rs`,
  `media_extractor/src/browser_download.rs`,
  `media_extractor/src/browser_media/*.rs`.
- JSON/media updates: `media_extractor/src/file_store.rs` +
  `media_extractor/src/render.rs`.
- Session handling: `media_extractor/src/session.rs`.

## Unused Or Legacy Code Candidates

- `media_extractor/src/discovery/scanner.rs` (entire `MediaDiscovery` engine is
  not referenced by current entry points).
- `media_extractor/src/discovery/helpers.rs` unused functions:
  `build_figures_index`, `extract_figure_reference`, `build_videos_index`,
  `CategorizedMedia`, `categorize_content_ids`, `extract_subspecialty`,
  `extract_product_type`, `extract_related_section`, `is_invalidated`.
  Only `extract_content_ids` is referenced.
- `media_extractor/src/discovery/types.rs`: `MediaType` and
  `MediaType::from_content_id` are unused; `QuestionMedia::has_media` unused.
- `media_extractor/src/discovery/mod.rs` re-exports unused `MediaDiscovery` and
  `MediaType`. `scan_local_questions` is legacy and currently unused.
- `media_extractor/src/file_store.rs`: `format_existing_tables` and
  `collect_table_files` are unused.
- `text_extractor/src/models.rs`: `RelatedContent.syllabus` remains in the output
  schema even though syllabus extraction is out of scope. Decide whether to
  rename or remove this field to eliminate syllabus terminology.

## Duplication And Consolidation Candidates

- Content ID extraction and type checks duplicated between
  `media_extractor/src/discovery/helpers.rs` and `media_extractor/src/download.rs`,
  plus inline table detection logic duplicated between
  `media_extractor/src/discovery/mod.rs` and `media_extractor/src/download.rs`.
- Content metadata fetchers duplicated:
  `load_figure_metadata` exists in both `media_extractor/src/discovery/mod.rs`
  and `media_extractor/src/download.rs`; similar patterns in
  `media_extractor/src/browser_download.rs` for videos/svgs.
- Media update merging in `media_extractor/src/file_store.rs` overlaps with the
  refresh-merge behavior in `text_extractor/src/workflow.rs`.

## Unification Notes (Next Steps)

- Shared HTTP client/session cookie config can be consolidated across extractors.
- Target pipeline order: discover valid IDs -> fetch JSON -> parse text and
  critique links -> write question JSON -> derive media references -> download
  tables/images/videos/svgs -> update JSON with media metadata.
- Keep modules under 500 lines; merge only when it reduces duplication and
  preserves clarity.
