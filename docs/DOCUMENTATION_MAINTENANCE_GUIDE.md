# Documentation Maintenance Guide

**Purpose**: Ensure documentation stays synchronized with codebase changes
**Last Updated**: January 20, 2026

---

## Related Documentation

**For AI assistants and Claude Code**: See **[DOCUMENTATION_POLICY.md](DOCUMENTATION_POLICY.md)** for comprehensive documentation lifecycle policies, including:
- When to create vs update documentation (decision tree)
- Documentation categories and lifecycle (Living, Versioned, Immutable, Temporary, Archive)
- Phase documentation patterns
- Mandatory INDEX.md linking requirements

**This guide** focuses on human maintenance workflows, verification procedures, and review schedules.

---

## Overview

This guide establishes a systematic approach to keeping documentation aligned with code as the project evolves. The goal
is to prevent documentation drift while maintaining historical context for debugging and understanding past decisions.

---

## Documentation Structure

### Project-Level Docs (Global)
```
docs/
├── INDEX.md                             # Navigation guide (UPDATE ON STRUCTURE CHANGES)
├── PROJECT_OVERVIEW.md                  # Project overview (KEEP CURRENT)
├── QUICKSTART.md                        # Command reference (UPDATE ON CLI CHANGES)
├── DOCUMENTATION_POLICY.md              # Documentation lifecycle rules
├── DOCUMENTATION_MAINTENANCE_GUIDE.md   # This file
└── architecture/                        # System design
    └── PROJECT_ORGANIZATION.md
```

### Component Docs (Owned by Each Module)
```
extractor/docs/                          # Rust extractor documentation
└── INDEX.md                              # Entry point for extractor docs

statement_generator/docs/                # Statement generator documentation
└── INDEX.md                              # Entry point for statement generator docs

anking_analysis/docs/                    # Anking analysis documentation
```

See each component INDEX.md for detailed file lists.

---

## Maintenance Triggers

### When to Update Documentation

| Code Change | Documentation to Update | Priority |
|-------------|------------------------|----------|
| **Add new module** | CLAUDE.md, docs/architecture/PROJECT_ORGANIZATION.md, <component>/docs/INDEX.md | HIGH |
| **Remove module** | CLAUDE.md, docs/architecture/PROJECT_ORGANIZATION.md, <component>/docs/INDEX.md | HIGH |
| **Refactor module** | Relevant component docs (e.g., extractor/docs/EXTRACTOR_MANUAL.md) | MEDIUM |
| **Add CLI command** | CLAUDE.md, docs/QUICKSTART.md, component guide (extractor/docs/EXTRACTOR_MANUAL.md or statement_generator/docs/STATEMENT_GENERATOR.md) | HIGH |
| **Remove CLI command** | CLAUDE.md, docs/QUICKSTART.md, component guide | HIGH |
| **Change CLI arguments** | docs/QUICKSTART.md, component guide | MEDIUM |
| **Add dependency** | CLAUDE.md (Technology Stack section), component guide | MEDIUM |
| **Remove dependency** | CLAUDE.md, component guide | MEDIUM |
| **Fix bug** | extractor/docs/TROUBLESHOOTING.md if pattern is reusable | LOW |
| **Add feature** | Relevant component guide + component INDEX.md | MEDIUM |
| **API changes** | extractor/docs/EXTRACTOR_MANUAL.md if new patterns found | MEDIUM |
| **Pipeline changes** | docs/architecture/PROJECT_ORGANIZATION.md + relevant component guide | HIGH |
| **Complete phase** | Create <component>/docs/PHASE_X_COMPLETION_REPORT.md, update <component>/docs/PHASE_X_STATUS.md and TODO.md | HIGH |
| **Start new phase** | Create <component>/docs/PHASE_X_STATUS.md, update TODO.md | HIGH |

---

## Documentation Update Checklist

### For Module Changes

When adding/removing/refactoring modules:

1. **Update CLAUDE.md**:
   - [ ] Module organization section
   - [ ] Line count totals
   - [ ] Module descriptions
   - [ ] Update "Last Updated" timestamp

2. **Update docs/architecture/PROJECT_ORGANIZATION.md**:
   - [ ] Module descriptions
   - [ ] Data flow diagrams
   - [ ] File structure examples

3. **Update the relevant component manual** (e.g., extractor/docs/EXTRACTOR_MANUAL.md):
   - [ ] Module descriptions
   - [ ] Data flow diagrams
   - [ ] File structure examples


### For CLI Changes

When adding/removing/changing CLI commands:

1. **Update CLAUDE.md**:
   - [ ] Common Commands section
   - [ ] Add/remove command examples
   - [ ] Update command descriptions

2. **Update docs/QUICKSTART.md**:
   - [ ] Add/remove command
   - [ ] Update arguments if changed

3. **Update the component guide** (extractor/docs/EXTRACTOR_MANUAL.md or statement_generator/docs/STATEMENT_GENERATOR.md):
   - [ ] Detailed command documentation
   - [ ] Examples and use cases


### For Architectural Changes

When changing system architecture:

1. **Update docs/architecture/PROJECT_ORGANIZATION.md**:
   - [ ] Pipeline diagrams
   - [ ] Component descriptions
   - [ ] Data flow explanations

2. **Update the relevant component manual** (e.g., extractor/docs/EXTRACTOR_MANUAL.md):
   - [ ] Technical implementation details
   - [ ] Module interactions
   - [ ] Design decisions

3. **Update CLAUDE.md**:
   - [ ] Project Architecture section
   - [ ] Reflect new design


---

## Version Control Policy

Documentation history is tracked in git. We do not keep local changelogs or archives.

**When documentation becomes obsolete:**
1. Remove the outdated doc.
2. Update references (INDEX, README, TODO, CLAUDE) to point at the current source.
3. Note the change in the commit message or PR description.

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
- [ ] Clean up outdated troubleshooting entries

**Per Phase**:
- [ ] Before phase start: Create PHASE_X_STATUS.md
- [ ] During phase: Update progress in status and TODO.md
- [ ] After phase: Create PHASE_X_COMPLETION_REPORT.md

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
for dir in docs extractor/docs statement_generator/docs; do
  (cd "$dir" && rg -n "\\]\\([^)]*\\.md\\)" .)
done
# Manually verify links are valid

# 4. Verify "Last Updated" timestamps are recent
rg -n "Last Updated" docs/**/*.md extractor/docs/**/*.md statement_generator/docs/**/*.md
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

5. **Scope review**:
   - [ ] Identify outdated documents
   - [ ] Remove anything no longer needed
   - [ ] Update INDEX.md

---

## Special Cases

### Handling Breaking Changes

When code changes break documented workflows:

1. **Before commit**:
   - [ ] Update all affected documentation
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
3. **Document fully** only when feature is release-ready

### Handling Deprecated Features

When deprecating code:

1. **Mark as deprecated** in documentation (add "⚠️ Deprecated" tag)
2. **Keep documentation** until feature is removed
3. **After removal**:
   - [ ] Remove from main documentation

---

## Documentation Standards

### Scope and Exclusions

- Legacy style guidance lives in `statement_generator/docs/LEGACY_STATEMENT_STYLE_GUIDE.md`.
- No documentation subfolders are excluded from validation.

### Documentation Placement (Claude/Codex)

**Note**: For comprehensive AI documentation policies, see [DOCUMENTATION_POLICY.md](DOCUMENTATION_POLICY.md).

**Quick rules**:
- Project-level documentation lives under `docs/`.
- Component-specific documentation lives under `<component>/docs/` (e.g., `extractor/docs/`, `statement_generator/docs/`).
- If you generate docs while working in a module, save them into that module's `docs/` folder.
- If tooling writes docs into the wrong location, move them into the owning component's `docs/` folder before committing.
- If new docs are created, link them from the appropriate INDEX.md (global or component).
- Temporary artifacts go in `statement_generator/artifacts/` (not `docs/`).

See [DOCUMENTATION_POLICY.md](DOCUMENTATION_POLICY.md) for detailed guidance on update-first policy, documentation categories, and lifecycle management.

### Change Tracking (Git)

- Rely on git history for documentation changes.
- Use clear commit messages describing what changed and why.
- Remove obsolete documents instead of archiving them locally.

### Filename Conventions

- **ALL_CAPS.md** - Major documents (CLAUDE.md, README.md)
- **Sentence_Case.md** - Regular documents (most reference docs)
- **PHASE_X_*.md** - Phase-specific documents

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
3. Consider automating the check

### Documentation is Scattered

**Symptoms**:
- Same information in multiple places
- Hard to find authoritative source
- Conflicting information

**Solution**:
1. Identify authoritative source
2. Consolidate information there
3. Add cross-references from other locations
4. Remove outdated duplicates

### Documentation is Overwhelming

**Symptoms**:
- Too many files
- Hard to navigate
- Unclear where to start

**Solution**:
1. Review INDEX.md structure
2. Create "Start Here" section
3. Simplify navigation paths

---

## Success Criteria

Documentation is well-maintained when:

✅ **Accurate**: Code examples work, commands match CLI ✅ **Current**: "Last Updated" timestamps within 3 months for
active docs ✅ **Complete**: All modules, commands, and features documented ✅ **Organized**: Easy to find information via
INDEX.md ✅ **Consistent**: Follows naming and structure conventions ✅ **Synchronized**: Updates happen with code
changes, not retroactively ✅ **Lean**: Only current docs retained; history in git ✅ **Navigable**: Clear paths from
README to detailed docs

---

## Questions?

If documentation maintenance becomes unclear:
1. Consult this guide first
2. Check git history for recent documentation changes
3. Review INDEX.md for structure
4. Ask: "Will this help future contributors?"

---

**Maintained By**: Documentation system as part of codebase **Review Frequency**: Monthly during active development,
quarterly during maintenance **Next Review**: January 27, 2026 (1 month from last update)
