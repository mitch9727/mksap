// scraper/src/extractors/figures.js
const fs = require('fs');
const path = require('path');
const { downloadFile } = require('../utils/fileSystem');
const { extractAssetName, sanitizeFilename } = require('../utils/assetNaming');
const selectors = require('../selectors');

/**
 * Extract figures from the current page/modal
 * Downloads images and returns metadata with relative paths
 *
 * @param {Page} page - Playwright page object
 * @param {string} _questionId - Question ID (e.g., CVMCQ24001) - kept for API consistency
 * @param {string} _systemFolder - System folder name (e.g., Cardiovascular) - kept for API consistency
 * @param {string} outputDir - Base output directory (e.g., scraper/output/Cardiovascular/CVMCQ24001)
 * @param {string} _context - Context label for fallback naming (default: 'main') - kept for API consistency
 * @returns {Promise<Array>} Array of figure metadata objects
 */
async function extractFigures(page, _questionId, _systemFolder, outputDir, _context = 'main') {
    const figures = await page.locator(selectors.question.figures).all();
    const results = [];

    for (let i = 0; i < figures.length; i++) {
        const fig = figures[i];
        let src = await fig.getAttribute('src');
        if (!src) continue;

        // Resolve relative URLs
        if (src.startsWith('/')) {
            src = `https://mksap.acponline.org${src}`;
        }

        try {
            // Try to extract meaningful name from the figure element
            let assetName = await extractAssetName(fig, 'figure', i + 1);

            // Get file extension from URL
            const ext = path.extname(src.split('?')[0]) || '.jpg';
            const fileName = sanitizeFilename(assetName) + ext;

            // Save to question folder
            const destPath = path.join(outputDir, fileName);

            // Ensure directory exists
            const destDir = path.dirname(destPath);
            if (!fs.existsSync(destDir)) {
                fs.mkdirSync(destDir, { recursive: true });
            }

            // Download file
            await downloadFile(src, destPath);

            results.push({
                originalSrc: src,
                path: `./${fileName}`, // Relative path for JSON portability
                alt: await fig.getAttribute('alt') || ''
            });
        } catch (e) {
            console.error(`Failed to download figure from ${src}:`, e.message);
        }
    }

    return results;
}

module.exports = { extractFigures };
