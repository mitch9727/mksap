// scraper/src/extractors/tables.js
const fs = require('fs');
const path = require('path');
const { extractAssetName, sanitizeFilename } = require('../utils/assetNaming');
const selectors = require('../selectors');

/**
 * Extract tables from the current page/modal
 * Saves tables as separate HTML files and returns metadata with relative paths
 *
 * @param {Page} page - Playwright page object
 * @param {string} _questionId - Question ID (e.g., CVMCQ24001) - kept for API consistency
 * @param {string} _systemFolder - System folder name (e.g., Cardiovascular) - kept for API consistency
 * @param {string} outputDir - Base output directory (e.g., scraper/output/Cardiovascular/CVMCQ24001)
 * @param {string} _context - Context label for fallback naming (default: 'main') - kept for API consistency
 * @returns {Promise<Array>} Array of table metadata objects with path and html
 */
async function extractTables(page, _questionId, _systemFolder, outputDir, _context = 'main') {
    const results = [];
    let tableCount = 0;

    // 1. Extract inline tables (directly visible)
    const inlineTables = await page.locator(selectors.question.tables).all();
    for (let i = 0; i < inlineTables.length; i++) {
        const table = inlineTables[i];
        if (!(await table.isVisible())) continue;

        try {
            const html = await table.evaluate(el => el.outerHTML);

            // Try to extract meaningful name from table context
            // Look for preceding heading or caption
            let tableName = await extractAssetName(table, 'table', ++tableCount);
            const fileName = sanitizeFilename(tableName) + '.html';

            // Ensure directory exists
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
            }

            // Save HTML file
            const filePath = path.join(outputDir, fileName);
            fs.writeFileSync(filePath, html, 'utf8');

            results.push({
                path: `./${fileName}`, // Relative path for JSON portability
                html: html
            });
        } catch (e) {
            console.warn(`Failed to extract inline table: ${e.message}`);
        }
    }

    // 2. Extract tables from modal links
    try {
        const tableLinks = await page.locator(selectors.question.tableLinks).all();
        for (let i = 0; i < tableLinks.length; i++) {
            const link = tableLinks[i];
            if (!(await link.isVisible())) continue;

            try {
                // Try to get meaningful name from link text
                let linkText = await link.innerText().catch(() => '');
                linkText = linkText.trim() || `Table ${++tableCount}`;

                // Click link to open table modal
                await link.click();
                await page.waitForTimeout(500); // Wait for modal to open

                // Get table from modal
                const modalTable = await page.locator(selectors.question.tables).first();
                if (await modalTable.isVisible()) {
                    const html = await modalTable.evaluate(el => el.outerHTML);
                    const fileName = sanitizeFilename(linkText) + '.html';

                    // Ensure directory exists
                    if (!fs.existsSync(outputDir)) {
                        fs.mkdirSync(outputDir, { recursive: true });
                    }

                    // Save HTML file
                    const filePath = path.join(outputDir, fileName);
                    fs.writeFileSync(filePath, html, 'utf8');

                    results.push({
                        path: `./${fileName}`, // Relative path for JSON portability
                        html: html
                    });
                }

                // Close modal (press Escape or click close button)
                await page.keyboard.press('Escape');
                await page.waitForTimeout(300);
            } catch (e) {
                console.warn(`Failed to extract table from link: ${e.message}`);
            }
        }
    } catch (e) {
        console.warn(`Table link extraction failed: ${e.message}`);
    }

    return results;
}

module.exports = { extractTables };
