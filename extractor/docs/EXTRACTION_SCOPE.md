# Extraction Scope and Success Criteria

## Purpose

Define the final, supported extraction scope for the project and the criteria for
considering the extraction phase complete.

## In Scope

- Text extraction for all valid question IDs (2,198 total).
- Media extraction for all referenced assets:
  - HTML tables saved under `tables/`.
  - Figures (PNG/JPG/SVG) saved under `figures/`.
  - Browser-extracted SVGs saved under `svgs/`.
  - Video files downloaded manually into `videos/` using the discovery report.
- Critique hyperlink extraction from the critique/exposition region into
  `critique_links`.

## Coverage and Counts

- The authoritative extraction target is 2,198 valid question IDs.
- The previously cited count includes 35 invalidated questions that should be excluded.

## Completion Criteria

1. Text extraction produces valid JSON for all 2,198 IDs.
2. Validation reports 100% coverage for discovered valid IDs.
3. Media extraction fills `media` and `media_metadata` with files on disk for
   all referenced tables, figures, and SVGs; videos are tracked for manual download.
4. `critique_links` includes all hyperlinks present in critique content.

## Operational Notes

- Invalidated questions are skipped and should not be counted as missing.
- Media extraction includes API-driven figures/tables and browser-driven SVGs.
- Video URLs are not downloaded automatically; use `media_discovery.txt` to guide manual download.
