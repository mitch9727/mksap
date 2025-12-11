# Codebase Guide for Claude Code Agents

## What This Project Does

This is a **medical question scraper** that:
1. Opens a browser to MKSAP.acponline.org
2. Logs in automatically (or with manual help)
3. Navigates to Cardiovascular Medicine → Answered Questions
4. Extracts each question's complete data:
   - Metadata: ID, objectives, care type, dates
   - Content: Answer explanation, key points, references
   - Assets: Figures (downloaded), tables (extracted), related text (with breadcrumbs)
5. Outputs everything to JSON (JSONL format)

## Architecture at a Glance

```
Browser (Playwright)
    ↓
State Machine (5 states)
    ├── INIT: Browser setup
    ├── LOGIN: Authentication
    ├── NAVIGATE: Go to question list
    ├── PROCESS_QUESTIONS: Extract questions in loop
    └── EXIT: Cleanup
    ↓
JSONL Output (scraper/output/data.jsonl)
```

## Key Files to Understand

### Entry Point
**`scraper/main.js`** - Start here
- Creates directories
- Initializes state machine
- Handles top-level errors
- ~50 lines, well-commented

### State Machine Core
**`scraper/src/stateMachine.js`** - Orchestrator
- Manages state transitions
- Holds browser, context, page instances
- Handles logging
- ~100 lines

### States (one per file)
**`scraper/src/states/`** - Implementation details
- `base.js` - Base class (getter/setter for logger, page)
- `init.js` - Launch browser, detect headless vs headful
- `login.js` - Handle authentication, save session
- `navigate.js` - Click through navigation (4 clicks)
- `process_questions.js` - Main loop: get questions, extract data, save JSON

Each state returns the next state name or 'EXIT'.

### Selectors (Master Configuration)
**`scraper/src/selectors.js`** - CSS selectors for finding HTML elements
- Groups by page section (login, nav, list, question, syllabus)
- All selectors manually discovered and tested
- Used everywhere to find elements on page
- ~60 lines with good comments

### Extractors (Asset Handling)
**`scraper/src/extractors/`** - Specialized extraction logic
- `figures.js` - Extract images, download, save metadata
- `tables.js` - Extract inline tables + modal tables (click → extract → close)
- `syllabus.js` - Navigate to related text, extract breadcrumbs, HTML body, assets

### Utilities (Output & Helpers)
**`scraper/src/utils/`** - Infrastructure
- `jsonWriter.js` - Append JSON lines to `data.jsonl`
- `fileSystem.js` - Download files, create directories, save assets
- `htmlParser.js` - Clean HTML, extract text with Cheerio

## How Data Flows

```
1. Click question button
   ↓
2. Wait for modal to appear
   ↓
3. Extract each field:
   - Text selectors: innerText() → string
   - Multiple items: .all() → map → array
   - HTML content: innerHTML() → extract text
   ↓
4. Download figures:
   - Find img elements
   - Download each from URL
   - Save to disk with metadata
   ↓
5. Extract tables:
   - Inline: Get <table> elements, save HTML
   - Modal: Click link → wait → extract → close
   ↓
6. Extract related text (optional):
   - Click "Related Text" link
   - Extract breadcrumbs
   - Extract HTML body
   - Download assets from related page
   - Go back
   ↓
7. Combine all into JSON object
   ↓
8. Append to data.jsonl (one line = one question)
   ↓
9. Close modal, repeat for next question
```

## Key Concepts

### Selectors
**What**: CSS patterns to find HTML elements
**Used by**: Playwright's `locator()` method
**Example**: `span[data-testid="greeting"]` finds `<span data-testid="greeting">`
**Updated in**: `scraper/src/selectors.js`
**Reference**: See `scraper/SELECTORS_REFERENCE.md`

### State Machine
**What**: Flow control pattern - discrete states with transitions
**Why**: Deterministic, easy to debug, good error recovery
**Pattern**: `execute() → returns nextState`
**Current states**: INIT, LOGIN, NAVIGATE, PROCESS_QUESTIONS, EXIT

### Headful vs Headless
**Headful**: Browser window visible (for manual login)
**Headless**: Browser runs in background (fast, no UI)
**Decision**: If `config/auth.json` exists → headless; else → headful

### Session Persistence
**What**: Storing login state so you don't have to log in again
**How**: Playwright's `context.storageState()` → save cookies/localStorage to JSON
**Where**: `scraper/config/auth.json` (auto-generated)
**When**: After first successful login

## Common Tasks for Agents

### "The scraper won't extract field X"
→ Check `scraper/src/selectors.js` for selector for field X
→ Check `scraper/src/states/process_questions.js` for extraction code
→ Check `scraper/SELECTORS_REFERENCE.md` for what selector should be

### "Selectors don't work anymore"
→ MKSAP HTML may have changed
→ Follow steps in `scraper/SELECTOR_DISCOVERY_GUIDE.md`
→ Update `scraper/src/selectors.js` with new selectors

### "Want to add a new field"
→ Find the HTML element in MKSAP by inspecting browser
→ Add selector to `scraper/src/selectors.js`
→ Add extraction code in `scraper/src/states/process_questions.js`
→ Add field to JSON schema in `scraper/src/extractors/*`

### "Want to change output format"
→ Modify `scraper/src/utils/jsonWriter.js` for JSONL changes
→ Or create new writer for different format
→ Update `process_questions.js` to use new writer

### "Browser automation is hanging"
→ Check if there's an infinite wait or wrong selector
→ Add timeout to relevant `waitFor*()` calls
→ Check logs: `tail -f scraper/logs/scraper.log`

## Data Flow Through Code

```
Question ID extraction:
  selectors.question.questionId = ".text-uppercase.text-nowrap"
         ↓
  process_questions.js: modal.locator(selector).innerText()
         ↓
  Returns: "CVMCQ24042"
         ↓
  Returns as: ID: "CVMCQ24042" in JSON

Multiple key points extraction:
  selectors.question.keyPoint = "ul.keypoints-list li"
         ↓
  process_questions.js: modal.locator(selector).all()
         ↓
  Returns: [element1, element2, element3]
         ↓
  Promise.all([element1.innerText(), ...])
         ↓
  Returns: ["Point A", "Point B", "Point C"]
         ↓
  Join with newline: "Point A\nPoint B\nPoint C"
         ↓
  Returns as: Key Point: "Point A\nPoint B\nPoint C" in JSON

Figure download:
  selectors.question.figures = "img[src*="d2chybfyz5ban.cloudfront.net"]"
         ↓
  extractors/figures.js: Get all img elements
         ↓
  For each image:
     - Get src attribute
     - Resolve relative URLs
     - Download via HTTPS
     - Save to output/QUESTIONID/figures/
     - Record metadata (original URL, path, alt text)
         ↓
  Returns: [{"originalSrc": "...", "itemPath": "figures/...", "alt": "..."}]
         ↓
  Returns as: Figures: [...] in JSON
```

## Configuration

**`scraper/config/default.js`**
- Base URL: `https://mksap.acponline.org`
- Headless: `true` (when authenticated)
- Auth file: `scraper/config/auth.json`
- Output dir: `scraper/output`

## Testing Approach

```
First run:
  1. npm start
  2. Browser opens
  3. Log in manually
  4. Check scraper/output/data.jsonl for first few questions
  5. Verify fields are populated
  6. Check assets downloaded to scraper/output/QUESTIONID/

Subsequent runs:
  1. npm start
  2. Check scraper/logs/scraper.log for progress
  3. Verify output continues to accumulate in data.jsonl
  4. Spot-check JSON validity: jq '.' scraper/output/data.jsonl
```

## Dependencies

**Production** (needed to run):
- `playwright` - Browser automation
- `cheerio` - HTML parsing
- `winston` - Logging

**Development**: None (no build/test dependencies)

**Remove if found**: `csv-writer`, `turndown` (scope was reduced to JSON-only)

## Debugging Tips

1. **Check logs**: `tail -f scraper/logs/scraper.log`
2. **Add console.log**: State machine logs everything with logger
3. **Check JSON validity**: `jq '.' scraper/output/data.jsonl | head`
4. **Check selectors**: Open DevTools in browser, inspect, verify selector finds element
5. **Check auth**: Look for `scraper/config/auth.json` (should exist after first run)
6. **Check output structure**: `head -1 scraper/output/data.jsonl | jq .`

## Code Style

- ✅ Async/await (not promises)
- ✅ Try-catch for errors
- ✅ JSDoc comments for modules
- ✅ Inline comments for complex logic
- ✅ Clear variable names
- ✅ One state per file
- ✅ Extractors are pure functions

## Documentation Map

```
For understanding:
  - README.md - What, why, project overview
  - QUICKSTART.md - How to run
  - CLAUDE_CODER_INSTRUCTIONS.md - Complete spec

For implementation details:
  - scraper/README.md - Usage & architecture
  - scraper/SELECTORS_REFERENCE.md - All selectors + their sources
  - scraper/SELECTOR_DISCOVERY_GUIDE.md - How to find/update selectors

For code:
  - scraper/src/selectors.js - All selectors (master file)
  - scraper/src/states/process_questions.js - Extraction logic
  - scraper/src/extractors/*.js - Asset handling

For data format:
  - READMEs/README_v7.md - MCQ markdown format (reference)
```

## Typical Agent Workflow

1. **Read**: `README.md` + `QUICKSTART.md` (5 min)
2. **Understand**: `CLAUDE_CODER_INSTRUCTIONS.md` (10 min)
3. **Explore**: `scraper/src/selectors.js` and `scraper/src/states/process_questions.js` (15 min)
4. **Modify**: Make changes to specific component
5. **Verify**: Run `npm start` and check output
6. **Document**: Update relevant documentation

## Questions to Answer Before Working

- [ ] Which state is the issue in? (INIT, LOGIN, NAVIGATE, PROCESS_QUESTIONS)
- [ ] Which field is missing or wrong? (See selectors.js)
- [ ] What's the error? (Check logs)
- [ ] Is it a selector issue? (Try in DevTools)
- [ ] Is it a logic issue? (Check extractors/)
- [ ] Is it a site change? (May need new selectors)

---

**Remember**: This is a deterministic system. State machine → selectors → extraction. Follow the data flow.
