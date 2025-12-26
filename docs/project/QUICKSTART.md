# MKSAP Quickstart

## 1) Build

```bash
cd /Users/Mitchell/coding/projects/MKSAP
cargo build --release
```

## 2) Run the extractor

```bash
./target/release/mksap-extractor
```

## 3) Validate output

```bash
./target/release/mksap-extractor validate
```

## 4) Run media extraction

```bash
cargo build --release -p media-extractor
./target/release/media-extractor
```

Media extractor arguments:

```bash
./target/release/media-extractor /path/to/mksap_data
./target/release/media-extractor /path/to/mksap_data https://mksap.acponline.org
```

Optional session override:

```bash
MKSAP_SESSION=... ./target/release/media-extractor
```

## Output Location

- Extracted questions: `mksap_data/{system}/{question_id}/`
