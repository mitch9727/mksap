Create a Rust program that extracts video and SVG files from ACP MKSAP questions using browser automation.

## **Problem Statement**

The ACP MKSAP platform stores videos and SVGs in hashed CDN locations. Unlike images and tables which have 
metadata API endpoints, videos require a hash value that's only available when the browser renders the page 
and initializes the video player. This program must use headless browser automation to capture video URLs 
from the DOM.

## **Architecture Overview**

The extraction requires TWO phases:

### **Phase 1: Browser Automation (Headless Chrome/Playwright)**
Use browser automation to:
1. Navigate to question pages
2. Wait for video players to render
3. Extract video URLs from the DOM or network traffic
4. Capture SVG content from the page

### **Phase 2: Data Processing (Rust)**
Process captured data and organize into structured output

## **Input**
The program should accept question IDs (e.g., "cvmcq24012") as command-line arguments or from a file.

## **API and Data Source Information**

### **Question JSON Endpoint** (to identify which questions have videos/SVGs)
- URL: `https://mksap.acponline.org/api/questions/{question_id}.json`
- Look in stimulus array for:
  - Objects with `contentIds` containing IDs starting with `cvvid` (videos)
  - Objects with `contentIds` containing IDs starting with `cvsvg` (SVGs)

### **Video URL Pattern**
- Videos are served from CloudFront: `https://d2chybfyz5ban.cloudfront.net/hashed_figures/{video_id}.{hash}.mp4`
- Status code: 206 (supports partial content/range requests)
- The hash is **NOT** available via API - must be extracted from:
  - Video `<source>` element src attribute
  - Network request interception when browser loads video
  - Analytics data (e.g., Google Analytics video tracking)

### **SVG Content Sources**
SVGs appear in two ways:
1. **Embedded in stimulus as inline elements:** Parse from question JSON's stimulus array
2. **Rendered SVGs:** Capture from DOM when page renders

### **Known Question Examples**
- `cvmcq24012`: Contains video `cvvid24201` (Title: "Apical Dyskinesis")
- Questions may contain multiple videos and/or SVGs

## **Implementation Strategy**

### **Option 1: Playwright/Puppeteer Approach (Recommended)**

Use the `playwright-rs` crate to:
```rust
// Pseudo-code structure:
// 1. Launch headless browser
// 2. For each question_id:
//    a. Navigate to question URL or load question data
//    b. Wait for video player elements to render
//    c. Extract video URLs from <video><source src="..."> elements
//    d. Intercept network requests to capture full URLs with hashes
//    e. Extract SVG elements from DOM
// 3. Download/save video files
// 4. Extract and save SVG content
// 5. Output structured data
```

### **Option 2: Network Interception Approach**

Use Playwright's network interception to:
1. Monitor all network requests made by the page
2. Filter for requests matching pattern: `*.mp4` and `*.svg`
3. Capture full URLs including hashes
4. Optionally download files during capture

### **Option 3: DOM Parsing Approach** (Lighter weight)

1. Use Playwright to render page
2. Query DOM for:
   - `<video><source src="...">` elements
   - `<svg>` elements
   - `<img>` elements with `.svg` src
3. Extract src attributes
4. Parse SVG content from inline elements

## **Data Extraction Details**

### **Video Extraction**

When browser renders a page with video content, the video element structure is:
```html
<video>
  <source src="https://d2chybfyz5ban.cloudfront.net/hashed_figures/cvvid24201.ef942062d045a470aa2c7ab3391ab6ed.mp4" type="video/mp4">
</video>
```

**Extraction process:**
1. Wait for video element to appear: `video { visibility: visible }`
2. Query for `<source>` children
3. Extract `src` attribute (this contains the full URL with hash)
4. Parse video ID and hash from URL: `{video_id}.{hash}.mp4`

**Network interception alternative:**
1. Monitor for requests containing `/hashed_figures/` and `.mp4`
2. Capture request URL (includes hash)
3. Log the full URL with video metadata

### **SVG Extraction**

SVGs may appear as:
```html
<!-- Inline SVG -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="40"/>
</svg>

<!-- External SVG -->
<img src="https://d2chybfyz5ban.cloudfront.net/assets/{hash}.svg">

<!-- SVG in data URI -->
<div style="background-image: url('data:image/svg+xml,...')"></div>
```

**Extraction process:**
1. Query all `<svg>` elements and extract innerHTML
2. Query all `<img>` elements with `src` containing `.svg`
3. Query all `[style*="background-image"]` attributes
4. Parse data URIs to extract SVG content
5. Store with metadata: location found, dimensions, etc.

## **Output Format**

Generate JSON output:
```json
{
  "question_id": "cvmcq24012",
  "videos": [
    {
      "id": "cvvid24201",
      "title": "Apical Dyskinesis",
      "download_url": "https://d2chybfyz5ban.cloudfront.net/hashed_figures/cvvid24201.ef942062d045a470aa2c7ab3391ab6ed.mp4",
      "hash": "ef942062d045a470aa2c7ab3391ab6ed",
      "duration": "0:07",
      "metadata": {
        "location_in_stimulus": true,
        "content_id": "cvvid24201",
        "type": "video/mp4"
      }
    }
  ],
  "svgs": [
    {
      "id": "unique_svg_id",
      "location": "stimulus",
      "source": "inline|external|data-uri",
      "download_url": "https://d2chybfyz5ban.cloudfront.net/assets/{hash}.svg",
      "content": "<svg>...</svg>",
      "dimensions": {
        "width": "100px",
        "height": "100px",
        "viewBox": "0 0 100 100"
      }
    }
  ],
  "extraction_method": "playwright_network_interception|dom_parsing",
  "timestamp": "2025-12-23T13:54:04Z"
}
```

## **Technical Implementation Details**

### **Dependencies**
Use these Rust crates:
- `playwright-rs` - Headless browser automation (Chromium/Firefox/Webkit)
- `tokio` - Async runtime for browser control
- `serde` and `serde_json` - JSON handling
- `reqwest` - HTTP client for downloading files (optional)
- `regex` - Pattern matching for URL parsing
- `chrono` - Timestamps
- `clap` - CLI argument parsing
- `anyhow` - Error handling
- `tracing` or `log` - Logging browser interactions

### **Code Structure**
```rust
// Module organization:
mod browser {
    // Browser initialization
    // Page navigation
    // Element waiting/querying
}

mod video_extractor {
    // Network interception setup
    // Video element detection
    // URL extraction and parsing
    // Video metadata extraction
}

mod svg_extractor {
    // SVG element detection
    // SVG content extraction
    // SVG URL parsing
}

mod data_processor {
    // JSON serialization
    // File I/O
    // Output formatting
}

#[tokio::main]
async fn main() {
    // Parse CLI arguments
    // Initialize browser
    // For each question_id:
    //   - Fetch question JSON to identify media
    //   - Navigate to question
    //   - Extract videos and SVGs
    //   - Save output
    // Close browser
}
```

### **Browser Navigation Strategy**

Since the API endpoint doesn't require the full UI, you have two approaches:

**Approach A: Direct API Loading (Lighter)**
```rust
// 1. Fetch question JSON via API
// 2. Create minimal HTML page with question content
// 3. Use Playwright to render that HTML
// 4. Extract videos/SVGs from rendered output
```

**Approach B: Full UI Navigation (More Complete)**
```rust
// 1. Open browser
// 2. Navigate to: https://mksap.acponline.org/app/question-bank/content-areas/cv/answered-questions
// 3. Click question from list
// 4. Wait for modal/question to load
// 5. Extract videos/SVGs
// Alternative: Use direct URLs if available
```

## **Error Handling & Robustness**

- **Browser crashes:** Implement retry logic (3 attempts)
- **Timeouts:** Set appropriate waits (10-30 seconds for video element appearance)
- **Missing videos/SVGs:** Log warnings but continue processing
- **Network failures:** Retry failed downloads with exponential backoff
- **Authentication:** Handle if sessions expire
- **Rate limiting:** Implement delays between requests (1-2 seconds)

## **Video Download Strategy**

Since video files can be large (several MB):
```rust
// Option 1: Stream download
// - Start download
// - Show progress
// - Save to disk

// Option 2: Capture metadata only
// - Store URLs
// - Don't download (requires manual download)
// - Save metadata JSON

// Option 3: Hybrid
// - Download videos to designated directory
// - Update JSON with local file paths
```

## **Testing**

Test with these known questions:
- `cvmcq24012` - Has video `cvvid24201`
- Search for other questions by trying various IDs or fetching question list

Verify extraction by:
1. Checking video URLs are valid (return HTTP 200/206)
2. Checking SVG content is valid XML
3. Comparing extracted URLs with what you see in browser DevTools

## **Example Usage**
```bash
# Single question
cargo run --release -- extract-media cvmcq24012

# Multiple questions from file
cargo run --release -- extract-media --file question_ids.txt

# With video download
cargo run --release -- extract-media cvmcq24012 --download-videos --output-dir ./media

# Network interception mode
cargo run --release -- extract-media cvmcq24012 --method network-intercept
```

## **Performance Considerations**

- Browser automation is slow (30-60 seconds per question)
- Process multiple questions in parallel with browser pooling
- Consider caching: If video URL already extracted, skip re-fetching
- Network interception method is slower but more complete
- DOM parsing method is faster but may miss some SVGs

## **Key Challenges & Solutions**

| Challenge | Solution |
|-----------|----------|
| Hash not in API | Use network interception or DOM parsing |
| Page requires rendering | Use Playwright to load full page |
| Dynamic content loading | Use explicit waits for elements |
| Large video files | Stream download or skip download step |
| Multiple SVG sources | Check inline, external, and data-uri sources |
| Browser stability | Use pooling and restart crashed instances |

## **Deliverables**

The program should produce:
1. A JSON file with all extracted video and SVG metadata
2. Downloaded video files (optional, based on flags)
3. SVG files or inline SVG content in JSON
4. Detailed logs of extraction process
5. Error report if any questions fail to process