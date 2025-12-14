# Codebase Organizer Skill

## Purpose

The `codebase-organizer` skill provides AI-powered analysis of project structure and intelligent file organization. It analyzes file content and project context to suggest correct file locations according to organization rules.

## Capabilities

### 1. File Analysis

Analyzes individual files to determine:
- File type and purpose
- Most appropriate directory
- Whether file is in correct location
- Related files that should be nearby

**Usage:**
```javascript
const organizer = require('./.claude/skills/codebase-organizer');

const analysis = await organizer.analyzeFile('docs/some-file.md');
// Returns: {
//   filePath: 'docs/some-file.md',
//   fileType: 'markdown',
//   purpose: 'documentation',
//   currentLocation: 'docs/',
//   suggestedLocation: 'docs/architecture/',
//   confidence: 0.95,
//   reasoning: 'Contains architecture diagrams and system design'
// }
```

### 2. Structure Suggestion

Suggests improvements to overall project organization:
- Identifies misplaced files
- Recommends reorganization
- Predicts impact of changes
- Suggests directory additions

**Usage:**
```javascript
const suggestions = await organizer.suggestStructure({
  scope: 'documentation',
  verbose: true
});
// Returns array of suggestions with reasoning
```

### 3. Organization Automation

Automatically organizes files according to rules:
- Moves files to correct locations
- Updates import/reference paths
- Validates changes
- Generates detailed report

**Usage:**
```javascript
const result = await organizer.organize({
  dryRun: true,
  scope: 'all'
});
// With dryRun: true, only shows what would change
// With dryRun: false, actually moves files and updates references
```

## Configuration

The skill uses `./.claude/organization-rules.json` for file placement rules. It respects:
- File patterns and exclusions
- Destination directories
- Naming conventions
- Required files list

## Integration with Commands

This skill is used by:
- `/organize-codebase` - Main command for file reorganization
- `/validate-structure` - Validation and structure checking
- `/update-docs` - Documentation link updates

## Implementation Notes

- All changes are validated before applying
- Supports dry-run mode for previewing changes
- Maintains git-compatible changes (can be reverted)
- Preserves file content, only relocates files
- Updates relative paths in documentation and imports
