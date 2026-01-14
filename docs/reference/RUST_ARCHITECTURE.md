# Rust MKSAP Extractor - Architecture

## System Architecture

The extractor follows a modular, async-first architecture optimized for API-based data extraction, with an integrated
asset discovery/download subsystem.

## Module Structure

### Main Entry Point

**Responsibilities**:
- Load `.env` and initialize logging
- Parse command-line arguments
- Configure base URL and output directory
- Dispatch extraction, validation, and media commands

**Key Functions**:
- `main()` - Application entry point
- `authenticate_extractor()` - Authentication flow
- `extract_category()` - Per-system extraction pipeline
- `validate_extraction()` / `show_discovery_stats()`

### Configuration

**Responsibilities**:
- Define all 16 system codes (including `fc` and `cs`)
- Store display names for system lookup
- Provide system lookup functions

**Key Structures**:
```rust
pub struct OrganSystem {
    pub id: String,                  // cv, en, fc, cs, etc.
    pub name: String,                // Full system name
}
```

**Key Functions**:
- `init_organ_systems()` - Returns all 16 system codes
- `get_organ_system_by_id()` - Lookup by ID

### Data Models

**Structures**:
- `QuestionData` - Complete question object
- `ApiQuestionResponse` - API response format
- `AnswerOption` - Multiple choice option
- `QuestionMetadata` - Metadata fields
- `UserPerformance` - Answer tracking fields
- `RelatedContent` - Related content references and learning plan topic
- `MediaFiles` - Tables/images/videos/SVGs arrays (video files are manual)

**Serialization**: All structures derive `Serialize`/`Deserialize` for JSON conversion

### Extraction Logic

**Three-Phase Extraction**:

#### Phase 1: Discovery
```rust
async fn discover_questions(&self, question_prefix: &str, existing: &HashSet<String>) -> Result<Vec<String>>
```
- Generate question IDs (pattern: `{code}{type}{year}{number}`)
- Test existence with HEAD requests
- Cache IDs in `.checkpoints/{system}_ids.txt`

#### Phase 2: Directory Setup
- Create `{output_dir}/{system}/{question_id}/` folders for each valid ID

#### Phase 3: Download + Save
```rust
async fn extract_question(&self, category_code: &str, id: &str) -> Result<bool>
```
- GET request to API endpoint
- Deserialize JSON response
- Skip `invalidated` questions
- Save `{question_id}.json` to disk

**Rate Limiting**:
- Discovery retries use short backoff on transient errors
- Extraction backs off for 429 (rate limit) responses
- 10s HEAD timeout and 30s GET timeout

### Validation

**Responsibilities**:
- Scan extracted question files
- Validate JSON structure
- Check required fields
- Generate validation reports

**Key Structures**:
```rust
pub struct ValidationResult {
    pub total_questions: usize,
    pub valid_questions: usize,
    pub invalid_questions: Vec<String>,
    pub missing_fields: Vec<(String, Vec<String>)>,
    pub missing_json: Vec<String>,
    pub parse_errors: Vec<String>,
    pub schema_invalid: Vec<String>,
    pub systems_verified: Vec<SystemValidation>,
}
```

**Non-Destructive**: Only reads files, creates no modifications **Discovery-Aware**: Uses
`.checkpoints/discovery_metadata.json` when available

### Asset Pipeline

**Responsibilities**:
- Discover media content IDs after text extraction
- Download images, tables, and SVGs (videos are manual)
- Update the `media` field in each `{question_id}.json`
- Store assets alongside question folders

### Browser Login

**Fallback Authentication**:
- Opens Chrome browser if API auth fails
- Allows manual login
- Detects successful authentication (best effort)
- Does not automatically persist browser cookies to the Rust client

**Platform Support**: macOS

### IO + Retry

**File IO**:
- Save JSON payloads
- Read/write checkpoint files
- Quarantine invalid data when enabled

**Retry Helpers**:
- Re-fetch missing JSON
- Re-run failed deserialize IDs
- Detect checkpoint IDs with missing JSON

## Data Flow

### Extraction Pipeline

```
1. START
   ↓
2. AUTHENTICATE
   ├─ Check saved session
   ├─ Try API login
   └─ Fallback to browser login
   ↓
3. FOR EACH SYSTEM (16 total)
   ├─ DISCOVER PHASE
   │  ├─ Generate question IDs
   │  ├─ HEAD request (existence check)
   │  └─ Collect valid IDs
   │
   ├─ EXTRACT PHASE
   │  ├─ GET /api/questions/{id}.json
   │  ├─ Deserialize JSON
   │  ├─ Transform format
   │  └─ Save JSON file
   │
   └─ REPEAT for next system
   ↓
4. VALIDATE (Optional)
   ├─ Scan mksap_data/
   ├─ Check each question
   └─ Generate report
   ↓
5. END
```

## API Integration

### MKSAP API Endpoints

**Base URL**: `https://mksap.acponline.org`

**Question API**:
```
HEAD /api/questions/{question_id}.json
GET /api/questions/{question_id}.json
```

**Authentication**:
- Session-based cookies
- `_mksap19_session` cookie required
- Browser login is best-effort; prefer `MKSAP_SESSION` for API access

### API Response Format

**JSON Structure**:
```json
{
  "id": "cvmcq25001",
  "subspecialtyId": "cv",
  "correctAnswer": "C",
  "stimulus": [{"type": "p", "children": [...]}],
  "prompt": [{"type": "p", "children": [...]}],
  "options": [
    {"letter": "A", "text": "..."},
    ...
  ],
  "exposition": [{"type": "p", "children": [...]}],
  "keypoints": [{"type": "p", "children": [...]}],
  "references": [...],
  "updatedDate": "2025-10-21",
  ...
}
```

**Nested Node Extraction**: Recursive traversal of nested `children` arrays to extract plain text

## Technology Stack

### Runtime
- **Tokio**: Async runtime with full features
- **reqwest**: HTTP client with JSON support

### Parsing
- **scraper**: CSS selector-based HTML parsing
- **select**: DOM traversal
- **serde**: Serialization framework
- **serde_json**: JSON handling

### Utilities
- **chrono**: Date/time handling
- **uuid**: Unique identifiers
- **futures**: Async stream helpers
- **anyhow**: Error handling

## Performance Characteristics

### Memory Usage
- Minimal footprint (async handles concurrency)
- Streaming JSON parsing
- Incremental file saves

### Network Optimization
- Efficient request-response cycling
- Rate limiting respects server
- Automatic retry on failures

### Disk I/O
- Organized directory structure
- Incremental writes (resumable)
- JSON-only question files (media added later)

## Extensibility Points

### Adding New Systems

1. Add to the system configuration list:
```rust
OrganSystem {
    id: "ns".to_string(),
    name: "New System Name".to_string(),
}
```

2. Extractor automatically handles the rest

### Custom Validation

Extend the validation module:
- Add new validation check function
- Call from `validate_extraction()`
- Include in report generation

### Media Handling

Extend the asset subsystem:
- Add support for new file types
- Update content-type detection
- Customize file naming

## Error Handling

### Strategy
- Non-fatal errors logged, extraction continues
- Fatal errors halt with context
- All errors include recovery suggestions

### Common Errors
- 404: Question doesn't exist (skipped)
- 401/403: Authentication expired (re-authenticate)
- 429: Rate limited (backoff and retry)
- Network timeout: Retry with backoff

## Testing Approach

### Current
- Manual testing during development
- Validation suite for data quality

### Potential Additions
- Unit tests for config, models
- Integration tests for extraction
- Mock API tests
- Validation regression tests

## Security Considerations

### Current Implementation
- Session cookie provided via environment variable
- Browser login is interactive and best-effort
- HTTPS for all API calls

### Recommendations
- Use environment variables for credentials
- Store secrets in a local `.env` (not committed)
- Add stronger credential storage if needed
- Keep rate limiting conservative to respect API terms

## Next Steps

1. Review [Setup Guide](RUST_SETUP.md) to build
2. Follow [Usage Guide](RUST_USAGE.md) to run
3. Check [Validation Guide](VALIDATION.md) for quality
4. See [Troubleshooting](TROUBLESHOOTING.md) for issues
