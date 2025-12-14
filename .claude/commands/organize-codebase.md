# /organize-codebase - Automatic Codebase Organizer

## Purpose

Automatically organize files in the MKSAP codebase according to organization rules. Moves misplaced files to correct locations, updates import paths and documentation links.

## Usage

```bash
/organize-codebase                     # Dry run - show what would change
/organize-codebase --execute           # Actually move files and update paths
/organize-codebase --check             # Just validate, no changes
/organize-codebase --scope docs        # Only organize documentation
/organize-codebase --scope commands    # Only organize commands
```

## Implementation

This command scans the codebase against `.claude/organization-rules.json` and:

1. **Identifies Misplaced Files**:
   - Finds `.md` files not in `docs/` subdirectories
   - Finds commands not in `.claude/commands/`
   - Finds skills not in `.claude/skills/`
   - Flags files in wrong locations

2. **Moves Files**:
   - Copies files to correct locations
   - Updates relative paths automatically
   - Updates documentation links
   - Removes originals

3. **Updates References**:
   - Scans all `.md` files for broken links
   - Updates documentation cross-references
   - Regenerates navigation files (INDEX.md)

4. **Validates Results**:
   - Verifies files moved successfully
   - Checks all links still work
   - Confirms imports are valid

## Organization Rules

Files are organized according to patterns and destinations defined in `.claude/organization-rules.json`:

**Documentation**:
- Pattern: `**/*.md`
- Excluded: `node_modules/`, `scraper/src/`
- Destinations:
  - Project-level → `docs/project/`
  - Architecture → `docs/architecture/`
  - Scraper-specific → `docs/scraper/`
  - Format specs → `docs/specifications/`
  - Examples → `docs/examples/`
  - Legacy → `docs/legacy/`

**Commands**:
- Pattern: `.claude/commands/**/*.md`
- Enforcement: Strict (must be in `.claude/commands/`)

**Skills**:
- Pattern: `.claude/skills/**/*`
- Enforcement: Strict (must be in `.claude/skills/`)

**Implementation Code**:
- Skills: Must stay in `scraper/src/skills/` (tightly coupled)
- Agents: Must stay in `scraper/src/agents/` (tightly coupled)

## Output Example

```
Codebase Organization Report
=============================

Dry Run Mode - No changes made

📂 Files to Move (3):
  1. /docs/OLD_README.md → /docs/project/README.md
  2. /scraper/GUIDE.md → /docs/scraper/GUIDE.md
  3. /.claude/test-command.md → /.claude/commands/test-command.md

🔗 Links to Update (12):
  1. .claude/README.md:15 - Update path to docs/project/
  2. docs/project/INDEX.md:23 - Update path reference
  ... (10 more)

✅ Validation Ready
  - All moves are valid
  - No circular references
  - No conflicts detected

Run with --execute to apply changes
```

## Safety Features

- **Dry Run Mode**: Always preview changes before executing
- **Backups**: Git state is saved before changes
- **Verification**: All changes are validated after execution
- **Rollback**: Git can revert if issues found

## Related Commands

- `/validate-structure` - Check organization compliance
- `/update-docs` - Update documentation links
- `/sync-imports` - Fix broken imports

## See Also

- `.claude/organization-rules.json` - Rules engine
- `.claude/README.md` - Claude Code integration guide
- `/docs/project/INDEX.md` - Documentation index
