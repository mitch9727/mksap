# Rust MKSAP Extractor - Architecture

## System Architecture

The Rust MKSAP Extractor follows a modular, async-first architecture optimized for API-based data extraction.

## Module Structure

### Main Entry Point (`main.rs` - 309 lines)

**Responsibilities**:
- Initialize application
- Handle command-line interface
- Orchestrate extraction phases
- Manage authentication

**Key Functions**:
- `main()` - Application entry point
- `authenticate()` - Handle session management
- `run_extraction()` - Coordinate extraction process
- `validate_extraction()` - Run data validation

### Configuration (`config.rs` - 162 lines)

**Responsibilities**:
- Define all 12 organ systems
- Map system IDs, codes, and metadata
- Provide system lookup functions

**Key Structures**:
```rust
pub struct OrganSystem {
    pub id: String,              // cv, en, hm, etc.
    pub name: String,            // Full system name
    pub url_slug: String,        // Web UI code
    pub api_code: String,        // API code for question IDs
    pub total_questions: u32,    // Expected question count
}
```

**Key Functions**:
- `init_organ_systems()` - Returns all 12 systems
- `get_organ_system_by_id()` - Lookup by ID
- `get_organ_system_by_api_code()` - Lookup by API code

### Data Models (`models.rs` - 279 lines)

**Structures**:
- `QuestionData` - Complete question object
- `ApiQuestionResponse` - API response format
- `AnswerOption` - Multiple choice option
- `QuestionMetadata` - Metadata fields
- `RelatedContent` - Related syllabus/figures

**Serialization**: All structures derive `Serialize`/`Deserialize` for JSON conversion

### Extraction Logic (`extractor.rs` - 407 lines)

**Three-Phase Extraction**:

#### Phase 1: Discovery
```rust
async fn discover_questions(&self, category_code: &str) -> Result<Vec<String>>
```
- Generate question IDs (pattern: `{code}mcq{year}{number}`)
- Test existence with HEAD requests
- Collect valid question IDs

#### Phase 2: Download
```rust
async fn extract_question(&mut self, category_code: &str, id: &str) -> Result<bool>
```
- GET request to API endpoint
- Deserialize JSON response
- Transform to internal format
- Save to disk

#### Phase 3: Media
```rust
async fn download_media(&mut self, question: &QuestionData) -> Result<()>
```
- Extract media URLs from question
- Download images, videos, SVGs
- Save with question directory

**Rate Limiting**:
- 500ms delay between requests
- 60s backoff on 429 (rate limit) responses
- Automatic retry on transient errors

### Validation (`validator.rs` - 299 lines)

**Responsibilities**:
- Scan extracted question files
- Validate JSON structure
- Check required fields
- Generate validation reports

**Key Structures**:
```rust
pub struct ValidationResult {
    pub total_found: u32,
    pub total_valid: u32,
    pub total_invalid: u32,
    pub system_validations: Vec<SystemValidation>,
}
```

**Non-Destructive**: Only reads files, creates no modifications

### Media Handling (`media.rs` - 107 lines)

**Responsibilities**:
- Download image files (PNG, JPG, GIF, WebP)
- Download video files (MP4, WebM, OGG)
- Download SVG files
- Store HTML tables

**Naming**: `{question_id}_{index}.{extension}`

### Browser Automation (`browser.rs` - 107 lines)

**Fallback Authentication**:
- Opens Chrome browser if API auth fails
- Allows manual login
- Detects successful authentication
- Extracts session cookie

**Platform Support**: macOS, Linux, Windows

### Utilities (`utils.rs` - 87 lines)

**Text Processing**:
- Parse nested JSON nodes
- Extract plain text from HTML
- Format output

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
3. FOR EACH SYSTEM (12 total)
   ├─ DISCOVER PHASE
   │  ├─ Generate question IDs
   │  ├─ HEAD request (existence check)
   │  └─ Collect valid IDs
   │
   ├─ EXTRACT PHASE
   │  ├─ GET /api/questions/{id}.json
   │  ├─ Deserialize JSON
   │  ├─ Transform format
   │  ├─ Save JSON file
   │  └─ Save metadata file
   │
   ├─ MEDIA PHASE
   │  ├─ Extract media URLs
   │  ├─ Download files
   │  └─ Save to question directory
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
GET /api/questions/{question_id}.json
```

**Authentication**:
- Session-based cookies
- `_mksap19_session` cookie required
- Auto-refresh on 401 response

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
- **regex**: Pattern matching
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
- Separate metadata files

## Extensibility Points

### Adding New Systems

1. Add to `config.rs`:
```rust
OrganSystem {
    id: "new_system".to_string(),
    name: "New System Name".to_string(),
    url_slug: "new_slug".to_string(),
    api_code: "ns".to_string(),
    total_questions: 100,
}
```

2. Extractor automatically handles the rest

### Custom Validation

Extend `validator.rs`:
- Add new validation check function
- Call from `validate_extraction()`
- Include in report generation

### Media Handling

Extend `media.rs`:
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
- Session cookies stored locally
- Credentials in source code (development only)
- HTTPS for all API calls

### Recommendations
- Use environment variables for credentials
- Implement secure credential storage
- Add rate limiting to respect API terms
- Implement request signing if available

## Next Steps

1. Review [Setup Guide](setup.md) to build
2. Follow [Usage Guide](usage.md) to run
3. Check [Validation Guide](validation.md) for quality
4. See [Troubleshooting](troubleshooting.md) for issues
