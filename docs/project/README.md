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
├── docs/                                 # Complete project documentation
│   ├── project/                         # Project-level documentation
│   │   ├── README.md                   # This file - Project overview
│   │   ├── QUICKSTART.md              # Getting started guide
│   │   ├── INDEX.md                   # Documentation navigator
│   │   └── PROJECT_STATUS.md          # Current project status
│   │
│   ├── architecture/                    # Architecture and design documentation
│   │   ├── CODEBASE_GUIDE.md          # How to understand the code
│   │   ├── PROJECT_ORGANIZATION.md    # Project structure documentation
│   │   ├── AI_INTEGRATION.md          # AI features architecture
│   │   └── CLAUDE_CODE_SETUP.md       # Claude Code integration guide
│   │
│   ├── scraper/                        # Scraper-specific documentation
│   │   ├── README.md                  # Scraper usage guide
│   │   ├── TECHNICAL_SPEC.md          # Complete technical specification
│   │   ├── AI_FEATURES.md             # AI integration complete documentation
│   │   ├── SELECTORS_REFERENCE.md     # All CSS selectors documentation
│   │   └── SELECTOR_DISCOVERY.md      # How to discover/update selectors
│   │
│   ├── specifications/                  # Format specifications
│   │   └── MCQ_FORMAT.md              # MCQ markdown format specification
│   │
│   ├── examples/                        # Example files
│   │   └── CVMCQ24041.md              # Example MCQ card
│   │
│   └── legacy/                          # Archived documentation
│       └── CLAUDE_MCQ_FORMAT.md        # Historical MCQ format
│
├── .claude/                              # Claude Code integration & automation
│   ├── README.md                        # Agent navigation guide
│   ├── settings.local.json             # Claude Code permissions
│   ├── .env.example                    # Environment variables template
│   │
│   ├── commands/                        # Slash commands for automation
│   │   ├── validate-structure.md       # Validate project structure
│   │   ├── organize-codebase.md        # Auto-organize files
│   │   ├── update-docs.md              # Auto-update documentation
│   │   ├── sync-imports.md             # Fix broken imports
│   │   └── README.md                   # Commands documentation
│   │
│   ├── skills/                          # Claude Agent SDK skills
│   │   ├── codebase-organizer/         # AI-powered organization skill
│   │   └── doc-validator/              # Documentation validation skill
│   │
│   └── templates/                       # Templates for consistency
│       ├── slash-command.md            # Template for new commands
│       ├── skill.json                  # Template for new skills
│       └── documentation.md            # Template for new docs
│
├── scraper/                             # Autonomous MKSAP scraper
│   ├── src/
│   │   ├── SystemScraper.js           # Main scraper orchestrator
│   │   ├── WorkerPool.js              # Multi-system concurrent scraping
│   │   ├── selectors.js               # MASTER: All CSS selectors
│   │   ├── states/                    # Scraper state handlers
│   │   ├── skills/                    # AI-powered scraper skills
│   │   ├── agents/                    # Intelligent agents
│   │   ├── ai/                        # AI client and utilities
│   │   └── utils/                     # Utilities
│   │
│   ├── config/
│   │   ├── ai_config.js               # AI configuration hub
│   │   ├── auth.json                  # Auto-generated auth state
│   │   └── selectors.json             # Auto-generated selector backup
│   │
│   ├── output/                        # Auto-generated: Scraped data
│   ├── logs/                          # Auto-generated: Execution logs
│   ├── package.json                   # Dependencies
│   └── README.md                      # Scraper usage guide
│
└── MCQs/                              # Processed medical questions (legacy)
    ├── COMPLETED/
    ├── CONVERTED/
    └── IN PROGRESS/
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

## Claude Code Organization

The project includes automated tooling through Claude Code integration for maintaining project structure and documentation quality.

### Available Commands (Slash Commands)

Run these commands in Claude Code to maintain the project:

- **`/validate-structure`** - Check if the codebase follows organization rules
  - Validates file placement
  - Checks documentation links
  - Verifies import paths
  - Reports any violations

- **`/organize-codebase`** - Auto-organize files according to rules
  - Dry-run mode (preview changes)
  - Auto-moves misplaced files
  - Updates all cross-references
  - Fixes relative paths

- **`/update-docs`** - Update and fix documentation
  - Validates all links
  - Fixes broken references
  - Regenerates INDEX.md
  - Updates navigation

- **`/sync-imports`** - Fix broken import paths
  - Scans for broken imports
  - Updates paths after file moves
  - Handles both ES6 and CommonJS

**See**: [.claude/commands/README.md](../../.claude/commands/README.md) for detailed usage

### Claude Agent SDK Skills

AI-powered skills for intelligent operations:

- **`codebase-organizer`** - Analyze and suggest file organization improvements
- **`doc-validator`** - Validate documentation quality and completeness

**See**: [.claude/skills/](../../.claude/skills/) for implementation details

### Configuration Files

- **[.claude/organization-rules.json](../../.claude/organization-rules.json)** - Defines file organization rules and naming conventions
- **[.claude/doc-standards.json](../../.claude/doc-standards.json)** - Documentation quality standards
- **[.claude/.env.example](../../.claude/.env.example)** - Environment variable template

### Templates

Templates for creating new project artifacts:

- **[.claude/templates/slash-command.md](../../.claude/templates/slash-command.md)** - New command template
- **[.claude/templates/skill.json](../../.claude/templates/skill.json)** - New skill template
- **[.claude/templates/documentation.md](../../.claude/templates/documentation.md)** - New doc template

---

## For Claude Code Agents

If reading this codebase:

1. **To understand what we're building**: Read this README
2. **To understand the scraper**: Read [docs/scraper/TECHNICAL_SPEC.md](../scraper/TECHNICAL_SPEC.md) and [docs/scraper/README.md](../scraper/README.md)
3. **To understand the data format**: Read [docs/specifications/MCQ_FORMAT.md](../specifications/MCQ_FORMAT.md)
4. **To understand the selectors**: Read [docs/scraper/SELECTORS_REFERENCE.md](../scraper/SELECTORS_REFERENCE.md)
5. **To modify selectors**: See [docs/scraper/SELECTOR_DISCOVERY.md](../scraper/SELECTOR_DISCOVERY.md)
6. **To understand AI features**: Read [docs/architecture/AI_INTEGRATION.md](../architecture/AI_INTEGRATION.md)
7. **To understand project structure**: Run `/validate-structure` to check organization

The scraper is **production-ready**. The main files to understand are:
- `scraper/src/selectors.js` - All CSS selectors (manually discovered)
- `scraper/src/states/process_questions.js` - Extraction logic
- `scraper/src/ai/claudeCodeClient.js` - AI integration

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
