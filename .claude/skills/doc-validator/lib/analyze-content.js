/**
 * Content Analysis Module
 *
 * Analyzes documentation content for quality, completeness,
 * and identifies areas for improvement.
 */

const fs = require('fs');
const path = require('path');

/**
 * Analyze documentation content
 * @param {Object} options - Analysis options
 * @param {string} options.scope - Scope to analyze
 * @param {boolean} options.checkCompleteness - Check for missing sections
 * @returns {Promise<Object>} Content analysis results
 */
async function analyzeContent(options = {}) {
  const {
    scope = 'docs/',
    checkCompleteness = true
  } = options;

  const results = {
    scope,
    filesAnalyzed: 0,
    issues: [],
    suggestions: [],
    completenessScore: 0,
    readabilityScore: 0
  };

  try {
    const projectRoot = process.cwd();
    const targetPath = path.join(projectRoot, scope);

    if (!fs.existsSync(targetPath)) {
      return { ...results, error: `Path not found: ${scope}` };
    }

    // Collect markdown files
    const mdFiles = collectMarkdownFiles(targetPath);
    results.filesAnalyzed = mdFiles.length;

    // Analyze each file
    for (const filePath of mdFiles) {
      const content = fs.readFileSync(filePath, 'utf8');
      const relPath = path.relative(projectRoot, filePath);

      // Check for issues
      const fileIssues = analyzeFile(relPath, content);
      results.issues.push(...fileIssues);

      // Check completeness
      if (checkCompleteness) {
        const completenessIssues = checkCompleteness(relPath, content);
        results.issues.push(...completenessIssues);
      }
    }

    // Generate overall scores
    results.completenessScore = calculateCompletenessScore(results.issues);
    results.readabilityScore = calculateReadabilityScore(results.issues);

    return results;
  } catch (error) {
    return { ...results, error: error.message };
  }
}

/**
 * Analyze a single file for content issues
 */
function analyzeFile(filePath, content) {
  const issues = [];
  const lines = content.split('\n');

  // Check for empty sections
  let currentHeading = '';
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.match(/^#+\s+/)) {
      // If previous section was empty, that's an issue
      if (currentHeading && i - 1 >= 0) {
        const contentAfterHeading = lines.slice(lines.indexOf(currentHeading) + 1, i)
          .filter(l => l.trim() !== '' && !l.match(/^#+/))
          .length;

        if (contentAfterHeading === 0) {
          issues.push({
            type: 'empty-section',
            file: filePath,
            line: i,
            section: currentHeading,
            issue: 'Section is empty - no content provided'
          });
        }
      }

      currentHeading = line;
    }
  }

  // Check for very short content
  const wordCount = content.split(/\s+/).length;
  if (wordCount < 50) {
    issues.push({
      type: 'thin-content',
      file: filePath,
      issue: `File is very short (${wordCount} words) - consider expanding`,
      severity: 'warning'
    });
  }

  // Check for outdated language
  const outdatedPatterns = [
    { pattern: /TODO|FIXME|HACK/i, issue: 'Contains TODO/FIXME markers' },
    { pattern: /\[WIP\]|\(work in progress\)/i, issue: 'Marked as work-in-progress' },
    { pattern: /coming soon|will be added|planned for/i, issue: 'References future plans' }
  ];

  for (const { pattern, issue } of outdatedPatterns) {
    if (pattern.test(content)) {
      issues.push({
        type: 'outdated-language',
        file: filePath,
        issue,
        severity: 'info'
      });
    }
  }

  // Check for proper examples
  if (!content.includes('```') && !content.includes('Example') && !content.includes('Usage')) {
    issues.push({
      type: 'missing-examples',
      file: filePath,
      issue: 'No code examples or usage examples provided',
      severity: 'warning'
    });
  }

  return issues;
}

/**
 * Check for missing sections (doesn't conflict with analyzeFile function)
 */
function checkContentCompleteness(filePath, content) {
  const issues = [];
  const lowerContent = content.toLowerCase();

  // Required sections for different file types
  const requirements = {
    'README.md': ['overview', 'installation', 'usage'],
    'TECHNICAL_SPEC.md': ['architecture', 'api', 'configuration'],
    'QUICKSTART.md': ['prerequisites', 'steps', 'troubleshooting']
  };

  const fileName = path.basename(filePath);
  const required = requirements[fileName] || [];

  for (const section of required) {
    if (!lowerContent.includes(`## ${section}`) && !lowerContent.includes(`# ${section}`)) {
      issues.push({
        type: 'missing-section',
        file: filePath,
        issue: `Missing expected section: ${section}`,
        severity: 'warning'
      });
    }
  }

  return issues;
}

/**
 * Calculate completeness score (0-100)
 */
function calculateCompletenessScore(issues) {
  if (issues.length === 0) return 100;

  const criticalIssues = issues.filter(i => i.severity === 'error').length;
  const warningIssues = issues.filter(i => i.severity === 'warning').length;

  const penalty = (criticalIssues * 10) + (warningIssues * 3);
  return Math.max(0, 100 - penalty);
}

/**
 * Calculate readability score (0-100)
 */
function calculateReadabilityScore(issues) {
  if (issues.length === 0) return 100;

  const styleIssues = issues.filter(i => i.type === 'spacing' || i.type === 'line-length').length;
  const penalty = styleIssues * 2;

  return Math.max(0, 100 - penalty);
}

/**
 * Collect all markdown files
 */
function collectMarkdownFiles(dirPath) {
  const files = [];

  const collect = (dir) => {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
          collect(fullPath);
        } else if (entry.name.endsWith('.md')) {
          files.push(fullPath);
        }
      }
    } catch (e) {
      // Ignore
    }
  };

  collect(dirPath);
  return files;
}

module.exports = analyzeContent;
