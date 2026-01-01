# Extractor Code Audit (Cleanup Phase)

## Scope

- Inventory current execution paths for the unified extractor.
- Identify unused or legacy code to prune after consolidation.
- Call out duplication that can be collapsed without changing extraction behavior.

## Active Execution Paths

### extractor

- Entry point: extractor CLI binary.
- Commands: Run, Validate, DiscoveryStats, RetryMissing, ListMissing, Standardize,
  CleanupRetired, CleanupFlat, MediaDiscover, MediaDownload, SvgBrowser, ExtractAll.
- Core pipeline: extractor type with workflow, discovery, I/O, retry, and cleanup
  subsystems.
- Auth flow: auth subsystem with browser fallback and session helpers.
- Data model + parsing: question schema includes critique link extraction.
- Asset pipeline (integrated):
  - Asset discovery + statistics (API-driven)
  - Figure/table download pipeline
  - SVG browser automation (videos manual)
  - JSON/media update + table rendering
  - Session cookie helpers

## Unused Or Legacy Code Candidates

- Inline table metadata backfill helpers were removed during consolidation;
  reintroduce only if we need a dedicated backfill pass.
- `RelatedContent` list field remains in the output schema even though related
  content extraction is out of scope. Decide
  whether to rename or remove this field to reduce confusion.

## Duplication And Consolidation Candidates

- Content ID extraction and type checks duplicated between
  content ID parsing and the asset download pipeline, plus inline table
  detection duplicated between asset discovery and asset download.
- Content metadata fetchers duplicated between asset discovery and asset
  download; similar patterns exist in SVG handling.
- Media update merging overlaps with refresh-merge behavior in the extraction
  workflow.

## Unification Notes (Next Steps)

- Shared HTTP client/session cookie config is now consolidated in `extractor`.
- Target pipeline order remains: discover valid IDs -> fetch JSON -> parse text and
  critique links -> write question JSON -> derive media references -> download
  tables/images/svgs -> update JSON with media metadata (videos manual).
- Next cleanup pass should prune unused media file_store helpers and consider
  consolidating duplicated metadata fetchers.
