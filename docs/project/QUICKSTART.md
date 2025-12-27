# MKSAP Quickstart

## 1) Build

```bash
cd /Users/Mitchell/coding/projects/MKSAP/text_extractor
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
cd ../media_extractor
cargo build --release
./target/release/media-extractor --all --data-dir ../mksap_data
```

Media extractor arguments:

```bash
./target/release/media-extractor --all --data-dir /path/to/mksap_data
./target/release/media-extractor cvmcq24001 --data-dir /path/to/mksap_data
```

Optional session override:

```bash
MKSAP_SESSION=... ./target/release/media-extractor
```

## Output Location

- Extracted questions: `mksap_data/{system}/{question_id}/`
- Checkpoints: `mksap_data/.checkpoints/`
- Failures: `mksap_data_failed/`
