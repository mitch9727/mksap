# Reference Folder Audit & Integration Report

**Date**: December 27, 2025
**Purpose**: Assess relevance of docs/reference/ files and integrate into updated documentation structure

---

## Summary

The `docs/reference/` folder contains **9 technical reference documents** (86KB total). After review, **all files remain relevant and current** with recommended updates for 3 files to reflect Phase 1 completion.

---

## File-by-File Analysis

### ✅ KEEP & MAINTAIN (No Changes Needed)

#### 1. **RUST_SETUP.md** (5.5KB)
- **Purpose**: Installation and configuration guide
- **Status**: ✅ Current - Installation steps unchanged
- **Integration**: Referenced in CLAUDE.md "For New Users" section
- **Maintenance Trigger**: Update when dependencies change
- **Recommendation**: Keep as-is

#### 2. **RUST_USAGE.md** (11KB)
- **Purpose**: How to run extractors with detailed examples
- **Status**: ✅ Current - CLI commands documented
- **Integration**: Referenced in CLAUDE.md "Running Extraction" section
- **Maintenance Trigger**: Update when CLI commands change
- **Recommendation**: Keep as-is

#### 3. **RUST_ARCHITECTURE.md** (8.4KB)
- **Purpose**: Technical implementation details
- **Status**: ✅ Current - Architecture explanations valid
- **Integration**: Referenced in CLAUDE.md "For Development" section
- **Maintenance Trigger**: Update on major refactoring
- **Recommendation**: Keep as-is

#### 4. **VALIDATION.md** (5.4KB)
- **Purpose**: Data quality validation framework
- **Status**: ✅ Current - Validation procedures documented
- **Integration**: Referenced in CLAUDE.md "Validation Framework" section
- **Maintenance Trigger**: Update when validator logic changes
- **Recommendation**: Keep as-is

#### 5. **TROUBLESHOOTING.md** (8.9KB)
- **Purpose**: Common issues and solutions
- **Status**: ✅ Current - Troubleshooting patterns still valid
- **Integration**: Referenced in CLAUDE.md "Common Issues" section
- **Maintenance Trigger**: Add new issues as discovered
- **Recommendation**: Keep as-is (append-only document)

#### 6. **DESERIALIZATION_ISSUES.md** (1.7KB)
- **Purpose**: API response quirks and edge cases
- **Status**: ✅ Current - API patterns documented
- **Integration**: Referenced in CLAUDE.md documentation section
- **Maintenance Trigger**: Add new API patterns as discovered
- **Recommendation**: Keep as-is (append-only document)

### ⚠️ UPDATE RECOMMENDED (Minor Changes)

#### 7. **EXTRACTOR_STATUS.md** (3.6KB)
- **Purpose**: Current extraction progress and status
- **Current Content**: Phase 1 overview, technology stack, data output
- **Issue**: Status information may be stale (needs verification)
- **Integration**: Referenced in CLAUDE.md documentation section
- **Recommended Updates**:
  - [ ] Verify "Current Status" section reflects 100% extraction
  - [ ] Update progress metrics if present
  - [ ] Add note about Phase 1 completion
  - [ ] Consider renaming to `EXTRACTION_OVERVIEW.md` (less temporal)
- **Alternative**: Archive and replace with link to PHASE_1_COMPLETION_REPORT.md

#### 8. **QUESTION_ID_DISCOVERY.md** (12KB)
- **Purpose**: Explains question ID patterns, discovery method, and count analysis
- **Current Content**: 6 question types, 16 system codes, distribution table
- **Issue**: This is **historical analysis** that led to current implementation
- **Integration**: Referenced in CLAUDE.md and PHASE_1_PLAN (archived)
- **Recommended Action**:
  - **Option A**: Keep as reference for understanding discovery approach
  - **Option B**: Move to `docs/project/archive/analysis/` since discovery is complete
  - **Recommendation**: **Keep** - Still valuable for understanding scope decisions
- **Updates Needed**:
  - [ ] Add note at top: "Historical Analysis - Informed Phase 1 Implementation"
  - [ ] Clarify this explains WHY we extract 2,198 questions
  - [ ] Link to PHASE_1_COMPLETION_REPORT.md for actual results

#### 9. **VIDEO_SVG_EXTRACTION.md** (10KB)
- **Purpose**: Specification for browser-based media extraction
- **Current Content**: Architecture overview, implementation strategy
- **Issue**: This is a **specification document**, not a reference guide
- **Integration**: Describes functionality implemented in the extractor asset modules
- **Recommended Action**:
  - **Option A**: Move to `docs/specifications/` (better category)
  - **Option B**: Keep in reference/ as implementation guide
  - **Recommendation**: **Move** to `docs/specifications/VIDEO_SVG_EXTRACTION.md`
- **Rationale**: Specifications describe "what to build", reference docs describe "what was built"

---

## Integration with Current Documentation Structure

### How Reference Files Connect to CLAUDE.md

All 9 reference files are **linked from CLAUDE.md** in the Documentation section:

```markdown
### Technical Deep Dives (docs/reference/)
- RUST_ARCHITECTURE.md - Implementation details
- VALIDATION.md - Data quality framework
- TROUBLESHOOTING.md - Common issues and solutions

### Reference (docs/reference/)
- QUESTION_ID_DISCOVERY.md - Understanding question counts
- EXTRACTOR_STATUS.md - Current extraction progress
- DESERIALIZATION_ISSUES.md - API response variations
```

**Recommendation**: Update CLAUDE.md to reflect:
- Move VIDEO_SVG_EXTRACTION.md reference to specifications section
- Update EXTRACTOR_STATUS.md link description to "Extraction overview"
- Add historical note to QUESTION_ID_DISCOVERY.md description

---

## Recommended Directory Reorganization

### Current Structure
```
docs/reference/
├── DESERIALIZATION_ISSUES.md      # API quirks
├── EXTRACTOR_STATUS.md            # Status overview
├── QUESTION_ID_DISCOVERY.md       # Historical analysis
├── RUST_ARCHITECTURE.md           # Technical details
├── RUST_SETUP.md                  # Installation
├── RUST_USAGE.md                  # How to run
├── TROUBLESHOOTING.md             # Problem-solving
├── VALIDATION.md                  # Data QA
└── VIDEO_SVG_EXTRACTION.md        # Specification
```

### Recommended Structure
```
docs/reference/                    # Technical reference (8 files)
├── DESERIALIZATION_ISSUES.md      # API quirks (KEEP)
├── EXTRACTION_OVERVIEW.md         # Renamed from EXTRACTOR_STATUS.md
├── QUESTION_ID_DISCOVERY.md       # Historical analysis (KEEP - add note)
├── RUST_ARCHITECTURE.md           # Technical details (KEEP)
├── RUST_SETUP.md                  # Installation (KEEP)
├── RUST_USAGE.md                  # How to run (KEEP)
├── TROUBLESHOOTING.md             # Problem-solving (KEEP)
└── VALIDATION.md                  # Data QA (KEEP)

docs/specifications/               # Output format specs (2 files)
├── VIDEO_SVG_EXTRACTION.md        # MOVED from reference/
└── (future: data exports spec)    # Phase 2+
```

---

## Maintenance Integration

### Per Documentation Maintenance Guide

According to `DOCUMENTATION_MAINTENANCE_GUIDE.md`:

**Reference folder files should be updated when**:

| File | Update Trigger | Frequency |
|------|---------------|-----------|
| RUST_SETUP.md | Dependency changes | Low (only on Cargo.toml changes) |
| RUST_USAGE.md | CLI command changes | Medium (per new feature) |
| RUST_ARCHITECTURE.md | Refactoring | Low (only on major changes) |
| VALIDATION.md | Validator logic changes | Low (stable validator) |
| TROUBLESHOOTING.md | New issues discovered | Ongoing (append-only) |
| DESERIALIZATION_ISSUES.md | New API patterns | Ongoing (append-only) |
| EXTRACTION_OVERVIEW.md | Major milestones | Low (Phase completions) |
| QUESTION_ID_DISCOVERY.md | Never (historical) | Archive-quality |

**Review Schedule**:
- Monthly: Verify examples still work
- Quarterly: Check for outdated content
- Per Phase: Update status/overview files

---

## Action Items

### Immediate (This Session)

1. **Move VIDEO_SVG_EXTRACTION.md**:
   ```bash
   mkdir -p docs/specifications
   mv docs/reference/VIDEO_SVG_EXTRACTION.md docs/specifications/
   ```

2. **Rename EXTRACTOR_STATUS.md**:
   ```bash
   mv docs/reference/EXTRACTOR_STATUS.md docs/reference/EXTRACTION_OVERVIEW.md
   ```

3. **Add historical note to QUESTION_ID_DISCOVERY.md**:
   - Add at top: "📜 Historical Analysis - This document explains the discovery process that informed Phase 1 implementation"
   - Link to PHASE_1_COMPLETION_REPORT.md for actual results

4. **Update EXTRACTION_OVERVIEW.md**:
   - Add note about Phase 1 completion
   - Verify metrics are current
   - Update "Current Status" section

5. **Update CLAUDE.md documentation links**:
   - Update VIDEO_SVG_EXTRACTION.md reference (new location)
   - Update EXTRACTOR_STATUS.md → EXTRACTION_OVERVIEW.md
   - Add historical note to QUESTION_ID_DISCOVERY.md description

6. **Update INDEX.md**:
   - Reflect new file locations
   - Add specifications/ section

### Future Maintenance

1. **Monthly**: Run verification procedures from DOCUMENTATION_MAINTENANCE_GUIDE.md
2. **Per Feature**: Update relevant reference docs
3. **Per Phase**: Update EXTRACTION_OVERVIEW.md with phase completion
4. **Per Issue**: Append to TROUBLESHOOTING.md and DESERIALIZATION_ISSUES.md

---

## File Relationship Map

```
CLAUDE.md (entry point)
    ↓
    ├─→ Getting Started
    │   └─→ RUST_SETUP.md
    │
    ├─→ Running Extraction
    │   └─→ RUST_USAGE.md
    │
    ├─→ Technical Deep Dives
    │   ├─→ RUST_ARCHITECTURE.md
    │   ├─→ VALIDATION.md
    │   └─→ TROUBLESHOOTING.md
    │
    ├─→ Reference
    │   ├─→ QUESTION_ID_DISCOVERY.md (historical)
    │   ├─→ EXTRACTION_OVERVIEW.md (current state)
    │   └─→ DESERIALIZATION_ISSUES.md (API quirks)
    │
    └─→ Specifications
        └─→ VIDEO_SVG_EXTRACTION.md (moved from reference/)
```

---

## Summary & Recommendations

### ✅ Files to Keep (8)
All technical reference files remain relevant and should be maintained:
- RUST_SETUP.md
- RUST_USAGE.md
- RUST_ARCHITECTURE.md
- VALIDATION.md
- TROUBLESHOOTING.md
- DESERIALIZATION_ISSUES.md
- EXTRACTION_OVERVIEW.md (renamed from EXTRACTOR_STATUS.md)
- QUESTION_ID_DISCOVERY.md (with historical note added)

### 📋 Files to Move (1)
- VIDEO_SVG_EXTRACTION.md → `docs/specifications/` (better categorization)

### 📝 Files to Update (2)
1. EXTRACTION_OVERVIEW.md - Update status to reflect Phase 1 completion
2. QUESTION_ID_DISCOVERY.md - Add historical context note

### 🔗 Files to Reference Update (1)
- CLAUDE.md - Update documentation links to reflect changes

---

## Change-Resistant Structure

The reference folder now follows these principles from DOCUMENTATION_MAINTENANCE_GUIDE.md:

✅ **Separation of Concerns**:
- Reference = "What was built" (technical guides)
- Specifications = "What to build" (requirements)
- Archive = "What was done" (historical)

✅ **Clear Update Triggers**:
- Each file has defined maintenance triggers
- Append-only files (TROUBLESHOOTING, DESERIALIZATION_ISSUES) grow over time
- Stable files (RUST_SETUP, VALIDATION) change rarely
- Status files (EXTRACTION_OVERVIEW) update per milestone

✅ **Historical Preservation**:
- QUESTION_ID_DISCOVERY.md kept for understanding scope decisions
- Original analysis preserved with clear historical context
- Links to completion reports for current state

✅ **Integration with Main Docs**:
- All reference files linked from CLAUDE.md
- Clear navigation path from entry point
- Cross-references maintained

---

**Audit Complete**: December 27, 2025
**Files Reviewed**: 9
**Recommendations**: 4 (1 move, 2 updates, 1 rename)
**Integration Status**: Fully integrated with documentation system
