# Rust MKSAP Extractor - Usage Guide

## Basic Usage

### Running the Extractor

```bash
cd /Users/Mitchell/coding/projects/MKSAP
./target/release/mksap-extractor
```

### First Run (Authentication Required)

On first run, the extractor will:
1. Check for existing session credentials
2. If missing, open a browser window
3. Wait for you to log in manually (5-minute timeout)
4. Save session for future runs
5. Begin extraction

**Expected behavior**:
```
🚀 MKSAP Extractor Starting...
[INFO] Checking authentication...
[INFO] No saved session found. Opening browser for login...
[Browser window opens]
⏰ Waiting for login... (5 minutes remaining)
✓ Login successful!
📋 Starting extraction...
```

### Subsequent Runs (Automatic)

Sessions are cached, so subsequent runs authenticate automatically:

```bash
./target/release/mksap-extractor
# Immediately begins extraction without requiring login
```

## Output Structure

### Directory Organization

Extracted questions are organized by organ system:

```
mksap_data/
├── cv/    # Cardiovascular Medicine
│   ├── cvmcq24001/
│   │   ├── cvmcq24001.json
│   │   └── cvmcq24001_metadata.txt
│   └── cvmcq24002/ ...
├── en/    # Endocrinology
├── hm/    # Hematology
├── id/    # Infectious Disease
├── np/    # Nephrology
├── nr/    # Neurology
├── on/    # Oncology
└── rm/    # Rheumatology
```

### Question Files

#### JSON Format
`{question_id}.json` contains complete question data:

```json
{
  "question_id": "cvmcq24001",
  "category": "cv",
  "educational_objective": "Treat cardiogenic shock",
  "question_text": "A 67-year-old woman is hospitalized...",
  "question_stem": "Which is the most appropriate management?",
  "options": [
    {"letter": "A", "text": "Biventricular pacemaker-defibrillator"},
    {"letter": "B", "text": "Coronary angiography"},
    {"letter": "C", "text": "Percutaneous mechanical support"},
    {"letter": "D", "text": "Pulmonary artery pressure sensor"}
  ],
  "correct_answer": "C",
  "critique": "The most appropriate management for this patient...",
  "key_points": [
    "Treatment of cardiogenic shock focuses on...",
    "Mechanical support options include..."
  ],
  "references": "Sinha SS, et al. [PMID: 40100174]",
  "metadata": {
    "care_types": ["Hospital"],
    "patient_types": ["Geriatric"],
    "last_updated": "2025-10-21"
  }
}
```

#### Metadata Format
`{question_id}_metadata.txt` contains human-readable summary:

```
Question ID: cvmcq24001
Category: Cardiovascular Medicine
Educational Objective: Treat cardiogenic shock
Care Type: Hospital
Patient Type: Geriatric
Last Updated: October 2025
Extracted: 2025-12-22
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

### Force Full Re-extraction

To re-extract all questions:

```bash
rm -rf mksap_data/
./target/release/mksap-extractor
# Starts completely fresh
```

## Extraction Progress

### Progress Indicators

During extraction, you'll see:

```
📋 Starting extraction for: Cardiovascular Medicine (cv)
[████████░░░░░░░░░░░░░░░░░░] 32%
Processing: cvmcq24001... ✓
Processing: cvmcq24002... ✓
[After 10 questions]
✓ Successfully extracted: 10 questions
✓ Cardiovascular Medicine complete: 132/216 questions

Moving to next system...
```

### Rate Limiting

The extractor automatically:
- Waits 500ms between API requests (respects server limits)
- Implements backoff on rate limiting (429 errors)
- Continues on non-critical errors
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
./target/release/mksap-extractor retry-missing
# Re-fetches missing JSON entries and prior failed-deserialize IDs
```

```bash
./target/release/mksap-extractor list-missing
# Writes remaining IDs to ../mksap_data/remaining_ids.txt
```

### Environment Variables

```bash
MKSAP_SESSION=... ./target/release/mksap-extractor
# Overrides the default session cookie used for API requests
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
MKSAP_QUARANTINE_INVALID=1 ./target/release/mksap-extractor
# Moves invalid extracted questions to mksap_data_failed/invalid
```

### Current Implementation Notes

The extractor only supports the commands above; other configuration lives in source:

**To customize**:
1. Edit `src/main.rs`
2. Modify credentials/timeouts as needed
3. Rebuild: `cargo build --release`

### Planned Features

Future versions may include:
- `--system cv` - Extract specific system
- `--resume` - Explicitly resume previous run
- `--validate` - Run validation only
- `--config file.toml` - External configuration

### Media Extraction (Post-Processing)

After text extraction is complete, build and run the separate media extractor:

```bash
cargo build --release --bin media-extractor
./target/release/media-extractor
```

This pass re-fetches question JSON, discovers `contentIds`, downloads figure/table assets, and updates each question's `media` field.

Media extractor arguments:

```bash
./target/release/media-extractor /path/to/mksap_data
./target/release/media-extractor /path/to/mksap_data https://mksap.acponline.org
```

Environment:

```bash
MKSAP_SESSION=... ./target/release/media-extractor
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

See [Validation Guide](validation.md) for details.

## Monitoring Extraction

### Check Progress

While extraction is running:

```bash
# In another terminal
ls -la mksap_data/cv/ | wc -l  # Count Cardiovascular questions
du -sh mksap_data/              # Total data size
```

### View Extraction Logs

Logs are printed to console. For persistent logs:

```bash
./target/release/mksap-extractor 2>&1 | tee extraction.log
```

## Storage Requirements

### Disk Space

- **Per 100 questions**: ~5-8MB
- **Current (754 questions)**: ~40-60MB
- **Final (1,810 questions)**: ~100-150MB

### Example Growth

```
Cardiovascular (132 q):   6-8MB
Endocrinology (101 q):    5-6MB
Hematology (72 q):        4MB
... (more systems)
Final estimate:           100-150MB
```

## Performance

### Extraction Speed

- **Per question**: 500-1000ms (including rate limiting)
- **Per system**: 30-60 minutes (depending on count)
- **Full extraction**: 24-48 hours (all 1,810 questions)

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
- See [Troubleshooting Guide](troubleshooting.md)

**Session expired**
- Delete cached session
- Re-run to authenticate
- Check credentials are valid

**Disk full**
- Check available space: `df -h`
- Move existing data to backup
- Resume after freeing space

For more help, see [Troubleshooting Guide](troubleshooting.md).

## Next Steps

1. Extract data using this guide
2. Validate data with [Validation Guide](validation.md)
3. Review [Architecture](architecture.md) for technical details
4. See [Troubleshooting](troubleshooting.md) if issues arise
