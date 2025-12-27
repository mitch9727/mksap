# Rust MKSAP Extractor - Usage Guide

## Basic Usage

### Running the Extractor

```bash
cd /Users/Mitchell/coding/projects/MKSAP/text_extractor
cargo build --release
./target/release/mksap-extractor
```

Alternate (no build artifact path):

```bash
cargo run --release --
```

### First Run (Authentication Required)

On first run, the extractor will:
1. Check if the current client is already authenticated
2. Attempt API login when `MKSAP_USERNAME` and `MKSAP_PASSWORD` are set
3. Fall back to browser login if needed (10-minute timeout)
4. Begin extraction

For reliable API access, set `MKSAP_SESSION` in your environment (or `.env` file). Browser login does not automatically share Chrome cookies with the Rust HTTP client.

**Expected behavior**:
```
🚀 MKSAP Extractor Starting...
[INFO] Step 0: Checking if already authenticated...
[INFO] Step 1: Attempting automatic login with provided credentials...
[INFO] Attempting browser-based login as fallback...
[Browser window opens]
⏰ Waiting for login... (10 minutes remaining)
✓ Login successful!
📋 Starting extraction...
```

### Subsequent Runs

If you keep `MKSAP_SESSION` (or `MKSAP_USERNAME`/`MKSAP_PASSWORD`) in a `.env` file, reruns can be non-interactive:

```bash
./target/release/mksap-extractor
# Uses environment credentials if present
```

## Output Structure

### Directory Organization

Extracted questions are organized by system code:

```
mksap_data/
├── .checkpoints/
│   ├── discovery_metadata.json
│   └── {system}_ids.txt
├── cv/    # Cardiovascular Medicine
│   ├── cvmcq24001/
│   │   ├── cvmcq24001.json
│   └── cvmcq24002/ ...
├── en/    # Endocrinology
├── hm/    # Hematology
├── id/    # Infectious Disease
├── np/    # Nephrology
├── nr/    # Neurology
├── on/    # Oncology
└── rm/    # Rheumatology
```

By default, the extractor writes to `../mksap_data` relative to `text_extractor/`, so checkpoints live in `../mksap_data/.checkpoints/`.

### Question Files

#### JSON Format
`{question_id}.json` contains complete question data:

```json
{
  "question_id": "cvmcq24001",
  "category": "cv",
  "educational_objective": "Treat cardiogenic shock",
  "metadata": {
    "care_types": [],
    "patient_types": [],
    "high_value_care": false,
    "question_updated": "12/22/2025"
  },
  "question_text": "A 67-year-old woman is hospitalized...",
  "question_stem": "Which is the most appropriate management?",
  "options": [
    {"letter": "A", "text": "Biventricular pacemaker-defibrillator", "peer_percentage": 0},
    {"letter": "B", "text": "Coronary angiography", "peer_percentage": 0},
    {"letter": "C", "text": "Percutaneous mechanical support", "peer_percentage": 0},
    {"letter": "D", "text": "Pulmonary artery pressure sensor", "peer_percentage": 0}
  ],
  "user_performance": {
    "user_answer": null,
    "correct_answer": "C",
    "result": null,
    "time_taken": null
  },
  "critique": "The most appropriate management for this patient...",
  "key_points": [
    "Treatment of cardiogenic shock focuses on...",
    "Mechanical support options include..."
  ],
  "references": "Sinha SS, et al. [PMID: 40100174]",
  "related_content": {
    "syllabus": ["cv-section-id"],
    "learning_plan_topic": ""
  },
  "media": {
    "tables": [],
    "images": [],
    "svgs": [],
    "videos": []
  },
  "extracted_at": "2025-12-22T12:34:56Z"
}
```

All metadata lives in the JSON file; there is no separate `_metadata.txt` file.

#### Media Files (Post-Processing)
The text extractor initializes empty `media` arrays. The `media_extractor` can later populate files and update JSON:

```
mksap_data/cv/cvmcq24001/
├── cvmcq24001.json
├── figures/   # images
├── tables/    # HTML tables
├── svgs/
└── videos/
```

## Resuming Interrupted Extractions

The extractor can resume from where it left off:

### Automatic Resume

If extraction is interrupted (network error, timeout, etc.):

```bash
./target/release/mksap-extractor
# Automatically detects existing data
# Skips already-extracted questions
# Resumes from next unprocessed system
```

The extractor checks `mksap_data/` and skips existing questions, making it safe to run multiple times.
Checkpoint files under `mksap_data/.checkpoints/` record discovered IDs and discovery metadata.

### Force Full Re-extraction

To re-extract all questions:

```bash
rm -rf ../mksap_data/
./target/release/mksap-extractor
# Starts completely fresh
```

## Extraction Progress

### Progress Indicators

During extraction, you'll see:

```
[1/16] Processing: Cardiovascular Medicine
✓ Found 240 valid questions
Progress: 10/240 questions processed
...
✓ cv: Extracted 2 new, 238 already extracted
```

### Rate Limiting

The extractor automatically:
- Retries discovery requests with short backoff for transient errors
- Backs off for 429 responses during extraction
- Times out discovery HEAD checks after 10s and extraction GETs after 30s
- Logs all retries and failures

## Command-Line Options

### Available Commands

```bash
./target/release/mksap-extractor
# Runs full extraction (skips already-extracted question folders)
```

```bash
./target/release/mksap-extractor validate
# Scans mksap_data/ and generates a validation report
```

```bash
./target/release/mksap-extractor discovery-stats
# Prints discovery metadata summary from mksap_data/.checkpoints/discovery_metadata.json
```

```bash
./target/release/mksap-extractor retry-missing
# Re-fetches missing JSON entries and prior failed-deserialize IDs
```

```bash
./target/release/mksap-extractor list-missing
# Writes remaining IDs to mksap_data/remaining_ids.txt
```

```bash
./target/release/mksap-extractor cleanup-retired
# Moves retired questions to mksap_data_failed/retired
```

```bash
./target/release/mksap-extractor cleanup-flat
# Deletes duplicate flat JSON files in system directories
```

### Environment Variables

```bash
MKSAP_SESSION=... ./target/release/mksap-extractor
# Overrides the default session cookie used for API requests
```

```bash
MKSAP_USERNAME=... MKSAP_PASSWORD=... ./target/release/mksap-extractor
# Enables automatic login before falling back to browser login
```

```bash
MKSAP_CONCURRENCY=8 ./target/release/mksap-extractor
# Overrides default parallelism for discovery/extraction
```

```bash
MKSAP_REFRESH_DISCOVERY=1 ./target/release/mksap-extractor
# Forces a fresh discovery pass (ignores cached checkpoints)
```

```bash
MKSAP_DISCOVERY_SHUFFLE=1 ./target/release/mksap-extractor
# Randomizes discovery order to reduce clustered misses from 429s/timeouts
```

```bash
MKSAP_DISCOVERY_RETRIES=5 ./target/release/mksap-extractor
# Increases retry attempts during discovery for transient errors
```

```bash
MKSAP_DISCOVERY_429_RETRIES=10 ./target/release/mksap-extractor
# Increases retry attempts specifically for 429 rate-limit responses
```

```bash
MKSAP_YEAR_START=23 MKSAP_YEAR_END=26 ./target/release/mksap-extractor
# Overrides the default year range used during discovery
```

```bash
MKSAP_QUESTION_TYPES=mcq,vdx ./target/release/mksap-extractor
# Limits discovery to specific question type codes
```

```bash
MKSAP_INSPECT_API=1 ./target/release/mksap-extractor
# Enables the API inspection phase before extraction
```

```bash
MKSAP_QUARANTINE_INVALID=1 ./target/release/mksap-extractor
# Moves invalid extracted questions to mksap_data_failed/invalid
```

### Current Implementation Notes

The extractor only supports the commands above; other configuration lives in source:

**To customize**:
1. Edit `src/main.rs`
2. Update `output_dir` (default is `../mksap_data`)
3. Rebuild: `cargo build --release`

### Planned Features

Future versions may include:
- `--system cv` - Extract specific system
- `--output-dir /path` - Configure output directory without code changes
- `--base-url https://...` - Override API host
- `--config file.toml` - External configuration

### Media Extraction (Post-Processing)

After text extraction is complete, build and run the separate media extractor:

```bash
cd ../media_extractor
cargo build --release
./target/release/media-extractor discover --discovery-file media_discovery.json
./target/release/media-extractor download --all --data-dir ../mksap_data --discovery-file media_discovery.json
```

This pass re-fetches question JSON, discovers `contentIds`, downloads figure/table assets, and updates each question's `media` field.

Media extractor arguments:

```bash
./target/release/media-extractor discover --discovery-file media_discovery.json
./target/release/media-extractor download --all --data-dir /path/to/mksap_data --discovery-file media_discovery.json
./target/release/media-extractor download --question-id cvmcq24001 --data-dir /path/to/mksap_data --discovery-file media_discovery.json
```

Environment:

```bash
MKSAP_SESSION=... ./target/release/media-extractor download --all --data-dir ../mksap_data --discovery-file media_discovery.json
# Overrides the default session cookie used for API requests
```

## Validation

### Running Validation

To validate extracted data without extracting:

```bash
# (Validator built into main.rs)
./target/release/mksap-extractor validate
```

This:
- Scans all extracted questions
- Validates JSON structure
- Checks required fields
- Generates report
- Doesn't modify anything

See [Validation Guide](VALIDATION.md) for details.

## Monitoring Extraction

### Check Progress

While extraction is running:

```bash
# In another terminal
ls -la ../mksap_data/cv/ | wc -l  # Count Cardiovascular questions
du -sh ../mksap_data/             # Total data size
```

### View Extraction Logs

Logs are printed to console. For persistent logs:

```bash
./target/release/mksap-extractor 2>&1 | tee extraction.log
```

## Storage Requirements

### Disk Space

- **Per 100 questions**: ~5-8MB
- **Total size**: depends on discovery counts and media downloads
- Use `du -sh mksap_data/` to measure current usage

## Performance

### Extraction Speed

- **Per question**: ~500-1000ms (including rate limiting)
- **Per system**: varies with discovery counts and API responsiveness
- **Full extraction**: depends on total discovered IDs and rate limiting

### Optimizations

- Async/parallel requests (Tokio)
- Incremental saving (no data loss on interruption)
- Minimal memory footprint
- Network error recovery

## Troubleshooting

### Common Issues

**Question not downloading**
- Check network connection
- Verify MKSAP API is accessible
- See [Troubleshooting Guide](TROUBLESHOOTING.md)

**Session expired**
- Delete cached session
- Re-run to authenticate
- Check credentials are valid

**Disk full**
- Check available space: `df -h`
- Move existing data to backup
- Resume after freeing space

For more help, see [Troubleshooting Guide](TROUBLESHOOTING.md).

## Next Steps

1. Extract data using this guide
2. Validate data with [Validation Guide](VALIDATION.md)
3. Review [Architecture](RUST_ARCHITECTURE.md) for technical details
4. See [Troubleshooting](TROUBLESHOOTING.md) if issues arise
