# Documentation Validator Skill

## Purpose

The `doc-validator` skill provides comprehensive documentation quality assurance. It validates links, enforces documentation standards, detects outdated content, and suggests improvements for documentation quality and consistency.

## Capabilities

### 1. Link Validation

Checks all links in documentation:
- Verifies internal file links exist
- Detects broken references
- Validates relative path correctness
- Suggests path fixes

**Usage:**
```javascript
const validator = require('./.claude/skills/doc-validator');

const linkResults = await validator.checkLinks({
  scope: 'docs/',
  verbose: true
});
// Returns: {
//   checked: 127,
//   valid: 124,
//   broken: 3,
//   brokenLinks: [{ file, line, link, issue, suggestion }]
// }
```

### 2. Style Enforcement

Enforces documentation standards:
- Checks heading structure
- Validates formatting consistency
- Verifies required sections
- Ensures proper markdown syntax

**Usage:**
```javascript
const styleResults = await validator.enforceStyle({
  standardsFile: '.claude/doc-standards.json'
});
// Returns array of style violations with fixes
```

### 3. Content Analysis

Analyzes documentation content:
- Detects duplicate sections
- Identifies outdated information
- Finds missing documentation
- Suggests content improvements

**Usage:**
```javascript
const contentResults = await validator.analyzeContent({
  scope: 'documentation',
  checkCompleteness: true
});
```

### 4. Quality Report

Generates comprehensive quality assessment:
- Overall documentation health score
- Severity breakdown (errors, warnings, info)
- Specific issues with locations
- Recommended fixes

**Usage:**
```javascript
const report = await validator.generateReport({
  verbose: true,
  fixSuggestions: true
});
// Returns detailed quality report
```

## Configuration

The skill uses `./.claude/doc-standards.json` for validation standards, including:
- Required sections for different document types
- Formatting requirements
- Link validation rules
- Content standards

## Integration with Commands

This skill is used by:
- `/validate-structure` - Documentation quality checks
- `/update-docs` - Link validation and fixing
- Continuous quality monitoring

## Implementation Notes

- Supports both internal and external link validation
- Generates actionable fix suggestions
- Works with markdown files
- Maintains detailed validation logs
- Can auto-fix common issues
