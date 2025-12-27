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
  - Browser-extracted videos saved under `videos/`.
- Critique hyperlink extraction from the critique/exposition region into
  `critique_links`.

## Out of Scope

- Syllabus content extraction.
- Any conversion of MKSAP data into MCQ-specific formats.

## Coverage and Counts

- The authoritative extraction target is 2,198 valid question IDs.
- The previously cited count includes 35 invalidated questions that should be excluded.

## Completion Criteria

1. Text extraction produces valid JSON for all 2,198 IDs.
2. Validation reports 100% coverage for discovered valid IDs.
3. Media extraction fills `media` and `media_metadata` with files on disk for
   all referenced tables, figures, SVGs, and videos.
4. `critique_links` includes all hyperlinks present in critique content.

## Operational Notes

- Invalidated questions are skipped and should not be counted as missing.
- Media extraction includes both API-driven figures/tables and browser-driven
  SVGs/videos.
