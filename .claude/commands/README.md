# Claude Code Commands

All slash commands for the MKSAP project are documented here. These commands automate project organization, validation, and maintenance tasks.

## Available Commands

### `/validate-structure`
**Status**: ✅ Documented
**Purpose**: Validate codebase organization and compliance
**Usage**: `@claude /validate-structure`

Checks if the project follows organization rules. Validates:
- File placement and organization
- Documentation links
- Import paths
- Configuration consistency

See [validate-structure.md](validate-structure.md) for details.

### `/organize-codebase`
**Status**: ✅ Documented
**Purpose**: Automatically organize files
**Usage**: `@claude /organize-codebase --execute`

Moves misplaced files to correct locations and updates all references. Features:
- Dry-run mode (preview changes)
- Auto-update links and paths
- Validate results

See [organize-codebase.md](organize-codebase.md) for details.

### `/update-docs`
**Status**: ✅ Documented
**Purpose**: Update documentation links and structure
**Usage**: `@claude /update-docs`

Fixes broken documentation links and regenerates navigation. Includes:
- Link validation
- Path updates
- Navigation regeneration
- Table of contents updates

See [update-docs.md](update-docs.md) for details.

### `/sync-imports`
**Status**: ✅ Documented
**Purpose**: Fix broken imports in JavaScript files
**Usage**: `@claude /sync-imports --verify`

Detects and fixes broken import paths. Handles:
- ES6 imports and CommonJS requires
- Relative and absolute paths
- Import style preservation
- Syntax validation

See [sync-imports.md](sync-imports.md) for details.

## Command Categories

### Organization Automation
- `/organize-codebase` - Auto-organize files
- `/validate-structure` - Validate organization

### Documentation Maintenance
- `/update-docs` - Update documentation links
- `/validate-structure` - Check documentation structure

### Code Integrity
- `/sync-imports` - Fix broken imports
- `/validate-structure` - Validate imports

## Usage Pattern

1. Make changes (move files, create docs, refactor code)
2. Run `/validate-structure` to check status
3. If issues found:
   - Use `/organize-codebase` to auto-fix file placement
   - Use `/update-docs` to auto-fix documentation links
   - Use `/sync-imports` to auto-fix import paths
4. Run `/validate-structure` again to verify

## Organization Rules

Commands follow rules defined in `.claude/organization-rules.json`:

**Documentation**:
- All `.md` files belong in `docs/` subdirectories
- Subdivided by purpose:
  - `docs/project/` - Project-level docs
  - `docs/architecture/` - Architecture & design
  - `docs/scraper/` - Scraper-specific docs
  - `docs/specifications/` - Format specs
  - `docs/examples/` - Example files
  - `docs/legacy/` - Archived docs

**Commands**:
- All commands must be in `.claude/commands/`
- Must be documented with markdown files
- Must follow naming: lowercase-with-hyphens.md

**Skills**:
- All skills must be in `.claude/skills/`
- Must have skill.json configuration
- Must have instructions.md documentation

**Implementation Code**:
- Skills in `scraper/src/skills/` (tightly coupled, don't move)
- Agents in `scraper/src/agents/` (tightly coupled, don't move)
- Other code follows standard structure

## Documentation Standards

Commands are documented in `.claude/doc-standards.json`:

- Include Purpose section
- Document all Usage variations
- Explain Implementation details
- Provide Output examples
- List Related commands
- Include error examples

## Future Commands

Planned commands (not yet implemented):

- `/generate-new-command` - Template generator for new commands
- `/check-imports` - Code-specific import validation
- `/update-implementation` - Update generated code
- `/lint-docs` - Comprehensive documentation linting

## Integration

Commands can be integrated into:
- Pre-commit hooks (verify before commit)
- CI/CD pipelines (validate on PR)
- Development workflow (manual validation)
- Automated maintenance (scheduled checks)

## See Also

- `.claude/README.md` - Claude Code integration overview
- `.claude/organization-rules.json` - Organization rules
- `.claude/doc-standards.json` - Documentation standards
- `/docs/project/INDEX.md` - Documentation index
