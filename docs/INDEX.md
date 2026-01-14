# MKSAP Documentation Index

**Start here for navigation across the MKSAP documentation set.**

**Last Updated**: January 6, 2026

---

## Start Here

1. **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Project goals, architecture, and scope
2. **[QUICKSTART.md](QUICKSTART.md)** - Essential commands and setup
3. **[PHASE_2_STATUS.md](PHASE_2_STATUS.md)** - Current implementation status and priorities
4. **[PHASE_1_COMPLETION_REPORT.md](PHASE_1_COMPLETION_REPORT.md)** - Phase 1 results (2,198 questions)
5. **[TODO.md](../TODO.md)** - Active and planned work

---

## Documentation Layout

- Top-level docs: project overview, quickstart, status, scope, audits, changelog
- `architecture/` - System design and codebase guides
- `reference/` - Rust extractor usage, troubleshooting, and validation
- `specifications/` - Formats and data extraction specs
- `archive/` - Historical plans and reports
- `old_method/` - Legacy reference output (excluded from validation)

---

## Core Project Docs

- **[EXTRACTION_SCOPE.md](EXTRACTION_SCOPE.md)** - Extraction scope and success criteria
- **[EXTRACTOR_CODE_AUDIT.md](EXTRACTOR_CODE_AUDIT.md)** - Code cleanup analysis
- **[CHANGELOG.md](CHANGELOG.md)** - Documentation change notes
- **[DOCUMENTATION_MAINTENANCE_GUIDE.md](DOCUMENTATION_MAINTENANCE_GUIDE.md)** - Doc workflow and standards

---

## Architecture & Design

- **[PROJECT_ORGANIZATION.md](architecture/PROJECT_ORGANIZATION.md)** - System architecture and pipeline overview
- **[CODEBASE_GUIDE.md](architecture/CODEBASE_GUIDE.md)** - How to navigate the code

---

## Phase 2: Statement Generator

- **[STATEMENT_GENERATOR.md](reference/STATEMENT_GENERATOR.md)** - Phase 2 usage, CLI, and pipeline
- **[PHASE_2_STATUS.md](PHASE_2_STATUS.md)** - Implementation status, open work, testing notes
- **[CLOZE_FLASHCARD_BEST_PRACTICES.md](reference/CLOZE_FLASHCARD_BEST_PRACTICES.md)** - Evidence-based
  flashcard guidance

---

## Rust Extractor Reference

- **[RUST_SETUP.md](reference/RUST_SETUP.md)** - Installation and configuration
- **[RUST_USAGE.md](reference/RUST_USAGE.md)** - How to run extraction
- **[RUST_ARCHITECTURE.md](reference/RUST_ARCHITECTURE.md)** - Implementation details
- **[TECHNICAL_SPEC.md](scraper/TECHNICAL_SPEC.md)** - Extractor technical spec and interfaces
- **[VALIDATION.md](reference/VALIDATION.md)** - Data quality checks
- **[TROUBLESHOOTING.md](reference/TROUBLESHOOTING.md)** - Common issues and solutions
- **[EXTRACTION_OVERVIEW.md](reference/EXTRACTION_OVERVIEW.md)** - Extractor overview and scope
- **[DESERIALIZATION_ISSUES.md](reference/DESERIALIZATION_ISSUES.md)** - API response quirks

---

## Specifications

- **[VIDEO_SVG_EXTRACTION.md](specifications/VIDEO_SVG_EXTRACTION.md)** - Browser-based media extraction specification

---

## Reports

- **[PHASE_1_COMPLETION_REPORT.md](PHASE_1_COMPLETION_REPORT.md)** - Final Phase 1 metrics
- **[archive/reports/](archive/reports/)** - Historical extraction and cleanup reports
- **[archive/phase-2/reports/](archive/phase-2/reports/)** - Week-by-week Phase 2 reports and handoffs

---

## Archive

### Phase 1 Planning

- **[PHASE_1_PLAN.md](archive/phase-1/PHASE_1_PLAN.md)** - Original Phase 1 detailed plan
- **[QUESTION_ID_DISCOVERY.md](archive/phase-1/QUESTION_ID_DISCOVERY.md)** - Historical discovery analysis

### Phase 2 Planning

- **[PHASE_2_PLANNING_SUMMARY.md](archive/phase-2/planning/PHASE_2_PLANNING_SUMMARY.md)** - Archived Week 1-7 roadmap
- **[PHASE_2_DETAILED_PLANNING.md](archive/phase-2/planning/PHASE_2_DETAILED_PLANNING.md)** - Detailed Phase 2 plan
- **[SPACY_SCISPACY_HYBRID_PLAN.md](archive/phase-2/planning/SPACY_SCISPACY_HYBRID_PLAN.md)** - Hybrid NLP plan

### Planning Sessions

- **[BRAINSTORM_SESSION_COMPLETE.md](archive/planning-sessions/BRAINSTORM_SESSION_COMPLETE.md)** - Initial brainstorm

---

## Navigation Tips

**For New Contributors**:
1. Start with PROJECT_OVERVIEW.md
2. Read PHASE_1_COMPLETION_REPORT.md
3. Review RUST_SETUP.md and RUST_USAGE.md

**For Running Extraction**:
1. Quick reference: QUICKSTART.md
2. Detailed instructions: RUST_USAGE.md
3. Troubleshooting: TROUBLESHOOTING.md

**For Development**:
1. Architecture: RUST_ARCHITECTURE.md
2. Code audit: EXTRACTOR_CODE_AUDIT.md
3. Maintenance: DOCUMENTATION_MAINTENANCE_GUIDE.md

**For Understanding History**:
1. Phase 1 completion: PHASE_1_COMPLETION_REPORT.md
2. Original plan: archive/phase-1/PHASE_1_PLAN.md
3. Discovery analysis: archive/phase-1/QUESTION_ID_DISCOVERY.md
4. Planning sessions: archive/planning-sessions/

---

**Project Status**: Phase 1 Complete (2,198 questions extracted)
**Next Phase**: Phase 2 - Statement Generator (active)
