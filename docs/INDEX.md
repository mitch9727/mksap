# MKSAP Documentation Index

**Start here for project-level documentation and pointers to component docs.**

**Last Updated**: January 23, 2026

---

## Start Here

1. **[Project Overview](README.md)** - Project goals, scope, and architecture
2. **[QUICKSTART.md](QUICKSTART.md)** - Essential commands and setup
3. **[DOCUMENTATION_POLICY.md](DOCUMENTATION_POLICY.md)** - Documentation lifecycle and organization rules
4. **[DOCUMENTATION_MAINTENANCE_GUIDE.md](DOCUMENTATION_MAINTENANCE_GUIDE.md)** - Maintenance workflows and reviews

**Component Docs**:
- **[Extractor Documentation](../extractor/docs/INDEX.md)** - Phase 1 extraction pipeline
- **[Statement Generator Documentation](../statement_generator/docs/INDEX.md)** - Phase 2-4 pipeline
- **[Anking Analysis Docs](../anking_analysis/docs/INDEX.md)** - Anking analysis workflow

---

## Recent Work (January 2026)

### Comprehensive Codebase Audit (Jan 23, 2026)
- **[Audit Plan](../.claude/plans/splendid-herding-sutherland.md)** - Original audit findings (performance, code quality, statement quality)
- **[Audit Implementation Summary](../statement_generator/artifacts/AUDIT_IMPLEMENTATION_SUMMARY.md)** - What was completed by parallel agents
- **[Async Implementation](../statement_generator/docs/ASYNC_IMPLEMENTATION.md)** - Async infrastructure analysis and status

**Key Improvements**:
- ✅ ProviderRegistry pattern (eliminated 40-line if-elif chain)
- ✅ ValidatorRegistry pattern (11 validators, 93.3% pass rate)
- ✅ NLP guidance consolidation (~200 lines removed)
- ✅ LLM response caching (5-15% speedup on re-runs)
- ✅ Performance optimizations (orjson, lru_cache, NLP singletons)

---

## Project Status

- 🟢 **[Phase 1 Completion Report](../extractor/docs/PHASE_1_COMPLETION_REPORT.md)**
- 🟢 **[Phase 4 Deployment Plan](../statement_generator/docs/deployment/PHASE4_DEPLOYMENT_PLAN.md)**
- 🟡 **[Phase 3 Final Report](../statement_generator/artifacts/phase3_evaluation/PHASE3_COMPLETE_FINAL_REPORT.md)**

---

## Architecture & Design

### Core Architecture (Updated Jan 23, 2026)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview (4-layer design, data flow, tech stack)
- **[CODING_STANDARDS.md](CODING_STANDARDS.md)** - Python best practices, naming conventions, patterns
- **[PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)** - Profiling, caching, benchmarking guide
- **[REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)** - Implementation patterns for improvements



---

## Documentation Layout (Project-Level Only)

- `docs/` - Project overview, policies, and architecture
- `extractor/docs/` - Rust extractor documentation (Phase 1)
- `statement_generator/docs/` - Statement generator documentation (Phases 2-4)
- `anking_analysis/docs/` - Anking analysis documentation

Component-specific docs should live alongside their owning folders to keep this global index lean and focused.
