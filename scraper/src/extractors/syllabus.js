// scraper/src/extractors/syllabus.js
const path = require('path');
const selectors = require('../selectors');
const { extractFigures } = require('./figures');
const { extractTables } = require('./tables');

/**
 * Extract syllabus/related text for a question
 * Navigates to related text, extracts content and assets, then returns
 *
 * @param {Page} page - Playwright page object
 * @param {string} _questionId - Question ID (e.g., CVMCQ24001) - kept for API consistency
 * @param {string} systemFolder - System folder name (e.g., Cardiovascular)
 * @param {string} baseOutputDir - Base output directory (e.g., scraper/output)
 * @returns {Promise<Object|null>} Syllabus data with breadcrumbs, bodyHtml, figures, tables, or null
 */
async function extractSyllabus(page, _questionId, systemFolder, baseOutputDir) {
    // 1. Check if syllabus link exists
    const link = page.locator(selectors.question.syllabusLink).first();
    if (!(await link.isVisible())) {
        return null; // No syllabus
    }

    try {
        await link.click();

        // Wait for syllabus page to load
        // (usually opens in a new page or replaces content)
        await page.waitForLoadState('networkidle');

        // 2. Extract Breadcrumbs (optional)
        let breadcrumbs = [];
        try {
            const breadcrumbElements = await page.locator(selectors.syllabus.breadcrumbs).all();
            breadcrumbs = await Promise.all(
                breadcrumbElements.map(el => el.innerText())
            );
        } catch (e) {
            // Breadcrumbs may not exist
        }

        // 3. Extract Content Body (HTML)
        const bodyLocator = page.locator(selectors.syllabus.contentBody);
        let bodyHtml = '';
        if (await bodyLocator.isVisible()) {
            bodyHtml = await bodyLocator.evaluate(el => el.innerHTML);
        }

        // 4. Extract Assets from syllabus page
        // Create separate output directory for syllabus assets
        const syllabusOutputDir = path.join(baseOutputDir, systemFolder, 'syllabus_assets');

        const figures = await extractFigures(page, _questionId, systemFolder, syllabusOutputDir, 'syllabus').catch(() => []);
        const tables = await extractTables(page, _questionId, systemFolder, syllabusOutputDir, 'syllabus').catch(() => []);

        // 5. Navigate Back to question
        // Use page.goBack() if syllabus opened as navigation, or handle modal if needed
        try {
            await page.goBack();
            await page.waitForLoadState('networkidle');
        } catch (e) {
            // If goBack fails, we may be in a different context - that's OK
            // The question extraction will handle recovery
        }

        return {
            breadcrumbs: breadcrumbs.join(' > '),
            bodyHtml,
            figures,
            tables
        };
    } catch (error) {
        // If anything goes wrong, try to go back and return null
        try {
            await page.goBack();
        } catch (e) {
            // Ignore
        }
        return null;
    }
}

module.exports = { extractSyllabus };
