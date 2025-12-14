/**
 * Codebase Organizer Skill - Main Entry Point
 *
 * Provides AI-powered file analysis and project organization capabilities.
 * Analyzes file content to suggest correct locations and automates organization.
 */

const analyzeFile = require('./analyze');
const organizeFiles = require('./organize');
const suggestStructure = require('./suggest');

/**
 * Main skill interface
 */
module.exports = {
  /**
   * Analyze a single file
   * @param {string} filePath - Path to file to analyze
   * @param {Object} options - Analysis options
   * @returns {Promise<Object>} Analysis result with suggestions
   */
  analyzeFile,

  /**
   * Organize files according to rules
   * @param {Object} options - Organization options
   * @param {boolean} options.dryRun - Preview changes without applying
   * @param {string} options.scope - 'all', 'documentation', 'commands', 'skills', or specific path
   * @returns {Promise<Object>} Organization result with changes and validation
   */
  organize: organizeFiles,

  /**
   * Suggest structural improvements
   * @param {Object} options - Suggestion options
   * @param {string} options.scope - Scope for suggestions
   * @param {boolean} options.verbose - Include detailed reasoning
   * @returns {Promise<Array>} Array of suggestions with reasoning
   */
  suggestStructure,

  /**
   * Version and metadata
   */
  version: '1.0.0',
  name: 'codebase-organizer'
};
