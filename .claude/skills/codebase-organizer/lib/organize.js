/**
 * File Organization Module
 *
 * Handles automatic organization of files according to
 * project rules and conventions.
 */

const fs = require('fs');
const path = require('path');
const analyzeFile = require('./analyze');

/**
 * Organize files according to project rules
 * @param {Object} options - Organization options
 * @param {boolean} options.dryRun - Preview without applying
 * @param {string} options.scope - Scope: 'all', 'documentation', 'commands', 'skills', or path
 * @returns {Promise<Object>} Organization report
 */
async function organizeFiles(options = {}) {
  const {
    dryRun = true,
    scope = 'all',
    verbose = false,
    rulesFile = '.claude/organization-rules.json'
  } = options;

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

    // Collect files to analyze
    const filesToAnalyze = collectFiles(scope);

    // Analyze each file
    const analyses = [];
    for (const filePath of filesToAnalyze) {
      try {
        const analysis = await analyzeFile(filePath, rules);
        analyses.push(analysis);
      } catch (e) {
        if (verbose) console.error(`Error analyzing ${filePath}:`, e.message);
      }
    }

    // Filter files that need moving
    const filesToMove = analyses.filter(a => !a.isCorrect && a.suggestedLocation);

    // Generate report
    const report = {
      dryRun,
      scope,
      timestamp: new Date().toISOString(),
      filesAnalyzed: analyses.length,
      filesToMove: filesToMove.length,
      moves: filesToMove.map(a => ({
        from: a.filePath,
        to: path.join(a.suggestedLocation, a.basename),
        reason: a.reasoning,
        confidence: a.confidence
      })),
      validationResults: {
        allAnalysed: analyses.length > 0,
        noErrors: !analyses.some(a => a.error),
        correctlyPlaced: analyses.filter(a => a.isCorrect).length,
        needsOrganization: filesToMove.length
      },
      summary: generateSummary(analyses, filesToMove, dryRun)
    };

    return report;
  } catch (error) {
    return {
      error: error.message,
      dryRun,
      scope
    };
  }
}

/**
 * Collect files to analyze based on scope
 */
function collectFiles(scope) {
  const files = [];
  const projectRoot = process.cwd();

  if (scope === 'all' || scope === 'documentation') {
    // Collect markdown files
    collectByPattern(path.join(projectRoot, 'docs'), '**/*.md', files);
  }

  if (scope === 'all' || scope === 'commands') {
    // Collect command files
    collectByPattern(path.join(projectRoot, '.claude/commands'), '**/*.md', files);
  }

  if (scope === 'all' || scope === 'skills') {
    // Collect skill files
    collectByPattern(path.join(projectRoot, '.claude/skills'), '**/*.json', files);
  }

  if (scope !== 'all' && scope !== 'documentation' && scope !== 'commands' && scope !== 'skills') {
    // Specific path
    if (fs.existsSync(scope)) {
      const stats = fs.statSync(scope);
      if (stats.isFile()) {
        files.push(scope);
      } else {
        collectByPattern(scope, '**/*', files);
      }
    }
  }

  return files;
}

/**
 * Recursively collect files matching pattern
 */
function collectByPattern(dirPath, pattern, files) {
  if (!fs.existsSync(dirPath)) return;

  const entries = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);

    if (entry.isDirectory()) {
      // Skip node_modules and other common exclusions
      if (!['node_modules', '.git', '.Claude', 'scraper/lib'].includes(entry.name)) {
        collectByPattern(fullPath, pattern, files);
      }
    } else {
      // Check if file matches pattern
      const relPath = path.relative(process.cwd(), fullPath);
      if (matchesPattern(relPath, pattern)) {
        files.push(relPath);
      }
    }
  }
}

/**
 * Simple pattern matching (supports ** and *)
 */
function matchesPattern(filePath, pattern) {
  // Convert pattern to regex
  const regexPattern = pattern
    .replace(/\./g, '\\.')
    .replace(/\*\*/g, '.*')
    .replace(/\*/g, '[^/]*')
    .replace(/\?/g, '.');

  return new RegExp(`^${regexPattern}$`).test(filePath);
}

/**
 * Generate summary text for report
 */
function generateSummary(analyses, filesToMove, dryRun) {
  const correctly = analyses.filter(a => a.isCorrect).length;
  const total = analyses.length;

  let summary = `Analyzed ${total} files: ${correctly} correctly placed`;

  if (filesToMove.length > 0) {
    summary += `, ${filesToMove.length} need reorganization`;
  }

  if (dryRun) {
    summary += ' (DRY RUN - no changes made)';
  }

  return summary;
}

module.exports = organizeFiles;
