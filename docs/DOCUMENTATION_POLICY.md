# Documentation Lifecycle and Organization Policy

**Created**: January 19, 2026
**Last Updated**: January 20, 2026
**Purpose**: Establish clear documentation creation, organization, and update policies to prevent documentation bloat and ensure maintainability
**Audience**: Claude Code, AI assistants, and human maintainers

## Overview

This policy defines when to create new documentation versus updating existing files, how to organize documentation by lifecycle, and how to maintain documentation health over time.

**Key Principles**:
1. **Update-first**: Default to updating existing documentation rather than creating new files
2. **Clear lifecycle**: Every document has a defined category (Living, Versioned, Immutable, Temporary, Archive)
3. **Mandatory linking**: Project-level docs are linked from docs/INDEX.md; component docs are linked from their component INDEX.md
4. **Automated validation**: Health checks catch documentation drift
5. **Temporary artifact cleanup**: Regular review and cleanup of temporary files

## When to Create New Documentation

Use this decision tree:

```
Are you documenting a new phase?
├─ YES → Create <component>/docs/PHASE_X_STATUS.md + link from <component>/docs/INDEX.md
└─ NO
   └─ Are you documenting a new major feature/component?
      ├─ YES → Create <component>/docs/FEATURE_NAME.md + link from <component>/docs/INDEX.md
      └─ NO
         └─ Are you creating temporary analysis/evaluation?
            ├─ YES → Create in statement_generator/artifacts/ (do not link from INDEX.md)
            └─ NO → **UPDATE EXISTING DOCUMENTATION**
```

**Examples**:
- ❌ "Phase 3 is ready" → Update existing statement_generator/docs/PHASE_3_STATUS.md, don't create PHASE3_QUICK_START.md
- ✅ "Phase 4 starts" → Create new statement_generator/docs/PHASE_4_STATUS.md
- ❌ "Validation implementation details" → Update statement_generator/docs/VALIDATION_IMPLEMENTATION.md, don't create new standalone files
- ✅ "Phase 3 evaluation results" → Create statement_generator/artifacts/phase3_evaluation/evaluation_report.md (temporary)

## Documentation Categories

| Category | Lifecycle | Location | Examples | Last Updated Policy |
|----------|-----------|----------|----------|---------------------|
| **Living** | Continuously updated | `docs/` (project) or `<component>/docs/` | PHASE_X_STATUS.md, TODO.md, TROUBLESHOOTING.md | Update timestamp on every significant change |
| **Versioned** | One per phase/version | `<component>/docs/` | PHASE4_DEPLOYMENT_PLAN.md, 2026-01-16-phase3-llm-integration-evaluation.md | Create new file per version, move old to archive |
| **Immutable** | Written once, never edited | `<component>/docs/` | PHASE_X_COMPLETION_REPORT.md | Do not update after finalization |
| **Temporary** | Deleted or promoted | `statement_generator/artifacts/` | evaluation_report.md, test_results.json | Review monthly, promote or delete |
| **Archive** | Historical reference | `<component>/docs/archive/` | Phase 1-only docs moved after phase completion | Mark with ⚪ Archive badge in INDEX.md |

### Category Details

#### Living Documents
**Purpose**: Continuously evolving documentation that changes throughout development

**Characteristics**:
- Updated frequently as project evolves
- Always reflects current state
- "Last Updated" timestamp required
- Examples: PHASE_X_STATUS.md, TODO.md, TROUBLESHOOTING.md, VALIDATION.md

**Update Policy**:
- Update timestamp on every significant change
- Add new sections for new information
- Overwrite outdated sections (git preserves history)
- Split into multiple files only if >500 lines and logical boundaries exist

#### Versioned Documents
**Purpose**: Plans and designs that evolve per phase or major version

**Characteristics**:
- One file per phase/version
- Date-stamped filename (YYYY-MM-DD-description.md)
- Previous versions moved to archive
- Examples: PHASE4_DEPLOYMENT_PLAN.md, phase3-evaluation-plan.md

**Update Policy**:
- Create new file for each version/phase
- Move superseded versions to `<component>/docs/archive/phaseX/`
- Link current version from <component>/docs/INDEX.md with 🟢 Active badge
- Link archived versions from <component>/docs/INDEX.md with ⚪ Archive badge

#### Immutable Archives
**Purpose**: Final reports that capture completed work and should never be edited

**Characteristics**:
- Written once after phase/milestone completion
- Never edited (corrections go in errata or new docs)
- Permanent historical record
- Examples: PHASE_1_COMPLETION_REPORT.md, PHASE_3_COMPLETION_REPORT.md

**Update Policy**:
- Do not edit after finalization
- If corrections needed, create errata document or note in current phase status
- Always linked from <component>/docs/INDEX.md with 🟡 Reference badge

#### Temporary Documents
**Purpose**: Work-in-progress analysis, evaluation results, or temporary notes

**Characteristics**:
- Short lifespan (≤30 days unless explicitly noted)
- Not linked from INDEX.md
- Stored in `statement_generator/artifacts/`
- Examples: evaluation logs, intermediate analysis, test results

**Update Policy**:
- Monthly review for files >30 days old
- **Promote** significant findings to permanent docs
- **Delete** temporary analysis and intermediate results
- **Archive** final reports if phase complete

#### Archive Documents
**Purpose**: Historical documentation no longer relevant to current development

**Characteristics**:
- Phase-specific docs after phase completion
- Superseded designs or approaches
- Stored in `<component>/docs/archive/phaseX/`
- Examples: RUST_SETUP.md (Phase 1 only), old deployment plans

**Update Policy**:
- Mark with ⚪ Archive badge in INDEX.md
- Link from "Archives" section of INDEX.md
- Do not update content
- Include note explaining why archived ("Phase 1 only", "Superseded by X")

## Update-First Policy

**Default behavior**: Update existing documentation rather than creating new files.

### Before Creating a New Document

Ask these questions in order:

1. **Does a document already cover this topic?**
   - YES → Update that document
   - NO → Continue to step 2

2. **Is this a new phase, major feature, or architectural component?**
   - YES → Create new document in `<component>/docs/` + link from `<component>/docs/INDEX.md`
   - NO → Continue to step 3

3. **Is this temporary analysis or evaluation?**
   - YES → Create in `statement_generator/artifacts/` (no INDEX.md link)
   - NO → Update existing reference docs

### When to Update vs Create

| Scenario | Action | Rationale |
|----------|--------|-----------|
| Phase 3 progress update | Update statement_generator/docs/PHASE_3_STATUS.md | Living document, continuous updates |
| Phase 4 begins | Create statement_generator/docs/PHASE_4_STATUS.md | New phase = new document |
| Validation improvements | Update extractor/docs/VALIDATION.md or statement_generator/docs/VALIDATION_IMPLEMENTATION.md | Existing feature enhancement |
| New NLP component | Create statement_generator/docs/NLP_COMPONENT.md | New major component |
| Evaluation results | Create artifacts/eval_report.md | Temporary analysis |
| Quick start instructions | Update docs/QUICKSTART.md or component guide | Don't duplicate phase docs |
| Bug fix documentation | Update extractor/docs/TROUBLESHOOTING.md (if extractor-related) | Existing troubleshooting resource |

### Update Strategy for Living Documents

When updating existing documentation:

1. **Add new section** for new information
2. **Update existing sections** if information has changed
3. **Add "Last Updated" note** with date and change summary
4. **Keep focused**: If document grows beyond 500 lines, consider splitting by logical boundaries
5. **Overwrite outdated content**: Git history preserves all changes

Example update:
```markdown
> **Last Updated**: 2026-01-19
> **Recent Changes**: Added NLP integration details, updated validation pass rates
```

## Phase Documentation Pattern

Every project phase follows this standard structure:

### Before Phase Starts

1. **Create `<component>/docs/PHASE_X_STATUS.md`** (living document)
   - Current status, goals, priorities
   - Link to relevant plans and specs
   - Updated continuously during phase
   - Template:
     ```markdown
     # Phase X Status

     > **Last Updated**: YYYY-MM-DD
     > **Status**: 🟢 Active

     ## Overview
     [Phase description and goals]

     ## Current Progress
     [What's done, what's in progress]

     ## Next Steps
     [Immediate priorities]

     ## Related Documentation
     - [Phase X Plan](phaseX/PHASEX_PLAN.md)
     - [Phase X Specification](specifications/phase_x_spec.md)
     ```

2. **Create `<component>/docs/phaseX/YYYY-MM-DD-phase-X-plan-name.md`** (versioned document)
   - Detailed implementation plan
   - One plan per major approach or iteration
   - Date-stamped filename for clear versioning

3. **Link both from `<component>/docs/INDEX.md`**
   - Add to appropriate sections
   - Use 🟢 Active badge
   - Link from `docs/INDEX.md` if it's a project-wide milestone

### During Phase

1. **Update `PHASE_X_STATUS.md`** with progress (living document)
   - Regular updates as work progresses
   - Track completed milestones
   - Note blockers and challenges

2. **Create temporary artifacts** in `statement_generator/artifacts/phaseX_*/`
   - Evaluation results
   - Test logs
   - Analysis documents
   - **Do not link from INDEX.md**

3. **Update TODO.md** with phase-specific tasks
   - Track active work items
   - Remove completed tasks

### After Phase Completes

1. **Create `<component>/docs/PHASE_X_COMPLETION_REPORT.md`** (immutable archive)
   - Final metrics, results, lessons learned
   - Never edited after creation
   - Template:
     ```markdown
     # Phase X Completion Report

     **Completed**: YYYY-MM-DD
     **Duration**: X weeks/months

     ## Summary
     [High-level accomplishments]

     ## Metrics
     [Quantitative results]

     ## Lessons Learned
     [What worked, what didn't]

     ## Next Phase Preview
     [Transition to Phase X+1]
     ```

2. **Update `PHASE_X_STATUS.md` one final time**
   - Add "Status: 🟡 COMPLETE ✅" at top
   - Add link to completion report
   - Change `<component>/docs/INDEX.md` badge to 🟡 Reference

3. **Review temporary artifacts**
   - Promote important findings to permanent docs
   - Delete or archive remaining temporary files
   - Move final reports to <component>/docs/ if needed

4. **Update project status**
   - CLAUDE.md current status section
   - README.md project status
   - docs/INDEX.md project status (plus component INDEX.md if phase-specific)

5. **Archive phase-specific docs** (if needed)
   - Move superseded plans to `<component>/docs/archive/phaseX/`
   - Update <component>/docs/INDEX.md to link from Archives section

## Temporary Documentation Handling

**Temporary artifacts** are analysis, evaluation results, or work-in-progress documents that are NOT permanent reference material.

### Storage Location
`statement_generator/artifacts/`

### Do NOT
- Link from docs/INDEX.md or component INDEX.md files
- Reference from CLAUDE.md (except final reports promoted to permanent)
- Create temporary docs in `docs/` or `<component>/docs/`

### Monthly Review Process

**Schedule**: First Monday of each month during active development

**Steps**:
1. **Identify** artifacts older than 30 days:
   ```bash
   find statement_generator/artifacts -type f -mtime +30
   ```

2. **Promote** significant findings to permanent docs:
   - Important evaluation results → `<component>/docs/`
   - Key technical decisions → Update relevant feature docs
   - Performance benchmarks → Add to completion report or status doc

3. **Delete** temporary analysis:
   - Intermediate results
   - Debug logs
   - Test runs
   - Work-in-progress notes

4. **Archive** final evaluation reports:
   - Move to `<component>/docs/` if phase complete
   - Link from phase completion report
   - Update <component>/docs/INDEX.md (and docs/INDEX.md if project-level)

### Example: Phase 3 Evaluation Artifacts

**During Phase 3**:
- `artifacts/phase3_evaluation/test_questions.md` (temporary - test data)
- `artifacts/phase3_evaluation/evaluation_log.txt` (temporary - debug output)
- `artifacts/phase3_evaluation/results.json` (temporary - raw results)
- `artifacts/phase3_evaluation/PHASE3_COMPLETE_FINAL_REPORT.md` (temporary, but will be promoted)

**After Phase 3 Completion**:
- ✅ Promoted `PHASE3_COMPLETE_FINAL_REPORT.md` → permanent doc, linked from PHASE_3_STATUS.md
- ❌ Deleted `test_questions.md`, `evaluation_log.txt`, `results.json`
- ✅ Updated PHASE_3_STATUS.md with key findings

## Mandatory INDEX.md Linking

**Rule**: Every new permanent document MUST be linked from the appropriate INDEX.md (docs/INDEX.md for project-level, or <component>/docs/INDEX.md for component docs) at creation time.

### Process

1. **Create new document** in `docs/` (project-level) or `<component>/docs/` (component-level)
2. **Immediately add link** to the relevant INDEX.md (global or component) in the correct category
3. **Add status badge** (🟢 Active, 🟡 Reference, ⚪ Archive)
4. **Update INDEX.md** "Last Updated" timestamp for the index you changed

### Link Format

```markdown
- 🟢 **[DOCUMENT_NAME.md](path/to/DOCUMENT_NAME.md)** - Brief description (Last Updated: YYYY-MM-DD)
```

### Status Badges

| Badge | Status | Meaning |
|-------|--------|---------|
| 🟢 | Active | Actively maintained, current phase/feature |
| 🟡 | Reference | Completed work, not actively updated |
| ⚪ | Archive | Historical only, phase-specific or superseded |

### INDEX.md Categories

Documents should be linked from appropriate sections:

- **Start Here** - Quick links for new users and AI assistants
- **Core Project Docs** - Overview, status, scope, roadmap
- **Architecture & Design** - System architecture and design decisions
- **Phase-Specific Reference** - PHASE_X_STATUS.md and completion reports
- **Technical Reference** - Feature-specific documentation
- **Specifications** - Detailed technical specifications
- **Plans & Roadmaps** - Implementation plans and strategies
- **Archives** - Superseded and phase-specific historical docs

### Orphaned Document Detection

Automated validation checks for documents not linked from INDEX.md:

```bash
./scripts/validate-docs.sh
```

Any orphaned documents should either be:
1. Linked from the appropriate INDEX.md, or
2. Moved to `statement_generator/artifacts/` (if temporary), or
3. Deleted (if no longer needed)

## Documentation Health Checks

### Monthly Review (During Active Development)

**Schedule**: First Monday of each month

**Checklist**:
- [ ] Run link validation script: `./scripts/validate-docs.sh`
- [ ] Check "Last Updated" timestamps (active docs should be within 30 days)
- [ ] Review `statement_generator/artifacts/` for stale files (>30 days)
- [ ] Verify TODO.md references valid documentation
- [ ] Scan for orphaned documents (not linked from INDEX.md)
- [ ] Update project status in CLAUDE.md if phase changed

**Actions**:
- Fix broken links
- Update stale documents or mark as archive
- Clean up temporary artifacts
- Link orphaned documents or delete them

### Per Phase Completion

**Checklist**:
- [ ] Create immutable completion report (`PHASE_X_COMPLETION_REPORT.md`)
- [ ] Update phase status document to "COMPLETE" with link to report
- [ ] Move superseded plans to `<component>/docs/archive/phaseX/`
- [ ] Review and clean up temporary artifacts
- [ ] Update CLAUDE.md project status section
- [ ] Update README.md project status (if exists)
- [ ] Update docs/INDEX.md project status (and component INDEX.md if phase-specific)

**Example Phase Completion**:
```markdown
# Phase 3 Status

> **Status**: 🟡 COMPLETE ✅ (Completed: January 16, 2026)
> **Completion Report**: [PHASE_3_COMPLETION_REPORT.md](PHASE_3_COMPLETION_REPORT.md)

[Rest of status document remains for reference]
```

### Automated Validation Script

**Location**: `scripts/validate-docs.sh`

**Purpose**: Automated health checks for documentation integrity

**Usage**:
```bash
# Run all checks
./scripts/validate-docs.sh

# Run in CI/CD
./scripts/validate-docs.sh && echo "Docs validated" || exit 1
```

**Checks Performed**:
1. **Broken Internal Links** - Verify all markdown links point to existing files
2. **Orphaned Documents** - Find docs not linked from INDEX.md
3. **Stale Artifacts** - Warn about files >30 days in artifacts/

See script source for implementation details.

## Examples and Anti-Patterns

### ✅ Good Practices

**Example 1: Phase Progress Update**
```
Scenario: Phase 3 validation pass rate improved from 85% to 92%
Action: Update statement_generator/docs/PHASE_3_STATUS.md with new metrics
Rationale: Living document, reflects current state
```

**Example 2: New Feature Documentation**
```
Scenario: Implemented new NLP caching layer
Action: Update <component>/docs/VALIDATION.md with new section
Rationale: Enhancement to existing feature, not new component
```

**Example 3: Temporary Evaluation**
```
Scenario: Running test evaluation on 10 questions
Action: Create artifacts/phase3_eval/test_run_2026-01-19.md
Rationale: Temporary analysis, not permanent reference
```

**Example 4: Phase Transition**
```
Scenario: Phase 3 complete, starting Phase 4
Actions:
1. Create statement_generator/docs/PHASE_3_COMPLETION_REPORT.md
2. Update statement_generator/docs/PHASE_3_STATUS.md with completion status
3. Create statement_generator/docs/PHASE_4_STATUS.md
4. Update CLAUDE.md and the relevant INDEX.md files
Rationale: Proper phase lifecycle management
```

### ❌ Anti-Patterns

**Anti-Pattern 1: Duplicate Quick Starts**
```
❌ Creating PHASE3_QUICK_START.md when PHASE_3_STATUS.md exists
✅ Add "Quick Start" section to PHASE_3_STATUS.md
```

**Anti-Pattern 2: Implementation Notes in Wrong Location**
```
❌ Creating statement_generator/VALIDATION_IMPLEMENTATION.md (outside docs/)
✅ Update statement_generator/docs/VALIDATION_IMPLEMENTATION.md
```

**Anti-Pattern 3: Editing Immutable Reports**
```
❌ Updating PHASE_1_COMPLETION_REPORT.md with corrections
✅ Add errata note to statement_generator/docs/PHASE_2_STATUS.md or create separate errata doc
```

**Anti-Pattern 4: Forgetting to Link New Docs**
```
❌ Creating <component>/docs/NEW_FEATURE.md without updating the component INDEX.md
✅ Create NEW_FEATURE.md AND add link to the component INDEX.md immediately
```

**Anti-Pattern 5: Permanent Docs in Artifacts**
```
❌ Creating comprehensive feature docs in artifacts/
✅ Create in <component>/docs/ and link from the component INDEX.md
```

## Tools and Automation

### Validation Script

**File**: `scripts/validate-docs.sh`

**Exit Codes**:
- `0` - All checks passed
- `1` - One or more checks failed

**Output**: Color-coded report with pass/fail summary

### Manual Checks

**Find documents not linked from INDEX.md**:
```bash
# Project-level docs
comm -23 \
  <(find docs -name "*.md" ! -name "INDEX.md" | sort) \
  <(grep -o 'docs/[^)]*\.md' docs/INDEX.md | sort | uniq)

# Component docs (run from each component's docs/ folder, then review output)
cd extractor/docs
comm -23 <(find . -name "*.md" ! -name "INDEX.md" | sort) <(grep -o '\\([^)]*\\.md\\)' INDEX.md | sort | uniq)

cd ../../statement_generator/docs
comm -23 <(find . -name "*.md" ! -name "INDEX.md" | sort) <(grep -o '\\([^)]*\\.md\\)' INDEX.md | sort | uniq)
```

**Find stale artifacts**:
```bash
find statement_generator/artifacts -type f -mtime +30 -ls
```

**Check for broken markdown links**:
```bash
cd docs
for file in $(find . -name "*.md"); do
  grep -o '\[.*\]([^)]*\.md)' "$file" | \
  sed 's/.*(\(.*\))/\1/' | \
  while read link; do
    if [ ! -f "$link" ]; then
      echo "Broken link in $file: $link"
    fi
  done
done
```

## Summary

This policy ensures documentation remains:
- **Organized** - Clear categories and lifecycle rules
- **Discoverable** - All permanent docs linked from INDEX.md
- **Current** - Regular health checks and updates
- **Maintainable** - Automated validation and cleanup processes

**Key Takeaways**:
1. Update existing docs by default
2. Follow phase documentation pattern
3. Link all permanent docs from INDEX.md
4. Clean up temporary artifacts monthly
5. Run validation script regularly

**Questions or Clarifications**: See [DOCUMENTATION_MAINTENANCE_GUIDE.md](DOCUMENTATION_MAINTENANCE_GUIDE.md) for human maintenance workflows or consult CLAUDE.md for project context.
