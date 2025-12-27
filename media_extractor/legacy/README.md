Legacy media-extractor sources (archived to keep the active build focused on discovery).

Use these files as reference before re-implementing functionality.

- legacy/src/main.rs: Old CLI entrypoint that wired discovery + extraction + formatting.
- legacy/src/api.rs: HTTP helpers to fetch question JSON and download figures/tables.
- legacy/src/browser.rs: WebDriver login flow and HTML scraping for videos/SVGs.
- legacy/src/file_store.rs: Data directory scanning, JSON update, table formatting.
- legacy/src/model.rs: CLI argument models and media update structs.
- legacy/src/render.rs: Render table JSON nodes into HTML + pretty formatting.
- legacy/src/session.rs: Session cookie load/save helpers.
- legacy/src/update.rs: Orchestrates media extraction and JSON updates.
- legacy/src/media/mod.rs: Shared filename/relative path helpers.
- legacy/src/media/svgs.rs: SVG download and inline SVG persistence.
- legacy/src/media/videos.rs: Video download helper.
