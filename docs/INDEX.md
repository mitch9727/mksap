# MKSAP Documentation Index

**Start here for navigation across the MKSAP documentation set.**

**Last Updated**: January 19, 2026

---

## Project Status

**Phase 1**: ✅ Complete (2,198 questions extracted)
**Phase 2**: ✅ Complete (LLM-based statement generator)
**Phase 3**: ✅ Complete (Hybrid pipeline validated - 92.9% pass rate)
**Phase 4**: 📋 Ready to Execute (Production deployment)

---

## Start Here

1. **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Project goals, architecture, and scope
2. **[QUICKSTART.md](QUICKSTART.md)** - Essential commands and setup
3. **[DOCUMENTATION_POLICY.md](DOCUMENTATION_POLICY.md)** - Documentation lifecycle and organization policy (for AI assistants)
4. **[TODO.md](../TODO.md)** - Active and planned work

**Phase Status Documents**:
- 🟢 **[PHASE_4_DEPLOYMENT_PLAN.md](plans/PHASE4_DEPLOYMENT_PLAN.md)** - Phase 4 production deployment plan
- 🟡 **[PHASE_3_STATUS.md](PHASE_3_STATUS.md)** - Phase 3 hybrid pipeline validation (complete)
- 🟡 **[PHASE_2_STATUS.md](PHASE_2_STATUS.md)** - Phase 2 statement generator (complete)
- 🟡 **[PHASE_1_COMPLETION_REPORT.md](PHASE_1_COMPLETION_REPORT.md)** - Phase 1 extraction results

---

## Documentation Categories

This documentation is organized by lifecycle and purpose:

- **🟢 Active** - Currently maintained, reflects current development
- **🟡 Reference** - Completed work, not actively updated but still relevant
- **⚪ Archive** - Historical documentation, phase-specific or superseded

See [DOCUMENTATION_POLICY.md](DOCUMENTATION_POLICY.md) for details on documentation lifecycle, categories, and update policies.

---

## Documentation Layout

- Top-level docs: project overview, quickstart, status, scope, audits
- `architecture/` - System design and codebase guides
- `reference/` - Technical documentation and feature guides
- `specifications/` - Formats and data extraction specs
- `plans/` - Implementation plans and strategies
- `archive/` - Phase-specific and superseded documentation

---

## Core Project Docs

- 🟢 **[EXTRACTION_SCOPE.md](EXTRACTION_SCOPE.md)** - Extraction scope and success criteria
- 🟡 **[EXTRACTOR_CODE_AUDIT.md](EXTRACTOR_CODE_AUDIT.md)** - Code cleanup analysis (Phase 1)
- 🟢 **[DOCUMENTATION_MAINTENANCE_GUIDE.md](DOCUMENTATION_MAINTENANCE_GUIDE.md)** - Doc workflow and standards
- 🟢 **[DOCUMENTATION_POLICY.md](DOCUMENTATION_POLICY.md)** - Documentation lifecycle and organization policy

---

## Architecture & Design

- 🟢 **[PROJECT_ORGANIZATION.md](architecture/PROJECT_ORGANIZATION.md)** - System architecture and pipeline overview
- 🟢 **[CODEBASE_GUIDE.md](architecture/CODEBASE_GUIDE.md)** - How to navigate the code

---

## Phase 2-4: Statement Generator, Validation & Deployment

- 🟢 **[STATEMENT_GENERATOR.md](reference/STATEMENT_GENERATOR.md)** - Phase 2 usage, CLI, and pipeline
- 🟡 **[PHASE_2_STATUS.md](PHASE_2_STATUS.md)** - Phase 2 implementation status (complete)
- 🟡 **[PHASE_3_STATUS.md](PHASE_3_STATUS.md)** - Phase 3 hybrid pipeline validation (complete - 92.9% pass rate)
- 🟢 **[PHASE_4_DEPLOYMENT_PLAN.md](plans/PHASE4_DEPLOYMENT_PLAN.md)** - Phase 4 production deployment plan
- 🟢 **[VALIDATION.md](reference/VALIDATION.md)** - Data quality checks and validation framework
- 🟡 **[NLP_MODEL_COMPARISON.md](reference/NLP_MODEL_COMPARISON.md)** - ScispaCy model evaluation and selection
- 🟡 **[SPECIALIZED_NER_EVALUATION.md](reference/SPECIALIZED_NER_EVALUATION.md)** - Specialized NER models evaluation
- 🟡 **[LEGACY_STATEMENT_STYLE_GUIDE.md](reference/LEGACY_STATEMENT_STYLE_GUIDE.md)** - Legacy style guidance (reference only)
- 🟢 **[CLOZE_FLASHCARD_BEST_PRACTICES.md](reference/CLOZE_FLASHCARD_BEST_PRACTICES.md)** - Evidence-based flashcard guidance

---

## Technical Reference

- 🟢 **[PHASE_1_DEEP_DIVE.md](reference/PHASE_1_DEEP_DIVE.md)** - Phase 1 architecture and technical details
- 🟢 **[TROUBLESHOOTING.md](reference/TROUBLESHOOTING.md)** - Common issues and solutions
- 🟡 **[TECHNICAL_SPEC.md](scraper/TECHNICAL_SPEC.md)** - Extractor technical spec and interfaces (Phase 1)
- 🟡 **[NLP_PERSISTENCE_IMPLEMENTATION.md](reference/NLP_PERSISTENCE_IMPLEMENTATION.md)** - NLP metadata persistence implementation details
- 🟡 **[VALIDATION_IMPLEMENTATION.md](reference/VALIDATION_IMPLEMENTATION.md)** - Validation framework implementation details
- 🟡 **[SCISPACY_INTEGRATION.md](SCISPACY_INTEGRATION.md)** - ScispaCy NLP model integration guide

---

## Specifications

- 🟡 **[VIDEO_SVG_EXTRACTION.md](specifications/VIDEO_SVG_EXTRACTION.md)** - Browser-based media extraction specification (Phase 1)

---

## Plans & Roadmaps

- 🟢 **[PHASE4_DEPLOYMENT_PLAN.md](plans/PHASE4_DEPLOYMENT_PLAN.md)** - Phase 4 production deployment strategy
- 🟡 **[Phase 3 LLM Integration Evaluation](plans/2026-01-16-phase3-llm-integration-evaluation.md)** - Phase 3 evaluation plan
- 🟡 **[Phase 3 Test Questions](phase3_evaluation/test_questions.md)** - Test question selection for Phase 3 evaluation

---

## Completion Reports

- 🟡 **[PHASE_1_COMPLETION_REPORT.md](PHASE_1_COMPLETION_REPORT.md)** - Final Phase 1 metrics (2,198 questions extracted)
- 🟡 **[Phase 3 Final Report](../statement_generator/artifacts/phase3_evaluation/PHASE3_COMPLETE_FINAL_REPORT.md)** - Phase 3 hybrid pipeline validation (92.9% pass rate)

---

## Archives

**Phase 1 Documentation** (archived after Phase 1 completion):
- ⚪ **[RUST_SETUP.md](archive/phase1/RUST_SETUP.md)** - Rust installation and configuration (Phase 1 only)
- ⚪ **[RUST_USAGE.md](archive/phase1/RUST_USAGE.md)** - How to run extraction (Phase 1 only)
- ⚪ **[RUST_ARCHITECTURE.md](archive/phase1/RUST_ARCHITECTURE.md)** - Rust implementation details (Phase 1 only)
- ⚪ **[EXTRACTION_OVERVIEW.md](archive/phase1/EXTRACTION_OVERVIEW.md)** - Extractor overview (Phase 1 only)
- ⚪ **[DESERIALIZATION_ISSUES.md](archive/phase1/DESERIALIZATION_ISSUES.md)** - API response quirks (Phase 1 only)

**Note**: Phase 1 comprehensive reference is maintained in [PHASE_1_DEEP_DIVE.md](reference/PHASE_1_DEEP_DIVE.md) (active).

---

## Navigation Tips

**For New Contributors**:
1. Start with [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
2. Review current phase status: [PHASE_3_STATUS.md](PHASE_3_STATUS.md) and [PHASE_4_DEPLOYMENT_PLAN.md](plans/PHASE4_DEPLOYMENT_PLAN.md)
3. Check [TODO.md](../TODO.md) for active work

**For Running Statement Generator (Phase 2-4)**:
1. Quick reference: [QUICKSTART.md](QUICKSTART.md)
2. Detailed instructions: [STATEMENT_GENERATOR.md](reference/STATEMENT_GENERATOR.md)
3. Troubleshooting: [TROUBLESHOOTING.md](reference/TROUBLESHOOTING.md)

**For Development**:
1. Architecture: [PROJECT_ORGANIZATION.md](architecture/PROJECT_ORGANIZATION.md)
2. Documentation policy: [DOCUMENTATION_POLICY.md](DOCUMENTATION_POLICY.md)
3. Maintenance: [DOCUMENTATION_MAINTENANCE_GUIDE.md](DOCUMENTATION_MAINTENANCE_GUIDE.md)
