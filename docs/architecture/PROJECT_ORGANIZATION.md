# MKSAP Project Organization

**Last Updated:** December 10, 2024

## Overview

This project is organized into clear phases, with Phase I (Web Scraping) fully implemented and self-contained in the `scraper/` directory.

## Directory Structure

```
MKSAP/
│
├── CLAUDE.MD                        # Project instructions for Claude Code (convention)
├── .gitignore                       # Git ignore patterns
│
├── scraper/                         # 🎯 PHASE I: Web Scraping (COMPLETE)
│   ├── main.js                      # Entry point - Worker pool orchestrator
│   ├── package.json                 # Dependencies & scripts
│   │
│   ├── config/
│   │   ├── systems.js               # All 12 medical system definitions
│   │   └── auth.json                # (Auto-generated after first login)
│   │
│   ├── src/
│   │   ├── WorkerPool.js            # Parallel execution manager (2 workers)
│   │   ├── SystemScraper.js         # System-aware state machine
│   │   ├── selectors.js             # CSS selectors for all page elements
│   │   ├── stateMachine.js          # (Legacy - can be archived)
│   │   │
│   │   ├── states/                  # State machine implementations
│   │   │   ├── base.js              # Base state class
│   │   │   ├── init.js              # Browser context creation
│   │   │   ├── login.js             # Authentication handling
│   │   │   ├── navigate.js          # Multi-system navigation
│   │   │   └── process_questions.js # Question extraction loop
│   │   │
│   │   ├── extractors/              # Asset extraction modules
│   │   │   ├── figures.js           # Image download & naming
│   │   │   ├── tables.js            # HTML table extraction
│   │   │   └── syllabus.js          # Related text extraction
│   │   │
│   │   └── utils/                   # Utility functions
│   │       ├── assetNaming.js       # Meaningful asset name extraction
│   │       ├── fileSystem.js        # File operations
│   │       ├── htmlParser.js        # HTML text extraction
│   │       ├── jsonWriter.js        # (Legacy JSONL writer)
│   │       └── questionWriter.js    # Per-question JSON writer
│   │
│   ├── output/                      # 📦 Generated output (gitignored)
│   │   ├── Cardiovascular/
│   │   │   ├── CVMCQ24001/
│   │   │   │   ├── CVMCQ24001.json
│   │   │   │   ├── ECG_Figure.png
│   │   │   │   └── Treatment_Table.html
│   │   │   └── ...
│   │   ├── Pulmonary/
│   │   └── ... (11 more systems)
│   │
│   └── logs/                        # 📋 Execution logs (gitignored)
│       ├── pool.log                 # Worker pool logs
│       ├── cv.log                   # System-specific logs
│       └── ...
│
├── docs/                            # 📚 PROJECT DOCUMENTATION
│   ├── README.md                    # Project overview & purpose
│   ├── QUICKSTART.md                # Getting started guide
│   ├── CLAUDE_CODER_INSTRUCTIONS.md # Complete specification
│   ├── CODEBASE_GUIDE.md            # Architecture & implementation guide
│   ├── PROJECT_STATUS.md            # Current status & completed work
│   ├── INDEX.md                     # Documentation index
│   ├── PROJECT_ORGANIZATION.md      # This file
│   │
│   └── phase2_phase3/               # 🔮 Future phases reference
│       └── MCQ_SPECIFICATION.md     # MCQ card format (for Phase II/III)
│
├── examples/                        # 📄 Example files
│   └── CVMCQ24041.md                # Sample MCQ card
│
├── .claude/                         # Claude Code configuration
└── .git/                            # Git repository

```

## Phase Breakdown

### ✅ Phase I: Web Scraping (COMPLETE)
**Location:** `scraper/`
**Status:** Fully implemented and ready for testing
**Purpose:** Extract ~2000+ medical questions from MKSAP website to JSON

**Key Features:**
- Multi-system support (12 medical systems)
- Parallel execution (2 concurrent workers)
- Meaningful asset naming
- Per-question JSON files with all assets
- Session persistence

**Usage:**
```bash
cd scraper
npm start              # Scrape all 12 systems
node main.js cv en    # Scrape specific systems
```

**Output:**
- Individual JSON files per question
- Downloaded figures (meaningful names from browser)
- Extracted tables (HTML files with meaningful names)
- Related text content
- All organized by system → question ID

### 🔮 Phase II: Processing (NOT STARTED)
**Purpose:** Convert raw "Answer & Critique" text to structured "True Statements"
**Status:** Future work
**Reference:** See `docs/phase2_phase3/MCQ_SPECIFICATION.md`

### 🔮 Phase III: Export (NOT STARTED)
**Purpose:** Export to CSV, SQL database, or other formats
**Status:** Future work

## Key Design Decisions

### Why `scraper/` is self-contained:
- Phase I is complete and independent
- Can be run without touching other phases
- Clear separation of concerns
- Easy to archive or reference later

### Why documentation is centralized in `docs/`:
- Single source of truth for project information
- Easier to navigate than scattered files
- Clear distinction between project docs and code

### Why future phases are in `docs/phase2_phase3/`:
- Keeps reference material accessible
- Doesn't clutter the root or active code
- Easy to move to active development when needed

## File Naming Conventions

### Documentation Files:
- `README.md` - Overview/introduction to a module or section
- `GUIDE.md` - Step-by-step instructions or tutorials
- `REFERENCE.md` - Detailed API or specification reference
- `STATUS.md` - Current state and progress tracking

### Code Files:
- `PascalCase.js` - Classes (WorkerPool, SystemScraper)
- `camelCase.js` - Utilities and modules (assetNaming, questionWriter)
- `lowercase.js` - Entry points (main.js)

## Git Workflow

### What's tracked:
- All source code (`scraper/src/`, `scraper/config/systems.js`)
- Documentation (`docs/`, `CLAUDE.MD`)
- Configuration (`package.json`, `.gitignore`)

### What's ignored:
- `scraper/output/` - Generated data (too large, user-specific)
- `scraper/logs/` - Execution logs (temporary, user-specific)
- `scraper/config/auth.json` - Authentication (sensitive)
- `node_modules/` - Dependencies (installed via npm)

## Navigation Guide

### "I want to run the scraper"
→ `docs/QUICKSTART.md`

### "I want to understand how it works"
→ `docs/CODEBASE_GUIDE.md`

### "I want to modify selectors"
→ `scraper/src/selectors.js` + `scraper/SELECTORS_REFERENCE.md` (if exists)

### "I want to add a new system"
→ `scraper/config/systems.js`

### "I want to change output format"
→ `scraper/src/utils/questionWriter.js`

### "I want to see MCQ card format"
→ `docs/phase2_phase3/MCQ_SPECIFICATION.md` + `examples/CVMCQ24041.md`

## Maintenance Notes

### Archive candidates (once tested):
- `scraper/src/stateMachine.js` - Replaced by `SystemScraper.js`
- `scraper/src/utils/jsonWriter.js` - Replaced by `questionWriter.js`

### Future additions:
- `scraper/tests/` - Unit and integration tests
- `scraper/docs/` - Scraper-specific documentation (if it grows)
- `phase2/` - When Phase II begins development
- `phase3/` - When Phase III begins development

---

**Note:** This organization was finalized on December 10, 2024, after completing all Phase I implementation tasks.
