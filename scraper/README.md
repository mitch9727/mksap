# MKSAP Headless Scraper

A robust, state-machine driven scraper for extracting MKSAP medical questions into structured JSON format.

## Features
- **Deterministic State Machine**: Robust navigation and error recovery
- **Structured JSON Output**: One question per JSON object with complete schema
- **Asset Management**: Downloads figures and extracts tables with references
- **Interactive Selector Discovery**: Built-in tool to identify page elements
- **Session Persistence**: Remembers authentication across runs
- **Syllabus Integration**: Extracts "Related Text" content when available

## Quick Start

### Installation
```bash
cd scraper
npm install
```

### Discover Selectors (First Time)
Before running the scraper, you need to discover the CSS selectors for the MKSAP site:

```bash
npm run discover
```

This launches an interactive tool that:
1. Opens the browser in headful mode
2. Guides you through each page element
3. Saves discovered selectors to `config/selectors.json`
4. Updates `src/selectors.js` with your selectors

### Run the Scraper
```bash
npm start
```

**First run:** Browser launches in headful mode for manual login
**Subsequent runs:** Browser launches in headless mode (uses saved session)

## Workflow

### Step 1: Run Discovery (One Time)
```bash
npm run discover
```
- Browser opens to MKSAP
- Follow prompts in terminal
- Inspect elements in DevTools (F12)
- Copy CSS selectors
- Tool saves configuration automatically

### Step 2: Run Scraper
```bash
npm start
```
- If no auth exists: Manual login (browser visible)
- If auth exists: Automatic headless mode
- Navigates to question list
- Extracts each question's data
- Saves to `output/data.jsonl`

## Output Format

### Main Output: `output/data.jsonl`
One JSON object per line (NDJSON). Each line contains:

```json
{
  "ID": "CVMCQ24042",
  "Reference": "Section reference text",
  "Last Updated": "12/10/2024",
  "Educational Objective": "Objective text",
  "Care type": "Inpatient or Outpatient",
  "Answer and Critique": "Full explanation text",
  "Key Point": "Key learning points",
  "Figures": [
    {
      "originalSrc": "https://...",
      "itemPath": "figures/main_fig_1.jpg",
      "alt": "Figure description"
    }
  ],
  "Tables": [
    {
      "fileName": "table_main_1.html",
      "html": "<table>...</table>"
    }
  ],
  "Videos": [],
  "Related Text": {
    "breadcrumbs": "Section > Subsection > Topic",
    "bodyHtml": "...",
    "figures": [...],
    "tables": [...]
  }
}
```

### Asset Storage
```
output/
├── data.jsonl              # Main data file
└── QUESTIONID/
    ├── figures/            # Downloaded images
    │   ├── main_fig_1.jpg
    │   └── main_fig_2.jpg
    └── tables/             # Extracted table HTML
        ├── table_main_1.html
        └── table_main_2.html
```

## Configuration

### Update Base URL
Edit `scraper/config/default.js`:
```javascript
baseUrl: 'https://mksap.acponline.org'  // Change if needed
```

### Update Selectors
Run `npm run discover` again to re-discover selectors, or manually edit `src/selectors.js`

## Troubleshooting

### Selectors Not Working?
1. Run `npm run discover` to re-identify elements
2. Check browser console for errors (logs in `logs/scraper.log`)
3. Ensure MKSAP website structure hasn't changed significantly

### Login Issues?
- Delete `config/auth.json` to force re-login
- Run `npm start` again
- Manually log in when browser appears

### Missing Data Fields?
- Check that all selectors are correctly identified
- Some fields may be optional (Videos, Related Text)
- Empty fields default to `""` or `[]`

## Development

### Project Structure
```
scraper/
├── main.js                    # Entry point
├── discover-selectors.js      # Interactive selector tool
├── package.json
├── README.md                  # This file
├── config/
│   ├── default.js             # Configuration
│   ├── auth.json              # Auto-generated (session storage)
│   └── selectors.json         # Auto-generated (discovered selectors)
├── output/                    # Generated data
├── logs/                      # Scraper logs
└── src/
    ├── stateMachine.js        # State orchestrator
    ├── selectors.js           # CSS selector definitions
    ├── states/                # State implementations
    │   ├── base.js
    │   ├── init.js
    │   ├── login.js
    │   ├── navigate.js
    │   └── process_questions.js
    ├── extractors/            # Content extractors
    │   ├── figures.js
    │   ├── tables.js
    │   └── syllabus.js
    └── utils/                 # Utilities
        ├── fileSystem.js
        ├── htmlParser.js
        └── jsonWriter.js
```

### States
1. **INIT**: Launch browser, check auth status
2. **LOGIN**: Authenticate (manual or cached)
3. **NAVIGATE**: Go to question list
4. **PROCESS_QUESTIONS**: Extract each question to JSON
5. **EXIT**: Clean shutdown
