/**
 * Structure Suggestion Module
 *
 * Analyzes project structure and suggests improvements
 * for better organization and maintainability.
 */

const fs = require('fs');
const path = require('path');
const analyzeFile = require('./analyze');

/**
 * Suggest structural improvements
 * @param {Object} options - Suggestion options
 * @param {string} options.scope - Scope for suggestions
 * @param {boolean} options.verbose - Include detailed reasoning
 * @returns {Promise<Array>} Array of suggestions
 */
async function suggestStructure(options = {}) {
  const {
    scope = 'all',
    verbose = false,
    rulesFile = '.claude/organization-rules.json'
  } = options;

  const suggestions = [];

  try {
    // Load organization rules
    let rules = {};
    try {
      if (fs.existsSync(rulesFile)) {
        const rulesContent = fs.readFileSync(rulesFile, 'utf8');
        rules = JSON.parse(rulesContent);
      }
    } catch (e) {
      if (verbose) console.error('Could not load rules file:', e.message);
    }

    // Analyze current structure
    const structureAnalysis = analyzeStructure(scope);

    // Generate suggestions from analysis
    if (structureAnalysis.misplacedFiles.length > 0) {
      suggestions.push({
        type: 'reorganization',
        priority: 'high',
        title: 'Reorganize misplaced files',
        description: `${structureAnalysis.misplacedFiles.length} files are not in their optimal locations`,
        files: structureAnalysis.misplacedFiles,
        action: 'Run /organize-codebase to automatically reorganize',
        impact: 'Improves code navigation and project clarity'
      });
    }

    // Check for missing directories
    if (structureAnalysis.missingDirectories.length > 0) {
      suggestions.push({
        type: 'structure',
        priority: 'medium',
        title: 'Create missing directories',
        description: `${structureAnalysis.missingDirectories.length} directories should exist but are missing`,
        directories: structureAnalysis.missingDirectories,
        action: 'Create missing directories: mkdir -p ' + structureAnalysis.missingDirectories.join(' '),
        impact: 'Ensures consistent project structure'
      });
    }

    // Check for duplicate documentation
    if (structureAnalysis.duplicateDocumentation.length > 0) {
      suggestions.push({
        type: 'consolidation',
        priority: 'medium',
        title: 'Consolidate duplicate documentation',
        description: `${structureAnalysis.duplicateDocumentation.length} pairs of similar files found`,
        files: structureAnalysis.duplicateDocumentation,
        action: 'Review and merge duplicate documentation',
        impact: 'Reduces maintenance burden and confusion'
      });
    }

    // Check for orphaned files
    if (structureAnalysis.orphanedFiles.length > 0) {
      suggestions.push({
        type: 'cleanup',
        priority: 'low',
        title: 'Review orphaned files',
        description: `${structureAnalysis.orphanedFiles.length} files appear to be orphaned or unused`,
        files: structureAnalysis.orphanedFiles,
        action: 'Review files and either organize or delete',
        impact: 'Reduces clutter and improves clarity'
      });
    }

    // Check for documentation gaps
    const docGaps = checkDocumentationGaps();
    if (docGaps.length > 0) {
      suggestions.push({
        type: 'documentation',
        priority: 'medium',
        title: 'Fill documentation gaps',
        description: `Missing documentation for ${docGaps.length} areas`,
        gaps: docGaps,
        action: 'Create missing documentation files',
        impact: 'Improves project understandability'
      });
    }

    return suggestions;
  } catch (error) {
    return [{
      type: 'error',
      priority: 'high',
      title: 'Error analyzing structure',
      error: error.message
    }];
  }
}

/**
 * Analyze current project structure
 */
function analyzeStructure(scope) {
  const analysis = {
    misplacedFiles: [],
    missingDirectories: [],
    duplicateDocumentation: [],
    orphanedFiles: [],
    filesByType: {}
  };

  const projectRoot = process.cwd();

  // Check expected directories exist
  const expectedDirs = [
    'docs/project',
    'docs/architecture',
    'docs/scraper',
    'docs/specifications',
    'docs/examples',
    'docs/legacy',
    '.claude/commands',
    '.claude/skills',
    '.claude/templates',
    'scraper/src/skills',
    'scraper/src/agents'
  ];

  for (const dir of expectedDirs) {
    if (!fs.existsSync(path.join(projectRoot, dir))) {
      analysis.missingDirectories.push(dir);
    }
  }

  // Scan for common misplaced files
  const docsPath = path.join(projectRoot, 'docs');
  if (fs.existsSync(docsPath)) {
    const files = fs.readdirSync(docsPath);
    for (const file of files) {
      const fullPath = path.join(docsPath, file);
      const stat = fs.statSync(fullPath);
      if (stat.isFile() && file.endsWith('.md')) {
        // Files directly in docs/ should be in subdirectories
        analysis.misplacedFiles.push({
          file: path.relative(projectRoot, fullPath),
          issue: 'Should be in docs/ subdirectory',
          suggestion: suggestDocLocation(file)
        });
      }
    }
  }

  // Check for duplicate documentation
  const docMap = {};
  scanForDuplicates(docsPath, docMap);
  for (const [name, occurrences] of Object.entries(docMap)) {
    if (occurrences.length > 1) {
      analysis.duplicateDocumentation.push({
        name,
        locations: occurrences
      });
    }
  }

  return analysis;
}

/**
 * Scan for duplicate files
 */
function scanForDuplicates(dirPath, docMap, baseDir = '') {
  if (!fs.existsSync(dirPath)) return;

  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      const relPath = path.join(baseDir, entry.name);

      if (entry.isDirectory()) {
        scanForDuplicates(fullPath, docMap, relPath);
      } else if (entry.name.endsWith('.md')) {
        const normalized = entry.name.toLowerCase();
        if (!docMap[normalized]) {
          docMap[normalized] = [];
        }
        docMap[normalized].push(relPath);
      }
    }
  } catch (e) {
    // Ignore errors in scanning
  }
}

/**
 * Suggest location for documentation file
 */
function suggestDocLocation(filename) {
  const lower = filename.toLowerCase();

  if (lower.includes('readme') || lower.includes('quickstart') || lower.includes('index')) {
    return 'docs/project/';
  }
  if (lower.includes('architecture') || lower.includes('design') || lower.includes('codebase')) {
    return 'docs/architecture/';
  }
  if (lower.includes('scraper') || lower.includes('technical') || lower.includes('spec')) {
    return 'docs/scraper/';
  }
  if (lower.includes('format') || lower.includes('specification')) {
    return 'docs/specifications/';
  }
  if (lower.includes('example')) {
    return 'docs/examples/';
  }
  if (lower.includes('legacy') || lower.includes('old') || lower.includes('deprecated')) {
    return 'docs/legacy/';
  }

  return 'docs/project/';
}

/**
 * Check for documentation gaps
 */
function checkDocumentationGaps() {
  const gaps = [];
  const required = [
    'docs/project/README.md',
    'docs/project/QUICKSTART.md',
    'docs/project/INDEX.md',
    'docs/architecture/CODEBASE_GUIDE.md',
    'docs/scraper/README.md',
    'docs/specifications/MCQ_FORMAT.md'
  ];

  const projectRoot = process.cwd();
  for (const file of required) {
    if (!fs.existsSync(path.join(projectRoot, file))) {
      gaps.push(file);
    }
  }

  return gaps;
}

module.exports = suggestStructure;
