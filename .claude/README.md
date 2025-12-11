# Claude Code Integration

This project is designed to be understood and modified by Claude Code agents.

## Quick Links

**Start here**: `/README.md` - Project overview

**For getting started**: `/QUICKSTART.md`

**For understanding everything**: `/CLAUDE_CODER_INSTRUCTIONS.md`

**For understanding the codebase**: `/CODEBASE_GUIDE.md`

**For current status**: `/PROJECT_STATUS.md`

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

1. Start with `/README.md`
2. Then `/CODEBASE_GUIDE.md` (your roadmap)
3. Then look at code in order:
   - `scraper/main.js` (entry)
   - `scraper/src/stateMachine.js` (orchestrator)
   - `scraper/src/states/` (implementations)
   - `scraper/src/selectors.js` (configurations)

## Project Status

✅ **FULLY IMPLEMENTED** - Ready to test

See `/PROJECT_STATUS.md` for complete status.

## Quick Start

```bash
cd scraper
npm install
npm start
```

## All Documentation Files

```
Root level:
├── README.md                    # Start here
├── QUICKSTART.md               # How to run
├── CODEBASE_GUIDE.md          # How to understand code
├── CLAUDE_CODER_INSTRUCTIONS.md # Complete spec
└── PROJECT_STATUS.md           # What's done

Scraper:
├── scraper/README.md           # Usage guide
├── scraper/SELECTORS_REFERENCE.md # All selectors explained
└── scraper/SELECTOR_DISCOVERY_GUIDE.md # How to update selectors

Reference:
└── READMEs/README_v7.md        # MCQ format spec
```

## Need Help?

| Question | Answer |
|----------|--------|
| How does scraper work? | `CLAUDE_CODER_INSTRUCTIONS.md` |
| How do I use it? | `QUICKSTART.md` |
| How do I understand the code? | `CODEBASE_GUIDE.md` |
| What's the CSS selector for X? | `scraper/SELECTORS_REFERENCE.md` |
| How do I update selectors? | `scraper/SELECTOR_DISCOVERY_GUIDE.md` |
| What's the output format? | `scraper/output/data.jsonl` |
| What's the MCQ markdown format? | `READMEs/README_v7.md` |

## For Next Agents

This project is **production-ready**. The main components are:

1. **State Machine** - Clean, deterministic flow
2. **Selectors** - Manually discovered, documented, verified
3. **Extractors** - Handle figures, tables, related text
4. **Output** - JSONL format, one JSON per question

Everything is documented. Start with `/CODEBASE_GUIDE.md` then read the code in order.

**No secrets. No hidden knowledge. Everything is in the docs.**
