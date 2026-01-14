# Documentation Maintenance Guide

**Purpose**: Ensure documentation stays synchronized with codebase changes **Last Updated**: January 13, 2026

---

## Overview

This guide establishes a systematic approach to keeping documentation aligned with code as the project evolves. The goal
is to prevent documentation drift while maintaining historical context for debugging and understanding past decisions.

---

## Documentation Structure

### Active Documentation
```
docs/
├── DOCUMENTATION_MAINTENANCE_GUIDE.md  # This file
│
├── INDEX.md                             # Navigation guide (UPDATE ON STRUCTURE CHANGES)
├── PROJECT_OVERVIEW.md                  # Project overview (KEEP CURRENT)
├── QUICKSTART.md                        # Command reference (UPDATE ON CLI CHANGES)
├── CHANGELOG.md                         # Documentation history (APPEND ONLY)
├── EXTRACTION_SCOPE.md                  # Scope definition (UPDATE ON SCOPE CHANGES)
├── PHASE_1_COMPLETION_REPORT.md         # Phase 1 results (FINAL, DO NOT EDIT)
├── PHASE_2_STATUS.md                    # Phase 2 status (KEEP CURRENT)
├── EXTRACTOR_CODE_AUDIT.md              # Code cleanup notes (ARCHIVE WHEN COMPLETE)
│
├── archive/                             # Historical documents
│   ├── planning-sessions/               # Brainstorm & planning meetings
│   ├── phase-1/                         # Phase 1 planning documents + discovery analysis
│   ├── phase-2/                         # Phase 2 planning + weekly reports (archived)
│   │   ├── planning/                    # Phase 2 planning documents
│   │   └── reports/                     # Phase 2 weekly reports and handoffs
│   └── reports/                         # Extraction reports (KEEP AS HISTORY)
│
├── architecture/                        # System design
│   └── PROJECT_ORGANIZATION.md          # 4-phase pipeline (UPDATE ON ARCHITECTURE CHANGES)
│
├── reference/                           # Technical documentation
│   ├── RUST_SETUP.md                    # Installation (UPDATE ON DEPENDENCY CHANGES)
│   ├── RUST_USAGE.md                    # How to run (UPDATE ON CLI CHANGES)
│   ├── RUST_ARCHITECTURE.md             # Technical details (UPDATE ON REFACTORING)
│   ├── VALIDATION.md                    # Data QA (UPDATE ON VALIDATOR CHANGES)
│   ├── TROUBLESHOOTING.md               # Problem-solving (ADD NEW ISSUES)
│   ├── DESERIALIZATION_ISSUES.md        # API quirks (ADD NEW PATTERNS)
│   ├── EXTRACTION_OVERVIEW.md           # Status & progress (UPDATE ON MILESTONES)
│   ├── STATEMENT_GENERATOR.md           # Phase 2 reference (UPDATE ON CLI CHANGES)
│   └── CLOZE_FLASHCARD_BEST_PRACTICES.md # Flashcard design guidance (STABLE)
│
├── specifications/                      # Output format specs
│   └── VIDEO_SVG_EXTRACTION.md          # Media extraction spec (UPDATE ON POLICY CHANGES)
│
├── scraper/                             # Scraper/extractor details
│   └── TECHNICAL_SPEC.md                # Extractor technical spec
│
└── old_method/                          # Legacy reference output (EXCLUDED FROM VALIDATION)
```

---

## Maintenance Triggers

### When to Update Documentation

| Code Change | Documentation to Update | Priority |
|-------------|------------------------|----------|
| **Add new module** | CLAUDE.md, RUST_ARCHITECTURE.md | HIGH |
| **Remove module** | CLAUDE.md, RUST_ARCHITECTURE.md, CHANGELOG.md | HIGH |
| **Refactor module** | RUST_ARCHITECTURE.md if structure changes significantly | MEDIUM |
| **Add CLI command** | CLAUDE.md, QUICKSTART.md, RUST_USAGE.md | HIGH |
| **Remove CLI command** | CLAUDE.md, QUICKSTART.md, RUST_USAGE.md, CHANGELOG.md | HIGH |
| **Change CLI arguments** | QUICKSTART.md, RUST_USAGE.md | MEDIUM |
| **Add dependency** | CLAUDE.md (Technology Stack section), RUST_SETUP.md | MEDIUM |
| **Remove dependency** | CLAUDE.md, RUST_SETUP.md, CHANGELOG.md | MEDIUM |
| **Fix bug** | TROUBLESHOOTING.md if pattern is reusable | LOW |
| **Add feature** | Relevant guide + CHANGELOG.md | MEDIUM |
| **API changes** | DESERIALIZATION_ISSUES.md if new patterns found | MEDIUM |
| **Pipeline changes** | PROJECT_ORGANIZATION.md, RUST_ARCHITECTURE.md | HIGH |
| **Complete phase** | Create PHASE_X_COMPLETION_REPORT.md, archive plan | HIGH |
| **Start new phase** | Create PHASE_X_PLAN.md | HIGH |

---

## Documentation Update Checklist

### For Module Changes

When adding/removing/refactoring modules:

1. **Update CLAUDE.md**:
   - [ ] Module organization section
   - [ ] Line count totals
   - [ ] Module descriptions
   - [ ] Update "Last Updated" timestamp

2. **Update RUST_ARCHITECTURE.md**:
   - [ ] Module descriptions
   - [ ] Data flow diagrams
   - [ ] File structure examples

3. **Update CHANGELOG.md**:
   - [ ] Add entry with date
   - [ ] Note module changes
   - [ ] Link to commit/PR if applicable

### For CLI Changes

When adding/removing/changing CLI commands:

1. **Update CLAUDE.md**:
   - [ ] Common Commands section
   - [ ] Add/remove command examples
   - [ ] Update command descriptions

2. **Update QUICKSTART.md**:
   - [ ] Add/remove command
   - [ ] Update arguments if changed

3. **Update RUST_USAGE.md**:
   - [ ] Detailed command documentation
   - [ ] Examples and use cases

4. **Update CHANGELOG.md**:
   - [ ] Note CLI changes
   - [ ] Migration notes if breaking change

### For Architectural Changes

When changing system architecture:

1. **Update PROJECT_ORGANIZATION.md**:
   - [ ] Pipeline diagrams
   - [ ] Component descriptions
   - [ ] Data flow explanations

2. **Update RUST_ARCHITECTURE.md**:
   - [ ] Technical implementation details
   - [ ] Module interactions
   - [ ] Design decisions

3. **Update CLAUDE.md**:
   - [ ] Project Architecture section
   - [ ] Reflect new design

4. **Update CHANGELOG.md**:
   - [ ] Major architectural changes
   - [ ] Rationale for changes

---

## Archive Policy

### When to Archive Documents

**Archive documents when they are:**
1. **Planning sessions** - Brainstorms and design meetings
2. **Phase plans** - When phase completes, archive plan and create completion report
3. **Phase reports** - Weekly or milestone progress summaries and handoffs
4. **Extraction reports** - Time-stamped audits and cleanup summaries
5. **Legacy analysis** - Rare historical context that still informs decisions

**DO NOT archive:**
- Current technical reference docs
- Active command guides
- Architectural documentation (unless doing major rewrite)
- Troubleshooting guides (they accumulate knowledge)
- One-off completion notices or superseded specs (summarize in CHANGELOG, then delete)

### Archive Location

```
docs/archive/
├── planning-sessions/          # Brainstorms, design meetings
├── phase-1/                    # Phase 1 planning documents
├── phase-2/                    # Phase 2 planning + weekly reports (archived)
│   ├── planning/               # Phase 2 planning documents
│   └── reports/                # Phase 2 weekly reports and handoffs
└── reports/                    # Extraction cleanup and discovery reports
```

### Archive Naming Convention

When archiving:
1. Keep original filename
2. Add date prefix if multiple versions: `YYYY-MM-DD_original-name.md`
3. Update INDEX.md to reference archive location
4. Add entry to CHANGELOG.md noting archival

---

## Review Schedule

### Regular Reviews

**Monthly** (during active development):
- [ ] Review CLAUDE.md for accuracy
- [ ] Check module counts match actual codebase
- [ ] Verify all CLI commands documented
- [ ] Update "Last Updated" timestamps

**Quarterly** (during maintenance):
- [ ] Review all reference docs for accuracy
- [ ] Archive completed phase plans
- [ ] Clean up outdated troubleshooting entries
- [ ] Consolidate CHANGELOG.md if too long

**Per Phase**:
- [ ] Before phase start: Create PHASE_X_PLAN.md
- [ ] During phase: Update progress in plan
- [ ] After phase: Create PHASE_X_COMPLETION_REPORT.md
- [ ] After phase: Archive phase plan to `archive/phase-x/`

---

## Verification Procedures

### Quick Documentation Health Check

Run these checks to ensure documentation is current:

```bash
# 1. Verify module count in CLAUDE.md matches actual modules
rg --files -g '*.rs' extractor | wc -l
# Compare to CLAUDE.md "Extractor Module Organization" count

# 2. Verify CLI commands documented
./target/release/mksap-extractor --help
# Compare to CLAUDE.md "Common Commands" section

# 3. Check for broken documentation links
cd docs
grep -r "](.*\.md)" . | grep -v "^Binary"
# Manually verify links are valid

# 4. Verify "Last Updated" timestamps are recent
grep "Last Updated" docs/**/*.md
# Should be within last 3 months for active docs
```

### Deep Documentation Audit

Perform full audit quarterly or when making major changes:

1. **Module inventory**:
   - [ ] List all modules in codebase
   - [ ] Compare to CLAUDE.md module list
   - [ ] Update discrepancies

2. **Command inventory**:
   - [ ] Run --help for all binaries
   - [ ] Compare to documented commands
   - [ ] Update discrepancies

3. **Link validation**:
   - [ ] Test all internal documentation links
   - [ ] Fix broken references
   - [ ] Update moved files

4. **Accuracy review**:
   - [ ] Read through key docs (CLAUDE.md, QUICKSTART.md)
   - [ ] Verify examples still work
   - [ ] Update outdated content

5. **Archive review**:
   - [ ] Identify historical documents in main docs
   - [ ] Move to appropriate archive location
   - [ ] Update INDEX.md

---

## Special Cases

### Handling Breaking Changes

When code changes break documented workflows:

1. **Before commit**:
   - [ ] Update all affected documentation
   - [ ] Add migration notes to CHANGELOG.md
   - [ ] Consider adding MIGRATION_GUIDE.md if major

2. **In commit message**:
   - [ ] Note documentation updates
   - [ ] Reference updated docs in commit

3. **After commit**:
   - [ ] Verify documentation matches new code
   - [ ] Test examples in fresh environment

### Handling Experimental Features

For features under development:

1. **Don't document in main docs** until stable
2. **Use comment blocks** in code to explain experimental features
3. **Add to CHANGELOG.md** when feature graduates to stable
4. **Document fully** only when feature is release-ready

### Handling Deprecated Features

When deprecating code:

1. **Mark as deprecated** in documentation (add "⚠️ Deprecated" tag)
2. **Add to CHANGELOG.md** with deprecation notice
3. **Keep documentation** until feature is removed
4. **After removal**:
   - [ ] Remove from main documentation
   - [ ] Add removal note to CHANGELOG.md
   - [ ] Archive documentation if historically valuable

---

## Documentation Standards

### Scope and Exclusions

- `docs/old_method/` contains legacy output and reference material only.
- Exclude `docs/old_method/` from documentation validation (links, formatting, line length, and heading rules).

### Documentation Placement (Claude/Codex)

- All generated documentation lives under `docs/`.
- Do not create module-level `docs/` folders (for example, `statement_generator/docs/`).
- If new docs are created, link them from `docs/INDEX.md` and `docs/CHANGELOG.md`.

### Change Notes

- Record completed work in `docs/CHANGELOG.md` with a date heading.
- Keep notes in plain text (no checkboxes or TODO items).
- Link to supporting reports when they exist.

### Filename Conventions

- **ALL_CAPS.md** - Major documents (CLAUDE.md, README.md, CHANGELOG.md)
- **Sentence_Case.md** - Regular documents (most reference docs)
- **PHASE_X_*.md** - Phase-specific documents
- **YYYY-MM-DD_*.md** - Dated archives (when multiple versions exist)

### Content Structure

All technical documents should include:
1. **Title** - Clear, descriptive
2. **Last Updated** - Date of last significant change
3. **Purpose/Overview** - What this document covers
4. **Table of Contents** - For documents >100 lines
5. **Main Content** - Organized with clear headings
6. **References** - Links to related docs
7. **Changelog Section** - For frequently updated docs (optional)

### Code Examples

- **Always test** code examples before committing
- **Use actual paths** from the repository
- **Include expected output** when helpful
- **Add comments** to explain non-obvious steps

### Cross-References

- **Use relative paths** for documentation links
- **Prefer markdown links** over raw URLs
- **Link to specific sections** with anchors when relevant
- **Keep links up to date** when moving files

---

## Automation Opportunities

### Scripts to Consider

1. **Module count checker**:
   ```bash # scripts/check-module-docs.sh # Verify module counts in CLAUDE.md match actual codebase ```

2. **Link validator**: ```bash # scripts/validate-doc-links.sh # Check all documentation links are valid ```

3. **Timestamp updater**: ```bash # scripts/update-timestamps.sh # Update "Last Updated" when files change ```

4. **CLI docs generator**:
   ```bash # scripts/generate-cli-docs.sh # Auto-generate command reference from --help output ```

---

## Troubleshooting Documentation Issues

### Documentation is Outdated

**Symptoms**:
- Commands don't match actual CLI
- Module counts wrong
- Examples don't work

**Solution**:
1. Run verification procedures above
2. Update affected documents
3. Add entry to CHANGELOG.md
4. Consider automating the check

### Documentation is Scattered

**Symptoms**:
- Same information in multiple places
- Hard to find authoritative source
- Conflicting information

**Solution**:
1. Identify authoritative source
2. Consolidate information there
3. Add cross-references from other locations
4. Archive outdated duplicates

### Documentation is Overwhelming

**Symptoms**:
- Too many files
- Hard to navigate
- Unclear where to start

**Solution**:
1. Review INDEX.md structure
2. Create "Start Here" section
3. Archive historical documents
4. Simplify navigation paths

---

## Success Criteria

Documentation is well-maintained when:

✅ **Accurate**: Code examples work, commands match CLI ✅ **Current**: "Last Updated" timestamps within 3 months for
active docs ✅ **Complete**: All modules, commands, and features documented ✅ **Organized**: Easy to find information via
INDEX.md ✅ **Consistent**: Follows naming and structure conventions ✅ **Synchronized**: Updates happen with code
changes, not retroactively ✅ **Historical**: Archive preserves context for debugging ✅ **Navigable**: Clear paths from
README to detailed docs

---

## Questions?

If documentation maintenance becomes unclear:
1. Consult this guide first
2. Check CHANGELOG.md for precedents
3. Review INDEX.md for structure
4. Ask: "Will this help future contributors?"

---

**Maintained By**: Documentation system as part of codebase **Review Frequency**: Monthly during active development,
quarterly during maintenance **Next Review**: January 27, 2026 (1 month from last update)
