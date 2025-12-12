/**
 * Temporary File Manager
 *
 * Manages temporary screenshot files for Claude Code vision analysis.
 * Creates, tracks, and cleans up temp files in .temp/ directory.
 *
 * @module tempFileManager
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Temp directory path
const TEMP_DIR = path.join(__dirname, '../../.temp');

// Track created temp files for cleanup
const tempFiles = new Set();

/**
 * Ensure temp directory exists
 */
function ensureTempDir() {
  if (!fs.existsSync(TEMP_DIR)) {
    fs.mkdirSync(TEMP_DIR, { recursive: true });
  }
}

/**
 * Save screenshot data to temp file
 *
 * @param {string} screenshotData - Base64 screenshot data or Buffer
 * @returns {Promise<string>} Path to temp file
 *
 * @example
 * const screenshot = await page.screenshot({ encoding: 'base64' });
 * const tempPath = await saveTempScreenshot(screenshot);
 * // tempPath: /path/to/scraper/.temp/screenshot_abc123.png
 */
async function saveTempScreenshot(screenshotData) {
  ensureTempDir();

  // Generate unique filename
  const hash = crypto.randomBytes(8).toString('hex');
  const timestamp = Date.now();
  const filename = `screenshot_${timestamp}_${hash}.png`;
  const filePath = path.join(TEMP_DIR, filename);

  try {
    // Handle different input formats
    let buffer;

    if (Buffer.isBuffer(screenshotData)) {
      buffer = screenshotData;
    } else if (typeof screenshotData === 'string') {
      // Remove data URL prefix if present
      const base64Data = screenshotData.replace(/^data:image\/\w+;base64,/, '');
      buffer = Buffer.from(base64Data, 'base64');
    } else {
      throw new Error('Screenshot data must be Buffer or base64 string');
    }

    // Write file
    await fs.promises.writeFile(filePath, buffer);

    // Track for cleanup
    tempFiles.add(filePath);

    return filePath;
  } catch (error) {
    throw new Error(`Failed to save temp screenshot: ${error.message}`);
  }
}

/**
 * Clean up a specific temp file
 *
 * @param {string} filePath - Path to temp file
 * @returns {Promise<boolean>} True if deleted successfully
 */
async function cleanupTempFile(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      await fs.promises.unlink(filePath);
      tempFiles.delete(filePath);
      return true;
    }
    return false;
  } catch (error) {
    console.error(`[tempFileManager] Failed to cleanup ${filePath}: ${error.message}`);
    return false;
  }
}

/**
 * Clean up all tracked temp files
 *
 * @returns {Promise<number>} Number of files deleted
 */
async function cleanupAllTempFiles() {
  let deleted = 0;

  for (const filePath of tempFiles) {
    const success = await cleanupTempFile(filePath);
    if (success) deleted++;
  }

  return deleted;
}

/**
 * Clean up old temp files (older than specified age)
 *
 * @param {number} maxAgeMs - Maximum age in milliseconds (default: 1 hour)
 * @returns {Promise<number>} Number of files deleted
 */
async function cleanupOldTempFiles(maxAgeMs = 3600000) {
  ensureTempDir();

  let deleted = 0;
  const now = Date.now();

  try {
    const files = await fs.promises.readdir(TEMP_DIR);

    for (const file of files) {
      const filePath = path.join(TEMP_DIR, file);
      const stats = await fs.promises.stat(filePath);

      if (now - stats.mtimeMs > maxAgeMs) {
        await fs.promises.unlink(filePath);
        tempFiles.delete(filePath);
        deleted++;
      }
    }
  } catch (error) {
    console.error(`[tempFileManager] Failed to cleanup old files: ${error.message}`);
  }

  return deleted;
}

/**
 * Get temp file stats
 *
 * @returns {Promise<Object>} Temp file statistics
 */
async function getTempFileStats() {
  ensureTempDir();

  try {
    const files = await fs.promises.readdir(TEMP_DIR);
    let totalSize = 0;

    for (const file of files) {
      const filePath = path.join(TEMP_DIR, file);
      const stats = await fs.promises.stat(filePath);
      totalSize += stats.size;
    }

    return {
      count: files.length,
      totalSizeBytes: totalSize,
      totalSizeMB: (totalSize / (1024 * 1024)).toFixed(2),
      trackedFiles: tempFiles.size
    };
  } catch (error) {
    return {
      count: 0,
      totalSizeBytes: 0,
      totalSizeMB: '0.00',
      trackedFiles: tempFiles.size,
      error: error.message
    };
  }
}

module.exports = {
  saveTempScreenshot,
  cleanupTempFile,
  cleanupAllTempFiles,
  cleanupOldTempFiles,
  getTempFileStats
};
