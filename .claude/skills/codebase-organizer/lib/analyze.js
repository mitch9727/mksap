/**
 * File Analysis Module
 *
 * Analyzes individual files to determine their purpose and
 * suggest correct location in the project structure.
 */

const fs = require('fs');
const path = require('path');

/**
 * Analyze a file to determine its purpose and location
 * @param {string} filePath - Path to file
 * @param {Object} rules - Organization rules from configuration
 * @returns {Promise<Object>} Analysis with suggestions
 */
async function analyzeFile(filePath, rules = {}) {
  try {
    // Read file metadata
    const stats = fs.statSync(filePath);
    const ext = path.extname(filePath);
    const basename = path.basename(filePath);
    const dirname = path.dirname(filePath);

    // Determine file type
    const fileType = determineFileType(filePath, ext);

    // Read content for analysis (first 500 chars)
    let content = '';
    if (fileType === 'markdown' || fileType === 'javascript' || fileType === 'json') {
      try {
        const fullContent = fs.readFileSync(filePath, 'utf8');
        content = fullContent.substring(0, 500);
      } catch (e) {
        // If can't read, continue with empty content
      }
    }

    // Determine current category
    const currentLocation = dirname;
    const category = categorizeFile(filePath, basename, content, fileType);

    // Suggest correct location
    const suggestedLocation = suggestLocation(category, fileType, basename, rules);

    // Calculate confidence
    const confidence = calculateConfidence(category, currentLocation, suggestedLocation);

    return {
      filePath,
      basename,
      fileType,
      sizeBytes: stats.size,
      category,
      purpose: getPurpose(category, basename, content),
      currentLocation,
      suggestedLocation,
      isCorrect: normalizePathForComparison(currentLocation) === normalizePathForComparison(suggestedLocation),
      confidence,
      reasoning: generateReasoning(category, basename, content, confidence)
    };
  } catch (error) {
    return {
      filePath,
      error: error.message,
      analysis: 'Could not analyze file'
    };
  }
}

/**
 * Determine file type from extension and content
 */
function determineFileType(filePath, ext) {
  switch (ext.toLowerCase()) {
    case '.md':
      return 'markdown';
    case '.js':
      return 'javascript';
    case '.json':
      return 'json';
    case '.yaml':
    case '.yml':
      return 'yaml';
    case '.sh':
      return 'shell';
    case '.py':
      return 'python';
    default:
      return 'other';
  }
}

/**
 * Categorize file based on name, location, and content
 */
function categorizeFile(filePath, basename, content, fileType) {
  // Check for documentation indicators
  if (fileType === 'markdown') {
    const lowerName = basename.toLowerCase();
    const lowerPath = filePath.toLowerCase();

    // Project-level docs
    if (lowerName.includes('readme') || lowerName.includes('quickstart') || lowerName.includes('index')) {
      return 'project-documentation';
    }

    // Architecture docs
    if (lowerName.includes('architecture') || lowerName.includes('design') ||
        lowerName.includes('codebase') || lowerName.includes('organization')) {
      return 'architecture-documentation';
    }

    // Scraper docs
    if (lowerPath.includes('scraper') || lowerName.includes('scraper') ||
        lowerName.includes('technical') || lowerName.includes('specification')) {
      return 'scraper-documentation';
    }

    // Specification docs
    if (lowerName.includes('spec') || lowerName.includes('format')) {
      return 'specification-documentation';
    }

    // Example docs
    if (lowerName.includes('example') || lowerPath.includes('example')) {
      return 'example-documentation';
    }

    // Legacy docs
    if (lowerName.includes('legacy') || lowerName.includes('old') || lowerName.includes('deprecated')) {
      return 'legacy-documentation';
    }

    return 'general-documentation';
  }

  // Check for command indicators
  if (fileType === 'markdown' && filePath.includes('.claude/commands')) {
    return 'claude-command';
  }

  // Check for skill indicators
  if ((fileType === 'json' && basename === 'skill.json') ||
      filePath.includes('.claude/skills')) {
    return 'claude-skill';
  }

  // Check for implementation code
  if (fileType === 'javascript' && filePath.includes('scraper/src')) {
    if (filePath.includes('skills')) return 'implementation-skill';
    if (filePath.includes('agents')) return 'implementation-agent';
    return 'scraper-implementation';
  }

  // Check for configuration
  if (fileType === 'json' && (lowerName.includes('config') || lowerName.includes('rules') || lowerName.includes('standards'))) {
    return 'configuration';
  }

  return 'unclassified';
}

/**
 * Suggest correct location for file
 */
function suggestLocation(category, fileType, basename, rules) {
  switch (category) {
    case 'project-documentation':
      return 'docs/project';
    case 'architecture-documentation':
      return 'docs/architecture';
    case 'scraper-documentation':
      return 'docs/scraper';
    case 'specification-documentation':
      return 'docs/specifications';
    case 'example-documentation':
      return 'docs/examples';
    case 'legacy-documentation':
      return 'docs/legacy';
    case 'general-documentation':
      return 'docs/project';
    case 'claude-command':
      return '.claude/commands';
    case 'claude-skill':
      return '.claude/skills';
    case 'implementation-skill':
      return 'scraper/src/skills';
    case 'implementation-agent':
      return 'scraper/src/agents';
    case 'scraper-implementation':
      return 'scraper/src';
    case 'configuration':
      return '.claude';
    default:
      return 'docs/project';
  }
}

/**
 * Get human-readable purpose for file
 */
function getPurpose(category, basename, content) {
  const purposeMap = {
    'project-documentation': 'Project overview and getting started guide',
    'architecture-documentation': 'Architecture and system design documentation',
    'scraper-documentation': 'Scraper functionality and technical details',
    'specification-documentation': 'Format specifications and standards',
    'example-documentation': 'Example files and sample content',
    'legacy-documentation': 'Archived or historical documentation',
    'claude-command': 'Claude Code slash command',
    'claude-skill': 'Claude Agent SDK skill',
    'implementation-skill': 'Scraper implementation skill',
    'implementation-agent': 'Scraper implementation agent',
    'configuration': 'Project configuration file'
  };

  return purposeMap[category] || 'Project file';
}

/**
 * Calculate confidence score (0-1)
 */
function calculateConfidence(category, currentLocation, suggestedLocation) {
  if (normalizePathForComparison(currentLocation) === normalizePathForComparison(suggestedLocation)) {
    return 1.0;
  }

  // Reduce confidence if file is in wrong location
  const penalty = 0.3;
  return Math.max(0.5, 1.0 - penalty);
}

/**
 * Generate reasoning for analysis
 */
function generateReasoning(category, basename, content, confidence) {
  const reasons = [];

  if (category.includes('documentation')) {
    reasons.push('File is markdown documentation');
  }

  if (basename.toLowerCase().includes('readme')) {
    reasons.push('README files belong in project organization');
  }

  if (category.includes('scraper')) {
    reasons.push('Related to scraper functionality');
  }

  if (category.includes('legacy')) {
    reasons.push('File appears to be archived or outdated');
  }

  if (confidence === 1.0) {
    reasons.push('File is in correct location');
  } else if (confidence >= 0.8) {
    reasons.push('File location confidence is high');
  } else {
    reasons.push('File may benefit from reorganization');
  }

  return reasons.join('; ');
}

/**
 * Normalize path for comparison
 */
function normalizePathForComparison(filePath) {
  return filePath.replace(/\\/g, '/').toLowerCase();
}

module.exports = analyzeFile;
