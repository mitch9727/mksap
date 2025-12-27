# Repository Guidelines

## Project Structure & Module Organization

- `extractor/`: Rust crate that builds the main `mksap-extractor` binary; core logic lives in `extractor/src/`.
- `docs/`: Project, architecture, and Rust usage documentation.
- `mksap_data/`: Extracted question output organized by system code (e.g., `mksap_data/cv/`).
- `mksap_data_failed/`: Quarantined or failed extraction artifacts.

## Build, Test, and Development Commands

```bash
# Build and run the main extractor
cd extractor
cargo build --release
./target/release/mksap-extractor
./target/release/mksap-extractor validate

# Media discovery/download (optional, integrated)
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download
# ./target/release/mksap-extractor svg-browser   # video/svg via browser
```

- Use `MKSAP_SESSION=...` to override the session cookie for API calls.
- `cargo test` runs in the extractor crate, but there are currently no unit tests.

## Coding Style & Naming Conventions

- Rust 2021 edition with standard formatting; run `cargo fmt` when changing Rust files.
- Indentation: 4 spaces; line length: follow rustfmt defaults.
- Naming: `snake_case` for functions/vars, `CamelCase` for types, `SCREAMING_SNAKE_CASE` for constants.

## Testing Guidelines

- No automated test suite yet; validation is done via the extractor:
  - `./target/release/mksap-extractor validate` (run from `extractor/`).
- Review `mksap_data/validation_report.txt` and `mksap_data_failed/` after changes.

## Commit & Pull Request Guidelines

- Commit messages follow Conventional Commits (examples from history: `feat: ...`, `chore: ...`).
- PRs should include: short summary, commands run, and whether data outputs changed.
- Avoid committing regenerated `mksap_data/` unless the change is intentional and documented.

## Configuration & Credentials

- Never commit session cookies or authentication artifacts.
- Prefer environment variables (`MKSAP_SESSION`, `MKSAP_CONCURRENCY`, etc.) for local overrides.
