# MKSAP Quickstart

## 1) Build

```bash
cd /Users/Mitchell/coding/projects/MKSAP/extractor
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

## Output Location

- Extracted questions: `mksap_data/{system}/{question_id}/`
- Checkpoints: `mksap_data/.checkpoints/`
- Failures: `mksap_data_failed/`
