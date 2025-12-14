# /update-docs - Documentation Updater

## Purpose

Automatically update documentation when files are moved or modified. Fixes broken links, updates path references, and regenerates navigation files.

## Usage

```bash
/update-docs                           # Update all documentation
/update-docs --check-links             # Just validate links
/update-docs --regenerate-nav          # Regenerate INDEX.md
/update-docs docs/project/             # Update specific directory
/update-docs docs/project/README.md    # Update specific file
/update-docs --verbose                 # Detailed output
```

## Implementation

This command:

1. **Scans Documentation**:
   - Finds all `.md` files in `docs/`
   - Identifies all internal links
   - Detects broken references

2. **Validates Links**:
   - Checks if linked files exist
   - Verifies relative paths are correct
   - Reports broken or outdated links

3. **Updates References**:
   - Fixes relative paths in links
   - Updates file path references in text
   - Corrects outdated documentation

4. **Regenerates Navigation**:
   - Updates `docs/project/INDEX.md`
   - Regenerates documentation tree
   - Updates "Quick Links" section
   - Refreshes table of contents

## Validation Checks

- **File Existence**: All linked files exist
- **Path Correctness**: Relative paths are accurate
- **Link Consistency**: Links use consistent format
- **Reference Accuracy**: All references point to correct locations

## Output Example

```
Documentation Update Report
=============================

🔍 Scanning Documentation (docs/)
  ├── project/ - 4 files
  ├── architecture/ - 2 files
  ├── scraper/ - 5 files
  ├── specifications/ - 1 file
  ├── examples/ - 1 file
  └── legacy/ - 1 file

🔗 Link Validation
  ✅ 127 internal links checked
  ✅ All links valid
  ⚠️  3 outdated path formats (will auto-fix)

📝 Updates Applied
  1. Updated 3 path references in INDEX.md
  2. Fixed 2 relative paths in QUICKSTART.md
  3. Regenerated navigation in INDEX.md

✅ Result: PASS
  All documentation is up-to-date
```

## Error Examples

```
Broken Links Found (3):
  1. docs/project/README.md:25
     Link: ../old-path/file.md
     Issue: File not found (moved to ../scraper/)
     Fix: Auto-update relative path

  2. docs/architecture/GUIDE.md:12
     Link: /CLAUDE.MD
     Issue: File moved to docs/legacy/CLAUDE_MCQ_FORMAT.md
     Fix: Update to relative path ../legacy/CLAUDE_MCQ_FORMAT.md
```

## Related Commands

- `/validate-structure` - Check organization compliance
- `/organize-codebase` - Move files and auto-update paths
- `/sync-imports` - Fix broken imports in code

## Integration

Should be run:
- After moving files (manually or with `/organize-codebase`)
- After creating new documentation
- After renaming files
- Weekly to catch any drift

## See Also

- `.claude/doc-standards.json` - Documentation standards
- `/docs/project/INDEX.md` - Main documentation index
- `.claude/README.md` - Claude Code integration
