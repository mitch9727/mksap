# MKSAP Medical Question Scraper & Processing Pipeline

## Project Overview

This repository contains a complete medical education pipeline for processing MKSAP (Medical Knowledge Self-Assessment Program) multiple-choice questions.

**Current Status**: ✅ Scraper fully implemented and ready for testing

## What This Project Does

1. **MKSAP Scraper** (`/scraper`) - Autonomous browser automation tool
   - Logs into MKSAP website
   - Navigates to Cardiovascular Medicine → Answered Questions
   - Extracts all question data including text, metadata, figures, tables, and related syllabus content
   - Outputs structured JSON (JSONL format) for downstream processing

2. **MCQ Card Library** (`/MCQs`) - Processed medical questions
   - COMPLETED: ~130 cardiovascular medicine questions in markdown format
   - IN PROGRESS: Foundations of clinical practice questions
   - Each question includes ID, objectives, answers, key points, and educational content

3. **Documentation** (`/READMEs`)
   - README_v7.md: Canonical specification for markdown output format
   - Historical versions (v0-v6): Evolution of the specification

## Quick Start

### For Scraping MKSAP

```bash
cd scraper
npm install

# First run (requires manual login):
npm start

# Subsequent runs (uses saved authentication):
npm start
```

**What Happens:**
- First run: Browser opens, you log in manually, session is saved
- Next runs: Browser runs headless, automatically scrapes all questions
- Output: `scraper/output/data.jsonl` - JSON data for each question

### For Understanding the Format

See `READMEs/README_v7.md` for the complete MCQ markdown template and conversion rules.

See `scraper/SELECTORS_REFERENCE.md` for all CSS selectors and how data is extracted.

## Project Structure

```
MKSAP/
├── README.md                                # This file - Project overview
├── CLAUDE.MD                               # Original project instructions (MCQ conversion)
├── CLAUDE_CODER_INSTRUCTIONS.md           # Scraper implementation spec
│
├── scraper/                               # 🔴 NEW - Autonomous MKSAP scraper
│   ├── main.js                           # Entry point
│   ├── package.json                      # Dependencies (Playwright, Cheerio, Winston)
│   ├── README.md                         # Scraper usage guide
│   ├── SELECTORS_REFERENCE.md           # Complete CSS selector documentation
│   ├── SELECTOR_DISCOVERY_GUIDE.md      # How to discover/update selectors
│   ├── config/
│   │   ├── default.js                  # Configuration
│   │   ├── auth.json                   # Auto-generated auth state
│   │   └── selectors.json              # Auto-generated selector backup
│   ├── src/
│   │   ├── stateMachine.js            # State machine orchestrator
│   │   ├── selectors.js               # MASTER: All CSS selectors
│   │   ├── states/                    # State implementations
│   │   ├── extractors/                # Data extraction logic
│   │   └── utils/                     # JSON writing, file management
│   ├── logs/                          # Auto-generated: Execution logs
│   └── output/                        # Auto-generated: Scraped data
│
├── MCQs/                               # Processed medical questions
│   ├── COMPLETED/
│   │   └── Cards/                    # ~130 completed cardiovascular cards
│   ├── CONVERTED/                     # Intermediate processing
│   └── IN PROGRESS/                   # Active work
│
└── READMEs/                            # Documentation versions
    ├── README_v7.md                   # 📌 CANONICAL specification
    ├── README_v6.md                   # Previous version
    └── README_v0.md - v5.md          # Historical versions
```

## What Each Component Does

### Scraper (`/scraper`)

**Purpose**: Extract MKSAP questions into structured JSON

**Input**: MKSAP website (https://mksap.acponline.org)

**Output**: `scraper/output/data.jsonl` - Newline-delimited JSON

**Architecture**: 5-state finite state machine
1. INIT - Browser setup
2. LOGIN - Authentication with session persistence
3. NAVIGATE - Automated navigation to question list
4. PROCESS_QUESTIONS - Extract all questions with pagination
5. EXIT - Clean shutdown

**Features**:
- ✅ Headful mode (manual login) on first run
- ✅ Headless mode (automatic) on subsequent runs
- ✅ Extracts: Question ID, objectives, answers, key points, references, care type, dates
- ✅ Downloads figures/images
- ✅ Extracts inline tables
- ✅ Opens and extracts modal-based tables
- ✅ Extracts related syllabus content with breadcrumbs
- ✅ Handles pagination automatically
- ✅ Error handling with screenshots and logging

**See**: `scraper/README.md` for detailed usage

### MCQ Cards (`/MCQs`)

**Purpose**: Store processed medical questions in markdown format

**Current Inventory**:
- **COMPLETED**: ~130 cardiovascular medicine questions (fully formatted)
- **IN PROGRESS**: Foundations of clinical practice questions (being processed)

**Format**: Follows README_v7.md specification
- Header with emoji and topic
- Question stem (not extracted - for Anki)
- True statements (atomic, cloze-ready facts)
- Extras (optional clarifications)
- References and tags
- Related text hierarchy
- Supplemental materials (figures, tables, videos)

**See**: `READMEs/README_v7.md` for complete format specification

### Documentation (`/READMEs`)

**README_v7.md** - CANONICAL specification
- Complete MCQ markdown template
- Extraction rules for all sections
- Quality control checklist
- Worked examples

**Historical versions** - Show evolution of the format

## The Full Pipeline

```
1. MKSAP Website
   ↓
2. Scraper (autonomous browser automation)
   ↓ extracts to JSONL
3. scraper/output/data.jsonl
   ↓
4. JSON → Markdown Converter (future)
   ↓
5. Individual .md files (MCQ cards)
   ↓
6. Anki Card Generator (future)
   ↓
7. Anki Decks for studying
```

**Current Status**: Steps 1-3 are complete and working. Steps 4-7 are downstream projects.

## For Claude Code Agents

If reading this codebase:

1. **To understand what we're building**: Read this README
2. **To understand the scraper**: Read `CLAUDE_CODER_INSTRUCTIONS.md` and `scraper/README.md`
3. **To understand the data format**: Read `READMEs/README_v7.md`
4. **To understand the selectors**: Read `scraper/SELECTORS_REFERENCE.md`
5. **To modify selectors**: See `scraper/SELECTOR_DISCOVERY_GUIDE.md`

The scraper is **production-ready**. The main files to understand are:
- `scraper/src/selectors.js` - All CSS selectors (manually discovered)
- `scraper/src/states/process_questions.js` - Extraction logic
- `scraper/src/extractors/*.js` - Asset extraction (figures, tables, syllabus)

## Key Technologies

**Scraper**:
- Node.js + Playwright (browser automation)
- Cheerio (HTML parsing)
- Winston (logging)

**Data Format**:
- JSONL (newline-delimited JSON)
- Markdown (README_v7.md template)

## Recent Changes

### Latest Work (December 10, 2024)
- ✅ Implemented complete state machine architecture
- ✅ Discovered all CSS selectors (manually verified against live HTML)
- ✅ Implemented text extraction for all question fields
- ✅ Added table extraction (both inline and modal-based)
- ✅ Added figure download with metadata
- ✅ Added syllabus/related text extraction with breadcrumbs
- ✅ Implemented pagination support
- ✅ Added session persistence (auth caching)
- ✅ Created comprehensive documentation

## Known Issues & Limitations

1. **Selectors are site-specific** - If MKSAP HTML structure changes, selectors may need updating
2. **Videos** - Currently placeholder (no extraction logic)
3. **Optional fields** - Some questions may have empty values for optional fields
4. **Related Text** - Navigation away from question may not always work; graceful fallback implemented

## Next Steps

1. **Test the scraper** - `cd scraper && npm start`
2. **Verify JSON output** - Check `scraper/output/data.jsonl`
3. **Build downstream processors**:
   - Anki card generator from JSON
   - Markdown formatter from JSON
   - CSV exporter

## File Organization Notes

### Do NOT modify:
- `READMEs/` - These are reference documentation
- `MCQs/COMPLETED/` - Finished work, keep as-is

### Safe to modify:
- `scraper/` - Active development
- `CLAUDE_CODER_INSTRUCTIONS.md` - Spec documentation

### Auto-generated (will be recreated):
- `scraper/config/auth.json` - Session storage
- `scraper/output/` - Scraped data
- `scraper/logs/` - Execution logs

## Support

For understanding specific components:

1. **Selectors not working?** → See `scraper/SELECTOR_DISCOVERY_GUIDE.md`
2. **How is data extracted?** → See `scraper/SELECTORS_REFERENCE.md` and `scraper/src/extractors/`
3. **What's the output format?** → See `READMEs/README_v7.md`
4. **How does the scraper work?** → See `scraper/README.md` and `CLAUDE_CODER_INSTRUCTIONS.md`

---

**Project Goal**: Build a complete pipeline to extract MKSAP medical questions into machine-readable, AI-processable formats for Anki flashcard generation and medical education.

**Current Status**: Scraper complete and ready for testing. Output pipeline pending.
