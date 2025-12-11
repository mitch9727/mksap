/**
 * Question JSON Writer
 *
 * Writes individual JSON files for each question, organized by system folder.
 * Replaces the old JSONL approach with per-question JSON structure.
 *
 * Output structure:
 * output/
 * ├── Cardiovascular/
 * │   ├── CVMCQ24001/
 * │   │   ├── CVMCQ24001.json
 * │   │   ├── figure_1.png
 * │   │   └── table_1.html
 * │   └── CVMCQ24002/
 * └── Neurology/
 *     └── ...
 *
 * @module questionWriter
 */

const fs = require('fs');
const path = require('path');

const { ensureDir } = require('./fileSystem');

/**
 * Write individual question JSON file
 *
 * Creates the question folder (e.g., output/Cardiovascular/CVMCQ24001/)
 * and writes the JSON data to a file named after the question ID.
 *
 * @param {Object} data - Question data object with all fields
 * @param {string} data.ID - Question ID (used as filename)
 * @param {string} systemFolder - System folder name (e.g., 'Cardiovascular')
 * @param {string} baseOutputDir - Base output directory (default: './output')
 * @returns {Promise<string>} Path to the written JSON file
 *
 * @example
 * const questionData = {
 *   ID: 'CVMCQ24001',
 *   'Last Updated': 'June 2025',
 *   Reference: '...',
 *   // ... other fields
 * };
 * const filePath = await writeQuestionJson(questionData, 'Cardiovascular');
 * // Creates: output/Cardiovascular/CVMCQ24001/CVMCQ24001.json
 */
async function writeQuestionJson(data, systemFolder, baseOutputDir = './output') {
  try {
    // Create question directory
    const questionDir = path.join(baseOutputDir, systemFolder, data.ID);
    ensureDir(questionDir);

    // Write JSON file
    const filePath = path.join(questionDir, `${data.ID}.json`);
    const jsonContent = JSON.stringify(data, null, 2);

    await fs.promises.writeFile(filePath, jsonContent, 'utf8');

    return filePath;
  } catch (error) {
    throw new Error(`Failed to write question JSON for ${data.ID}: ${error.message}`);
  }
}

/**
 * Get the question directory path (without filename)
 *
 * Useful for saving related files (images, tables) in the same folder.
 *
 * @param {string} questionID - Question ID
 * @param {string} systemFolder - System folder name
 * @param {string} baseOutputDir - Base output directory
 * @returns {string} Path to question directory
 *
 * @example
 * const dir = getQuestionDir('CVMCQ24001', 'Cardiovascular');
 * // Returns: 'output/Cardiovascular/CVMCQ24001'
 */
function getQuestionDir(questionID, systemFolder, baseOutputDir = './output') {
  return path.join(baseOutputDir, systemFolder, questionID);
}

module.exports = {
  writeQuestionJson,
  getQuestionDir
};
