# Claude Code Integration

This project is designed to be understood and modified by Claude Code agents.

## Quick Links

**Start here**: `/docs/project/README.md` - Project overview

**For getting started**: `/docs/project/QUICKSTART.md`

**For understanding everything**: `/docs/scraper/TECHNICAL_SPEC.md`

**For understanding the codebase**: `/docs/architecture/CODEBASE_GUIDE.md`

**For current status**: `/docs/project/PROJECT_STATUS.md`

## What You Need to Know

This project automates extraction of MKSAP medical questions into JSON.

**State Machine Architecture** (easiest to understand):
1. INIT - Start browser
2. LOGIN - Authenticate
3. NAVIGATE - Go to questions
4. PROCESS_QUESTIONS - Extract each question
5. EXIT - Clean up

**Key Files**:
- `scraper/src/selectors.js` - ALL selectors (CSS patterns to find elements)
- `scraper/src/states/process_questions.js` - Extraction logic
- `scraper/src/extractors/` - Figure/table/syllabus extraction

**Output**: `scraper/output/data.jsonl` - One JSON per line

## For Agents Reading This

1. Start with `/docs/project/README.md`
2. Then `/docs/architecture/CODEBASE_GUIDE.md` (your roadmap)
3. Then look at code in order:
   - `scraper/main.js` (entry)
   - `scraper/src/WorkerPool.js` (orchestrator)
   - `scraper/src/states/` (implementations)
   - `scraper/src/selectors.js` (configurations)

## Project Status

✅ **FULLY IMPLEMENTED** - Ready to test

See `/docs/project/PROJECT_STATUS.md` for complete status.

## Quick Start

```bash
cd scraper
npm install
npm start
```

## All Documentation Files

```
docs/
├── project/
│   ├── README.md                # Start here
│   ├── QUICKSTART.md            # How to run
│   ├── INDEX.md                 # Documentation navigator
│   └── PROJECT_STATUS.md        # What's done
├── architecture/
│   ├── CODEBASE_GUIDE.md       # How to understand code
│   └── PROJECT_ORGANIZATION.md # Project structure
├── scraper/
│   ├── README.md                # Usage guide
│   ├── TECHNICAL_SPEC.md        # Complete spec
│   ├── AI_FEATURES.md           # AI integration
│   ├── CLAUDE_CODE_SETUP.md     # Claude Code setup
│   ├── SELECTORS_REFERENCE.md   # All selectors
│   └── SELECTOR_DISCOVERY.md    # How to update selectors
├── specifications/
│   └── MCQ_FORMAT.md            # MCQ format spec
├── examples/
│   └── CVMCQ24041.md            # Example MCQ card
└── legacy/
    └── CLAUDE_MCQ_FORMAT.md     # Legacy MCQ format
```

## Need Help?

| Question | Answer |
|----------|--------|
| Where do I start? | `/docs/project/README.md` |
| How does scraper work? | `/docs/scraper/TECHNICAL_SPEC.md` |
| How do I use it? | `/docs/project/QUICKSTART.md` |
| How do I understand the code? | `/docs/architecture/CODEBASE_GUIDE.md` |
| What's the CSS selector for X? | `/docs/scraper/SELECTORS_REFERENCE.md` |
| How do I update selectors? | `/docs/scraper/SELECTOR_DISCOVERY.md` |
| What's the output format? | `/docs/specifications/MCQ_FORMAT.md` |
| How are Claude commands organized? | `/docs/project/README.md` (see .claude/ section) |

## For Next Agents

This project is **production-ready**. The main components are:

1. **State Machine** - Clean, deterministic flow
2. **Selectors** - Manually discovered, documented, verified
3. **Extractors** - Handle figures, tables, related text
4. **Output** - JSONL format, one JSON per question

Everything is documented. Start with `/docs/architecture/CODEBASE_GUIDE.md` then read the code in order.

## Claude Code Organization

All Claude-specific files are organized in `.claude/`:

- **Commands**: `.claude/commands/` - Slash commands for automation
- **Skills**: `.claude/skills/` - AI-powered skills for intelligent operations
- **Templates**: `.claude/templates/` - Templates for consistency
- **Configuration**: `.claude/organization-rules.json`, `.claude/doc-standards.json`

See `.claude/commands/README.md` for command documentation.

**No secrets. No hidden knowledge. Everything is in the docs.**
