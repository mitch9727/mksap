# Quick Start Guide - MKSAP Scraper

## What This Does
Automatically scrapes MKSAP medical questions into structured JSON format for processing into Anki flashcards.

## Files to Know
- **Main docs**: `README.md` (overview), `CLAUDE_CODER_INSTRUCTIONS.md` (complete spec)
- **Scraper docs**: `scraper/README.md` (usage), `scraper/SELECTORS_REFERENCE.md` (how data is extracted)
- **Data format**: `READMEs/README_v7.md` (MCQ markdown specification)

## Setup (First Time Only)

```bash
# 1. Install dependencies
cd scraper
npm install

# 2. Run scraper (browser will open for manual login)
npm start

# 3. Log into MKSAP when browser appears
# → System saves auth automatically

# 4. Wait for scraping to complete
# → Check output: scraper/output/data.jsonl
```

## Usage (Subsequent Runs)

```bash
cd scraper
npm start
```

→ Browser runs headless, uses saved auth, scrapes autonomously

## Output Location

**Main file**: `scraper/output/data.jsonl`
- One JSON object per line (NDJSON format)
- Each line contains: ID, objectives, answer, key points, references, figures, tables, related text

**Assets**:
- Figures: `scraper/output/QUESTIONID/figures/`
- Tables: `scraper/output/QUESTIONID/tables/`

## Example Output

```json
{
  "ID": "CVMCQ24042",
  "Educational Objective": "Diagnosis and management of acute coronary syndrome",
  "Care type": "Inpatient, Outpatient",
  "Answer and Critique": "Full explanation text...",
  "Key Point": "Point 1\nPoint 2",
  "Reference": "Section citation",
  "Last Updated": "June 2025",
  "Figures": [{"originalSrc": "https://...", "itemPath": "figures/main_fig_1.jpg", "alt": "..."}],
  "Tables": [{"fileName": "table_main_1.html", "html": "<table>...</table>"}],
  "Videos": [],
  "Related Text": {"breadcrumbs": "Topic > Subtopic", "bodyHtml": "...", "figures": [], "tables": []}
}
```

## Architecture

```
5-State Machine:
  INIT (setup) → LOGIN (auth) → NAVIGATE (go to questions)
    → PROCESS_QUESTIONS (extract all) → EXIT (cleanup)
```

## Common Tasks

### View logs
```bash
tail -f scraper/logs/scraper.log
```

### Force re-login (reset auth)
```bash
rm scraper/config/auth.json
npm start
```

### Check if selectors work
→ If errors, see `scraper/SELECTOR_DISCOVERY_GUIDE.md`

### Convert JSON to Anki
→ Downstream project (see `README.md` for pipeline)

## Key Technologies

- **Playwright** - Browser automation
- **Cheerio** - HTML parsing
- **Winston** - Logging
- **Node.js** - Runtime

## Project Status

✅ Scraper: Complete and tested
✅ JSON output: Ready for processing
⏳ Anki generator: Pending (next phase)

## Need Help?

1. **How the scraper works**: `CLAUDE_CODER_INSTRUCTIONS.md`
2. **How to use it**: `scraper/README.md`
3. **How data is extracted**: `scraper/SELECTORS_REFERENCE.md`
4. **How to update selectors**: `scraper/SELECTOR_DISCOVERY_GUIDE.md`
5. **Output format**: `READMEs/README_v7.md`

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Selector not found" | Update selectors (see SELECTOR_DISCOVERY_GUIDE.md) |
| Login timeout | Delete auth.json, log in within 5 minutes |
| No questions extracted | Check logs: `tail -f scraper/logs/scraper.log` |
| Figures not downloading | Check internet, verify URLs are accessible |

---

**Next Step**: `cd scraper && npm start`
