# MKSAP Project - Master Todo List

**Last Updated:** December 25, 2025
**Current Phase:** Phase 1 (Data Extraction)
**Overall Progress:** 0% (Starting Phase 1 execution)

---

## Legend

- ⬜ Pending (not started)
- 🟨 In Progress (actively working)
- 🟩 Completed (finished, verified)
- 🔴 Blocked (waiting on something)
- ⚠️ At Risk (may require revision)

---

## PHASE 1: Data Extraction - Complete Question Bank (2,233 questions)

**Phase Goal:** Extract all 2,233 MKSAP questions across 16 systems and 6 question types.

**Detailed Roadmap:** See [PHASE_1_PLAN.md](PHASE_1_PLAN.md)

### Task 1: Finalize Question Count & Discovery Algorithm
- **Status:** ⬜ Pending
- **Details:** Confirm 2,233 total questions (16 systems × 6 question types)
- **Sub-tasks:**
  - ⬜ Read Question ID Discovery.md completely
  - ⬜ Test API metadata endpoint (`/api/content_metadata.json`)
  - ⬜ Execute discovery against live API
  - ⬜ Document final counts per system
  - ⬜ Create PHASE_1_DISCOVERY_RESULTS.md
- **Success Criteria:** Question count verified and documented as 2,233

### Task 2: Update Configuration with Accurate Counts
- **Status:** ⬜ Pending
- **Details:** Update text_extractor/src/config.rs with all 16 systems and accurate targets
- **Sub-tasks:**
  - ⬜ Open config.rs
  - ⬜ Update ORGAN_SYSTEMS array (16 systems, all question types)
  - ⬜ Test compilation
  - ⬜ Verify question ID generation
- **Success Criteria:** config.rs compiles, targets 2,233 questions total

### Task 3: Verify Question Type Support in Extractor
- **Status:** ⬜ Pending
- **Details:** Ensure extractor supports all 6 question types (cor, mcq, qqq, mqq, vdx, sq)
- **Sub-tasks:**
  - ⬜ Review extractor.rs for question type handling
  - ⬜ Test each question type via API (6 manual tests)
  - ⬜ Update logic if needed for all types
  - ⬜ Document QUESTION_TYPES_SUPPORT.md
- **Success Criteria:** All 6 question types can be extracted

### Task 4: Complete Question Extraction (All 2,233)
- **Status:** ⬜ Pending
- **Details:** Run extractor to extract all 2,233 questions from MKSAP API
- **Sub-tasks:**
  - ⬜ Prepare environment (MKSAP_SESSION cookie)
  - ⬜ Start extraction (./target/release/mksap-extractor)
  - ⬜ Wait for completion (~30+ hours due to rate limiting)
  - ⬜ Monitor progress using checkpoint files
- **Success Criteria:** All 2,233 questions in mksap_data/ with minimal failures (<10)
- **Estimated Duration:** 2-4 weeks (24-30+ hours of actual processing)

### Task 5: Monitor Extraction Progress & Handle Issues
- **Status:** ⬜ Pending (Concurrent with Task 4)
- **Details:** Active monitoring of extraction, session management, error handling
- **Sub-tasks:**
  - ⬜ Set up progress monitoring (watch script)
  - ⬜ Handle session expiration (restart with new cookie)
  - ⬜ Handle rate limiting (automatic backoff active)
  - ⬜ Document issues in PHASE_1_EXTRACTION_LOG.md
  - ⬜ Update DESERIALIZATION_ISSUES.md if new patterns found
- **Success Criteria:** Extraction completes with all issues documented

### Task 6: Validate All Extracted Questions
- **Status:** ⬜ Pending
- **Details:** Run built-in validator on all 2,233 extracted questions
- **Sub-tasks:**
  - ⬜ Run: ./target/release/mksap-extractor validate
  - ⬜ Review validation_report.txt
  - ⬜ Check for missing 'critique' fields (critical for Phase 2)
  - ⬜ Spot-check 20 random questions across systems
  - ⬜ Create PHASE_1_VALIDATION_REPORT.md
- **Success Criteria:** Validation shows 100% pass rate, 2,233 questions have 'critique' fields

### Task 7: Verify Media Files Downloaded
- **Status:** ⬜ Pending
- **Details:** Ensure all referenced media (images, videos, SVGs, tables) downloaded
- **Sub-tasks:**
  - ⬜ Count total media files (expected 1000s)
  - ⬜ Verify file integrity (spot-check JPEGs, PNGs, SVGs)
  - ⬜ Check organization in figures/ subdirectories
  - ⬜ Audit for missing media
  - ⬜ Create PHASE_1_MEDIA_AUDIT.md
- **Success Criteria:** All referenced media files present and verified

### Task 8: Audit Deserialization Issues
- **Status:** ⬜ Pending
- **Details:** Identify and document any JSON inconsistencies or API response variations
- **Sub-tasks:**
  - ⬜ Review existing DESERIALIZATION_ISSUES.md
  - ⬜ Scan 50 random questions for type variations
  - ⬜ Check if models.rs handles variations correctly
  - ⬜ Document any new patterns in DESERIALIZATION_ISSUES.md
- **Success Criteria:** All JSONs parse cleanly, no critical deserialization blockers

### Task 9: Extract Syllabus Breadcrumb References
- **Status:** ⬜ Pending
- **Details:** Add `related_syllabus_refs` field to each question JSON with breadcrumbs
- **Sub-tasks:**
  - ⬜ Understand current syllabus reference structure
  - ⬜ Design breadcrumb extraction logic
  - ⬜ Implement extraction (Rust or Python script)
  - ⬜ Test on sample questions
  - ⬜ Process all 2,233 questions
  - ⬜ Document in SYLLABUS_BREADCRUMB_MAPPING.md
- **Success Criteria:** All 2,233 questions have `related_syllabus_refs` field with syllabus sections

### Task 10: Final Phase 1 Completion Report
- **Status:** ⬜ Pending
- **Details:** Verify all Phase 1 goals met, generate completion report, prepare for Phase 2
- **Sub-tasks:**
  - ⬜ Verify all 9 tasks completed
  - ⬜ Generate statistics (question count, media files, storage used)
  - ⬜ Create PHASE_1_COMPLETION_REPORT.md
  - ⬜ Create Phase 2 prerequisites checklist
  - ⬜ Backup mksap_data/ directory
  - ⬜ Document lessons learned
- **Success Criteria:** Phase 1 complete, all 2,233 questions extracted with validation report, ready for Phase 2

---

## PHASE 2: Intelligent Fact Extraction (Pending - After Phase 1)

**Phase Goal:** Extract atomic medical facts from question critiques using Claude LLM.

**Status:** ⬜ Planning (Will create PHASE_2_PLAN.md after Phase 1 completes)

**High-Level Tasks:**
1. Design LLM prompt for fact extraction
2. Create Claude Code skill for batch processing
3. Implement JSON schema validation
4. Process all 2,233 questions (one isolated LLM call per question)
5. Generate facts_backup_raw.jsonl (6,000-7,000 facts)
6. QA sampling and prompt refinement

---

## PHASE 3: Anki Card Generation (Pending - After Phase 2)

**Phase Goal:** Convert extracted facts into Anki-ready cards with cloze deletions and media.

**Status:** ⬜ Planning (Will create PHASE_3_PLAN.md after Phase 2 completes)

**High-Level Tasks:**
1. Design Anki note schema
2. Build Rust module: Cloze generation
3. Build Rust module: Media association
4. Build Rust module: HTML table extraction
5. Build Rust module: Card assembly
6. Build Rust module: JSON iterator
7. Generate anki_notes.jsonl (6,000-7,000 cards)

---

## PHASE 4: Import & Validation (Pending - After Phase 3)

**Phase Goal:** Generate importable Anki deck (.apkg file) and validate correctness.

**Status:** ⬜ Planning (Will create PHASE_4_PLAN.md after Phase 3 completes)

**High-Level Tasks:**
1. Choose Anki deck format (genanki library)
2. Build Anki deck converter
3. Bundle media files
4. Test import locally
5. Spot-check card quality
6. Generate final report

---

## Supporting Tasks (Not Phase-Specific)

### Documentation
- 🟩 Completed: Project organization and brainstorming
- 🟩 Completed: Created PHASE_1_PLAN.md with 10 detailed tasks
- 🟩 Completed: Reorganized documentation into clean structure
- ⬜ Create: PHASE_2_PLAN.md (after Phase 1)
- ⬜ Create: PHASE_3_PLAN.md (after Phase 2)
- ⬜ Create: PHASE_4_PLAN.md (after Phase 3)

### Code Organization
- 🟩 Completed: Rust workspace structure (text_extractor, media_extractor)
- ⬜ Pending: Phase 2 Claude Code skill creation
- ⬜ Pending: Phase 3 modular Rust pipeline

---

## Quick Navigation

**To Start Phase 1:**
1. Read [PHASE_1_PLAN.md](PHASE_1_PLAN.md) in detail
2. Begin with Task 1
3. Update this file as you progress

**For Reference Documentation:**
- Installation: [docs/reference/RUST_SETUP.md](../reference/RUST_SETUP.md)
- Running: [docs/reference/RUST_USAGE.md](../reference/RUST_USAGE.md)
- Architecture: [docs/reference/RUST_ARCHITECTURE.md](../reference/RUST_ARCHITECTURE.md)
- Validation: [docs/reference/VALIDATION.md](../reference/VALIDATION.md)
- Troubleshooting: [docs/reference/TROUBLESHOOTING.md](../reference/TROUBLESHOOTING.md)

**For Analysis & Planning:**
- Question count justification: [docs/reference/QUESTION_ID_DISCOVERY.md](../reference/QUESTION_ID_DISCOVERY.md)
- Phase 2+ syllabus plan: [docs/reference/SYLLABUS_EXTRACTION.md](../reference/SYLLABUS_EXTRACTION.md)
- Media extraction reference: [docs/reference/VIDEO_SVG_EXTRACTION.md](../reference/VIDEO_SVG_EXTRACTION.md)
- Risk analysis: [docs/risks/POTENTIAL_SYLLABUS_ERRORS.md](../risks/POTENTIAL_SYLLABUS_ERRORS.md)

---

## Progress Summary

| Phase | Status | Tasks | Complete | Progress |
|-------|--------|-------|----------|----------|
| Phase 1 | 🟨 Starting | 10 | 0/10 | 0% |
| Phase 2 | ⬜ Pending | TBD | 0/? | 0% |
| Phase 3 | ⬜ Pending | TBD | 0/? | 0% |
| Phase 4 | ⬜ Pending | TBD | 0/? | 0% |
| **Total** | **🟨 In Progress** | **~30** | **0/30** | **0%** |

---

## How to Update This File

As you complete tasks:

1. **In Progress:** Change ⬜ to 🟨 at task level
2. **Completed:** Change 🟨 to 🟩 and date completed
3. **Blocked:** Change to 🔴 and note blocker
4. **At Risk:** Change to ⚠️ and note risk

**Example Format for Completion:**
```
### Task 1: Finalize Question Count & Discovery Algorithm
- **Status:** 🟩 Completed (December 27, 2025)
```

---

## Key Milestones

- **Phase 1 Complete:** All 2,233 questions extracted
- **Phase 2 Complete:** ~6,700 atomic facts extracted
- **Phase 3 Complete:** ~6,700 Anki cards generated
- **Phase 4 Complete:** mksap.apkg ready to import

**Overall Project Complete:** Ready-to-study MKSAP Anki deck with full medical knowledge base

---

**This is your master todo list. Update regularly as you progress through phases.**
