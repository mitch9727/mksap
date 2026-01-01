# MKSAP Quickstart

## 1) Build

```bash
cd /path/to/MKSAP/extractor
cargo build --release
```

## 2) Run the extractor

```bash
./target/release/mksap-extractor
```

Optional session override:

```bash
MKSAP_SESSION=... ./target/release/mksap-extractor
```

## 3) Validate output

```bash
./target/release/mksap-extractor validate
```

## 4) Run media extraction

```bash
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download --all
```

Media commands:

```bash
./target/release/mksap-extractor media-discover
./target/release/mksap-extractor media-download --all
./target/release/mksap-extractor media-download --question-id cvmcq24001
```

Optional session override:

```bash
MKSAP_SESSION=... ./target/release/mksap-extractor media-download --all
```

## 5) Statement generator (Phase 2)

```bash
cd statement_generator
pip install -r requirements.txt

# Test on 1-2 questions
python -m src.main process --mode test --system cv
```

See `docs/reference/STATEMENT_GENERATOR.md` for provider setup and full CLI options.

## Output Location

- Extracted questions: `mksap_data/{system}/{question_id}/`
- Checkpoints: `mksap_data/.checkpoints/`
- Failures: `mksap_data_failed/`
