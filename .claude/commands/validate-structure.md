# /validate-structure - Codebase Structure Validator

## Purpose

Check if the MKSAP codebase follows organization rules and standards. This command validates file placement, documentation links, import paths, and configuration consistency.

## Usage

```bash
/validate-structure                    # Full validation report
/validate-structure --docs             # Validate documentation only
/validate-structure --imports          # Validate import paths only
/validate-structure --files            # Validate file placement only
/validate-structure --links            # Validate documentation links only
/validate-structure --verbose          # Detailed output with line numbers
```

## Implementation

This is a slash command that can be called from Claude Code to validate the project structure.

### What It Checks

1. **File Organization**:
   - All `.md` files in correct locations (docs/ subdirectories)
   - No documentation scattered in root or scraper/
   - No files in wrong locations per `.claude/organization-rules.json`

2. **Documentation Links**:
   - All internal links are valid and point to existing files
   - Relative paths are correctly formatted
   - No broken links in markdown files

3. **Import Paths**:
   - All JavaScript imports reference existing files
   - No broken import chains
   - Correct relative path usage

4. **Configuration**:
   - Required files exist (.claude/README.md, .claude/settings.local.json, etc.)
   - Organization rules are defined
   - Documentation standards are enforced

5. **Claude Code Setup**:
   - `.claude/` directory has correct structure
   - Commands exist and are documented
   - Skills are properly configured

### Output Format

```
Codebase Structure Validation Report
====================================
Generated: 2025-12-13 21:45:00

📚 Documentation Organization
  ✅ All docs in docs/ directory
  ✅ Subdirectories correctly used
  ✅ No stray .md files found
  Result: PASS

🔗 Documentation Links
  ✅ 35/35 internal links valid
  ⚠️  2 external links (unchecked)
  Result: PASS

📂 File Organization
  ✅ All files in correct locations
  ✅ No misplaced files detected
  Result: PASS

💻 Import Paths
  ✅ All imports valid
  ✅ No broken import chains
  Result: PASS

⚙️  Configuration Files
  ✅ All required files present
  ✅ Configuration valid
  Result: PASS

🤖 Claude Code Setup
  ✅ .claude/ structure correct
  ✅ Commands documented
  ⚠️  Skills directory empty (expected - future use)
  Result: PASS

════════════════════════════════════════
Summary: 0 errors, 2 warnings
Status: PASS - Codebase well organized
```

### Error Examples

```
File Locations: 1 ERROR
  Found: /scraper/NEW_DOC.md
  Should be: docs/scraper/NEW_DOC.md
  Action: Move file or update organization rules

Import Paths: 2 WARNINGS
  File: docs/project/INDEX.md:45
  Issue: Link to ../scraper/SELECTOR_DISCOVERY.md (file moved - old path)
  Action: Run /update-docs to auto-fix, or manually update path

Link Validation: 3 ERRORS
  File: .claude/README.md:15
  Issue: Link to non-existent /docs/scraper/AI_FEATURES.md
  Action: Verify file location or update link
```

## Integration

This command should be called:
- After moving or creating new files
- Before committing changes to verify structure
- Periodically (weekly/monthly) to ensure ongoing compliance
- After significant refactoring

## Related Commands

- `/organize-codebase` - Auto-fix organization issues
- `/update-docs` - Update documentation links
- `/sync-imports` - Fix broken imports

## See Also

- `.claude/organization-rules.json` - Organization rules
- `.claude/doc-standards.json` - Documentation standards
- `/docs/project/INDEX.md` - Documentation index
