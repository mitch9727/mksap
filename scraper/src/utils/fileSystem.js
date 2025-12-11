// scraper/src/utils/fileSystem.js
const fs = require('fs');
const path = require('path');
const https = require('https');
const { pipeline } = require('stream');
const { promisify } = require('util');
const streamPipeline = promisify(pipeline);

const OUTPUT_BASE = path.join(__dirname, '../../output');

/**
 * Ensure directory exists, create recursively if needed
 * @param {string} dir - Directory path
 */
function ensureDir(dir) {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

/**
 * Download file from HTTPS URL
 * @param {string} url - File URL
 * @param {string} destPath - Destination file path
 * @returns {Promise<string>} Path to downloaded file
 */
async function downloadFile(url, destPath) {
    ensureDir(path.dirname(destPath));
    return new Promise((resolve, reject) => {
        const file = fs.createWriteStream(destPath);
        https.get(url, response => {
            if (response.statusCode !== 200) {
                reject(new Error(`Failed to download ${url}: ${response.statusCode}`));
                return;
            }
            response.pipe(file);
            file.on('finish', () => {
                file.close();
                resolve(destPath);
            });
        }).on('error', err => {
            fs.unlink(destPath, () => {});
            reject(err);
        });
    });
}

/**
 * Save text/HTML content to file
 * Legacy version - saves to output/{questionId}/{subDir}/
 *
 * @param {string} questionId - Question ID
 * @param {string} subDir - Subdirectory (e.g., 'figures', 'tables')
 * @param {string} fileName - Filename
 * @param {string} content - File content
 * @returns {Promise<string>} Path to saved file
 */
async function saveAsset(questionId, subDir, fileName, content) {
    const dir = path.join(OUTPUT_BASE, questionId, subDir);
    ensureDir(dir);
    const filePath = path.join(dir, fileName);
    fs.writeFileSync(filePath, content, 'utf8');
    return filePath;
}

/**
 * Save asset with system folder support
 * Saves to output/{systemFolder}/{questionId}/
 *
 * @param {string} questionId - Question ID
 * @param {string} systemFolder - System folder name (e.g., 'Cardiovascular')
 * @param {string} fileName - Filename (with extension)
 * @param {string|Buffer} content - File content
 * @returns {Promise<string>} Path to saved file
 */
async function saveAssetWithSystem(questionId, systemFolder, fileName, content) {
    const dir = path.join(OUTPUT_BASE, systemFolder, questionId);
    ensureDir(dir);
    const filePath = path.join(dir, fileName);
    await fs.promises.writeFile(filePath, content, 'utf8');
    return filePath;
}

/**
 * Download file with system folder support
 * Downloads to output/{systemFolder}/{questionId}/
 *
 * @param {string} url - File URL
 * @param {string} questionId - Question ID
 * @param {string} systemFolder - System folder name
 * @param {string} fileName - Filename (with extension)
 * @returns {Promise<string>} Path to downloaded file
 */
async function downloadFileWithSystem(url, questionId, systemFolder, fileName) {
    const dir = path.join(OUTPUT_BASE, systemFolder, questionId);
    const filePath = path.join(dir, fileName);
    return downloadFile(url, filePath);
}

/**
 * Get asset path without creating directory
 * Useful for building relative paths in JSON
 *
 * @param {string} questionId - Question ID
 * @param {string} systemFolder - System folder name
 * @param {string} fileName - Filename
 * @returns {string} Full path to asset
 */
function getAssetPath(questionId, systemFolder, fileName) {
    return path.join(OUTPUT_BASE, systemFolder, questionId, fileName);
}

module.exports = {
    ensureDir,
    downloadFile,
    downloadFileWithSystem,
    saveAsset,
    saveAssetWithSystem,
    getAssetPath,
    OUTPUT_BASE
};
