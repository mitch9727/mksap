/**
 * Documentation Validator Skill - Main Entry Point
 *
 * Provides comprehensive documentation quality assurance:
 * link validation, style enforcement, and content analysis.
 */

const checkLinks = require('./check-links');
const enforceStyle = require('./enforce-style');
const analyzeContent = require('./analyze-content');

/**
 * Main skill interface
 */
module.exports = {
  /**
   * Check all links in documentation
   * @param {Object} options - Validation options
   * @returns {Promise<Object>} Link validation results
   */
  checkLinks,

  /**
   * Enforce documentation style standards
   * @param {Object} options - Style options
   * @returns {Promise<Array>} Style violations found
   */
  enforceStyle,

  /**
   * Analyze documentation content
   * @param {Object} options - Analysis options
   * @returns {Promise<Object>} Content analysis results
   */
  analyzeContent,

  /**
   * Generate comprehensive quality report
   * @param {Object} options - Report options
   * @returns {Promise<Object>} Quality assessment report
   */
  generateReport: async (options = {}) => {
    const links = await checkLinks(options);
    const style = await enforceStyle(options);
    const content = await analyzeContent(options);

    return {
      timestamp: new Date().toISOString(),
      links,
      style,
      content,
      overallScore: calculateScore(links, style, content),
      summary: generateSummary(links, style, content)
    };
  },

  /**
   * Version and metadata
   */
  version: '1.0.0',
  name: 'doc-validator'
};

/**
 * Calculate overall quality score
 */
function calculateScore(links, style, content) {
  const linkScore = links.valid / Math.max(1, links.checked);
  const styleScore = style.length === 0 ? 1.0 : Math.max(0, 1.0 - (style.length * 0.1));
  const contentScore = content.issues ? Math.max(0, 1.0 - (content.issues.length * 0.05)) : 1.0;

  return Math.round((linkScore * 0.4 + styleScore * 0.35 + contentScore * 0.25) * 100);
}

/**
 * Generate summary text
 */
function generateSummary(links, style, content) {
  const parts = [];

  if (links.broken > 0) {
    parts.push(`${links.broken} broken links`);
  }
  if (style.length > 0) {
    parts.push(`${style.length} style violations`);
  }
  if (content.issues && content.issues.length > 0) {
    parts.push(`${content.issues.length} content issues`);
  }

  if (parts.length === 0) {
    return 'Documentation is well-maintained ✅';
  }

  return 'Found: ' + parts.join(', ');
}
