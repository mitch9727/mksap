# MKSAP Project - Claude Code Guide

## Project Overview

This is a medical education project for processing MKSAP (Medical Knowledge Self-Assessment Program) multiple-choice questions into structured, machine-readable markdown files optimized for Anki flashcard generation.

**Current working directory:** `/Users/Mitchell/coding/projects/MKSAP`

## Project Structure

```
MKSAP/
├── MCQs/                    # Medical multiple-choice questions
│   ├── COMPLETED/          # Finished MCQ cards
│   │   └── Cards/          # Individual markdown files (e.g., CVMCQ24042.md)
│   ├── IN PROGRESS/        # Cards currently being worked on
│   └── CONVERTED/          # Intermediate files
├── READMEs/                # Project documentation
│   └── README.md           # Current canonical specification
├── scraper/                # Headless MKSAP Scraper
│   ├── src/                # Scraper source code
│   ├── config/             # Configuration & Auth
│   ├── output/             # JSON & Asset Output
│   └── README.md           # Scraper instructions
└── CLAUDE.MD               # This file
```

## Key Workflows

### 1. MCQ Card Generation

**Purpose:** Transform raw MCQ explanations into standardized, Anki-ready markdown files.

**Input:** MCQ text with:
- Answer & Critique section
- Related Text section
- Optional supplemental materials (figures, videos, tables)

**Output:** Structured `.md` file following the template in `READMEs/README_v7.md`

**File naming:** Exact Question ID (e.g., `CVMCQ24042.md`)

**Key requirements:**
- Follow the **exact** canonical template from README_v7.md
- Extract True Statements as atomic, cloze-ready facts
- Number Extra(s) by parent True Statement index (not sequentially)
- Expand abbreviations on first use
- Bold key clinical terms once per section
- Convert table images to faithful HTML
- Preserve all supplemental materials (figures, videos, tables)

### 2. Content Extraction Rules

**True Statements:**
- Extract ONLY directly stated facts
- Each must stand alone
- Keep numbers/thresholds verbatim
- Make atomic (one idea per statement)
- Cloze-ready phrasing

**Extra(s):**
- Optional clarifications only
- Numbered by parent True Statement (e.g., 1., 4., not 1., 2., 3.)
- Keep patient-specific details here, not in True Statements

**System Emojis:**
- 🫀 Cardiovascular medicine
- 🦋 Endocrinology and metabolism
- 🩺 Foundations of clinical practice
- 🤒 Common symptoms
- 🍽️ Gastroenterology and Hepatology
- 🩸 Hematology
- 🦠 Infectious disease
- 🩹 Interdisciplinary medicine and dermatology
- 💧 Nephrology
- 🧠 Neurology
- 🎗️ Oncology
- 🫁 Pulmonary and critical care medicine
- 🦴 Rheumatology

### 3. Quality Control Checklist

Before completing any MCQ card generation:

1. ✅ Filename equals Question ID
2. ✅ Title format: `### [EMOJI] [System]: [Key Concept]`
3. ✅ Correct section order maintained
4. ✅ Exactly one blank line between sections
5. ✅ Horizontal rules placed correctly (3 total)
6. ✅ Extra(s) numbered by parent True Statement
7. ✅ Related Text shows hierarchy only (not full body)
8. ✅ All three supplemental headings present
9. ✅ Tables converted to valid HTML
10. ✅ Each table followed by derived True Statements
11. ✅ Abbreviations expanded on first use
12. ✅ Key terms bolded once per block
13. ✅ True Statements are atomic and cloze-ready
14. ✅ Tags present for Main and Related blocks
15. ✅ Last Updated matches parsed month/year

## Important Guidelines

### Strict Template Adherence
- **Never** reorder sections
- **Never** drop required headings
- **Always** keep exactly one blank line between sections
- Use horizontal rules (`---`) at the three specified boundaries

### Content Extraction Philosophy
- **Verbatim-leaning:** Stay maximally faithful to source wording
- **No inference:** Extract only explicitly stated facts
- **Atomic statements:** One testable idea per True Statement
- **Discriminative cues:** Include features that differentiate similar entities
- **Precision with numbers:** Keep thresholds verbatim with units

### Common Pitfalls to Avoid
- ❌ Numbering Extras sequentially (1, 2, 3) instead of by parent index
- ❌ Pasting full Related Text body (only include title line)
- ❌ Summarizing tables in prose (must provide HTML + derived statements)
- ❌ Moving Reference/Tags to bottom (keep immediately after Extra(s))
- ❌ Missing horizontal rules or extra blank lines
- ❌ Creating multi-clause True Statements (split into atomic facts)

## Documentation

**Primary specification:** `READMEs/README.md`

This file contains:
- Complete canonical template
- Input parsing rules
- Output formatting requirements
- Flashcard optimization principles
- Quality control checklist
- Worked examples

**Version history:** Consolidated from earlier versions (v0-v7).

## Technical Context

### Browser Application
- **Purpose:** Electron-based browser for viewing/testing MCQ cards
- **Technology:** Electron with webview
- **Entry point:** `my-browser/main.js`
- **UI:** `my-browser/index.html` and `my-browser/renderer.js`

### File Processing
- MCQs progress through: IN PROGRESS → CONVERTED → COMPLETED
- Each completed card is a standalone markdown file
- Files are machine-parsable for CSV/Anki import

## When Working on This Project

1. **Always reference README_v7.md** for the canonical specification
2. **Use TodoWrite** for multi-step MCQ processing tasks
3. **Validate output** against the quality control checklist
4. **Preserve formatting** exactly as specified
5. **Test HTML** if generating tables or figures
6. **Check file naming** matches Question ID

## Repository Status

- **Git initialized:** Yes
- **Current branch:** master
- **No remote configured** (main branch field empty)
- **Untracked directories:** MCQs/, READMEs/, my-browser/

## Notes for AI Assistance

- This project requires **high precision** in formatting
- Medical content must be **factually preserved** (no paraphrasing clinical facts)
- Template compliance is **non-negotiable** for downstream parsing
- Quality over speed - each card must pass all checklist items
- When generating MCQ cards, work through the README_v7.md specification step by step
