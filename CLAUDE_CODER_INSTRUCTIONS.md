# MKSAP Scraper - Implementation Status

## Current State: ✅ FULLY IMPLEMENTED & READY TO TEST

This project implements an autonomous MKSAP question scraper that extracts medical MCQs into structured JSON (JSONL format).

## Architecture: State Machine

The scraper uses a deterministic finite state machine with the following states:

1. **INIT** - Browser initialization
   - Launches Chromium with Playwright
   - Detects if authentication exists
   - Selects headful mode (no auth) or headless mode (auth exists)

2. **LOGIN** - Authentication
   - If no auth: Opens browser in headful mode for manual login
   - Waits for login indicator: `span[data-testid="greeting"]`
   - Saves authenticated session to `config/auth.json`
   - If auth exists: Loads and validates session

3. **NAVIGATE** - Automated navigation to question list
   - Clicks: Question Bank → Cardiovascular Medicine → Answered Questions
   - Waits for page loads with `waitForLoadState('networkidle')`
   - Validates question list appears

4. **PROCESS_QUESTIONS** - Main extraction loop
   - Gets all questions from current page
   - For each question:
     - Clicks to open modal
     - Extracts all data fields (ID, objectives, answer, etc.)
     - Downloads figures and extracts tables
     - Extracts related text/syllabus if available
     - Saves to `output/data.jsonl`
   - Handles pagination automatically

5. **EXIT** - Clean browser shutdown

## Data Extraction

### Output Format: JSONL (Newline-Delimited JSON)
File: `output/data.jsonl` - One JSON object per line

Schema per question:
```json
{
  "ID": "CVMCQ24042",
  "Reference": "Section citation",
  "Last Updated": "June 2025",
  "Educational Objective": "Learning objective text",
  "Care type": "Inpatient, Outpatient",
  "Answer and Critique": "Full explanation text",
  "Key Point": "Key learning point(s)",
  "Figures": [
    {"originalSrc": "https://...", "itemPath": "figures/main_fig_1.jpg", "alt": "description"}
  ],
  "Tables": [
    {"fileName": "table_main_1.html", "html": "<table>...</table>"}
  ],
  "Videos": [],
  "Related Text": {
    "breadcrumbs": "Topic > Subtopic",
    "bodyHtml": "...",
    "figures": [],
    "tables": []
  }
}
```

### Asset Storage
- Figures: `output/QUESTIONID/figures/`
- Tables: `output/QUESTIONID/tables/`
- Syllabus assets: Same directory structure, labeled with 'syllabus' context

## Selectors

All CSS selectors have been manually discovered and verified. See [scraper/SELECTORS_REFERENCE.md](scraper/SELECTORS_REFERENCE.md) for complete reference.

Key selectors:
- **Login**: `span[data-testid="greeting"]`
- **Question Item**: `button.list-group-item.list-group-item-action`
- **Answer & Critique**: `div.critique`
- **Figures**: `img[src*="d2chybfyz5ban.cloudfront.net"]`
- **Tables**: `table` (inline) + `a.callout[href*="/tables/"]` (modal)
- **Breadcrumbs**: `ol.page-location li span`

## Project Structure

```
scraper/
├── main.js                           # Entry point
├── package.json                      # Dependencies (Playwright, Cheerio, Winston)
├── SELECTORS_REFERENCE.md           # Complete selector documentation
├── SELECTOR_DISCOVERY_GUIDE.md      # How to discover selectors (reference)
├── README.md                        # Usage and setup instructions
├── config/
│   ├── default.js                  # Configuration settings
│   ├── auth.json                   # Auto-generated: authentication state
│   └── selectors.json              # Auto-generated: selector backup
├── output/                         # Auto-generated: scraped data
│   ├── data.jsonl                 # Main output file
│   └── QUESTIONID/
│       ├── figures/               # Downloaded images
│       └── tables/                # Extracted table HTML
├── logs/                          # Auto-generated: execution logs
└── src/
    ├── stateMachine.js            # State machine orchestrator
    ├── selectors.js               # CSS selector definitions (MASTER FILE)
    ├── states/
    │   ├── base.js               # Base state class
    │   ├── init.js               # Browser initialization
    │   ├── login.js              # Authentication handling
    │   ├── navigate.js           # Navigation to question list
    │   └── process_questions.js  # Main extraction logic
    ├── extractors/
    │   ├── figures.js            # Figure/image extraction
    │   ├── tables.js             # Table extraction (inline + modal)
    │   └── syllabus.js           # Related text/syllabus extraction
    └── utils/
        ├── jsonWriter.js         # JSONL writer
        ├── fileSystem.js         # Asset management & downloads
        └── htmlParser.js         # HTML cleaning & text extraction
```

## Usage

### Installation
```bash
cd scraper
npm install
```

### First Run (Manual Login Required)
```bash
npm start
```
- Browser opens in headful mode
- Manually log in to MKSAP
- System auto-detects login and saves authentication

### Subsequent Runs (Headless)
```bash
npm start
```
- Browser launches in headless mode
- Uses saved authentication automatically
- Scrapes all questions autonomously

### Clean Up Auth (Force Re-login)
```bash
rm config/auth.json
npm start
```

## Implementation Details

### What Works
✅ Automated browser navigation with error handling
✅ Interactive selector discovery (manual inspection process documented)
✅ Text extraction from all question fields
✅ Multiple tag handling (care type, key points)
✅ Inline table extraction
✅ Modal-based table opening and extraction
✅ Figure download with metadata
✅ Syllabus/related text extraction with breadcrumbs
✅ Pagination support
✅ JSONL output with proper schema
✅ Session persistence (headless operation)
✅ Error handling with screenshots
✅ Comprehensive logging to file and console

### Known Limitations
- Selectors are MKSAP-specific and may need updates if site structure changes
- Videos are currently placeholder (no extraction logic)
- Some optional fields may be empty depending on question

## Troubleshooting

### "Selectors not working" Error
→ MKSAP HTML structure may have changed. Run the manual discovery process (see SELECTOR_DISCOVERY_GUIDE.md) and update selectors.js

### "Login timeout"
→ Manual login took too long. Delete auth.json and try again with 5 minutes to log in.

### "No questions found"
→ Check if user is authenticated and navigation selectors are correct. View browser logs.

## Next Steps (Downstream Projects)

The output `data.jsonl` is ready to be processed by:
1. **Anki Card Generator** - Converts JSON to Anki-compatible format
2. **Markdown Converter** - Generates README_v7.md compatible markdown
3. **CSV Exporter** - Converts to spreadsheet format for analysis
