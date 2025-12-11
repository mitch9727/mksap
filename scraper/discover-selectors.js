#!/usr/bin/env node

/**
 * Interactive Selector Discovery Tool for MKSAP Scraper
 *
 * This script launches the browser in headful mode with slow motion enabled,
 * allowing you to manually inspect elements and discover the correct CSS selectors.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const CONFIG_DIR = path.join(__dirname, 'config');
const SELECTORS_OUTPUT = path.join(CONFIG_DIR, 'selectors.json');
const SELECTORS_FILE = path.join(__dirname, 'src', 'selectors.js');

// Ensure config directory exists
if (!fs.existsSync(CONFIG_DIR)) {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
}

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function question(prompt) {
    return new Promise(resolve => rl.question(prompt, resolve));
}

async function main() {
    console.log('\n🔍 MKSAP Selector Discovery Tool');
    console.log('================================\n');
    console.log('This tool will help you discover the correct CSS selectors for MKSAP.');
    console.log('The browser will open in headful mode with slow motion enabled.');
    console.log('You can inspect elements using DevTools (F12 or Cmd+Option+I).\n');

    const baseUrl = await question('Enter MKSAP base URL (e.g., https://mksap.acponline.org): ');

    const browser = await chromium.launch({
        headless: false,
        slowMo: 500  // 500ms delay between operations
    });

    const context = await browser.newContext();

    // Try to load auth if it exists
    const authPath = path.join(CONFIG_DIR, 'auth.json');
    if (fs.existsSync(authPath)) {
        console.log('\n✓ Found existing auth.json, loading stored session...');
        try {
            await context.addInitScript(() => {
                const stored = localStorage.getItem('auth');
                if (stored) {
                    localStorage.setItem('auth', stored);
                }
            });
        } catch (e) {
            console.warn('Could not load stored auth, you may need to login manually.');
        }
    }

    const page = await context.newPage();

    // Set viewport for consistent browsing
    await page.setViewportSize({ width: 1280, height: 720 });

    const discoveredSelectors = {};

    try {
        console.log('\n📍 Navigating to MKSAP base URL...');
        await page.goto(baseUrl);

        // Wait for login indicator OR wait for user to manually login
        console.log('\n⏳ Waiting for login...');
        console.log('   If not logged in, please log in manually in the browser.');
        console.log('   Once logged in, press Enter to continue: ');
        await question('');

        // --- LOGIN INDICATOR ---
        console.log('\n📋 Step 1: Login Indicator');
        console.log('Instructions:');
        console.log('  1. Look for an element that indicates you are logged in');
        console.log('     (e.g., user profile icon, user name, logout button)');
        console.log('  2. Right-click → Inspect in DevTools');
        console.log('  3. Copy the CSS selector (e.g., ".user-profile" or "#logout-btn")');
        console.log('  4. Paste it below: ');
        const loginIndicator = await question('Login Indicator CSS Selector: ');

        if (loginIndicator.trim()) {
            discoveredSelectors.loginIndicator = loginIndicator.trim();
            // Validate
            try {
                const found = await page.locator(loginIndicator).first();
                if (await found.isVisible()) {
                    console.log('✓ Selector validated!\n');
                } else {
                    console.log('⚠ Selector found but not visible. May still be correct.\n');
                }
            } catch (e) {
                console.log('⚠ Selector validation failed. It may need refinement.\n');
            }
        }

        // Navigate to question list
        console.log('📍 Navigating to Cardiovascular Medicine → Answered Questions...');
        console.log('   Please navigate manually and press Enter when ready: ');
        await question('');

        // --- QUESTION LIST CONTAINER ---
        console.log('\n📋 Step 2: Question List Container');
        console.log('Instructions:');
        console.log('  1. Look for the container holding all question items (a list, table, or div)');
        console.log('  2. Inspect and copy its CSS selector');
        const listContainer = await question('Question List Container CSS Selector: ');
        if (listContainer.trim()) {
            discoveredSelectors.listContainer = listContainer.trim();
        }

        // --- INDIVIDUAL QUESTION ITEM ---
        console.log('\n📋 Step 3: Individual Question Item');
        console.log('Instructions:');
        console.log('  1. Look for a single question item in the list');
        console.log('  2. Inspect and copy its CSS selector');
        const questionItem = await question('Question Item CSS Selector: ');
        if (questionItem.trim()) {
            discoveredSelectors.questionItem = questionItem.trim();
        }

        // Click on first question
        console.log('\n📍 Opening first question...');
        try {
            const firstQuestion = await page.locator(discoveredSelectors.questionItem || '.question-list-item').first();
            await firstQuestion.click();
            await page.waitForTimeout(1000);
        } catch (e) {
            console.log('Could not auto-click. Please click on a question manually.');
            await question('Press Enter when a question is open: ');
        }

        // --- QUESTION MODAL/CONTAINER ---
        console.log('\n📋 Step 4: Question Modal/Container');
        console.log('Instructions:');
        console.log('  1. Look for the main container/modal of the question details');
        console.log('  2. Inspect and copy its CSS selector');
        const questionContainer = await question('Question Container CSS Selector: ');
        if (questionContainer.trim()) {
            discoveredSelectors.questionContainer = questionContainer.trim();
        }

        // --- QUESTION ID ---
        console.log('\n📋 Step 5: Question ID Element');
        console.log('Instructions:');
        console.log('  1. Look for the Question ID (e.g., "CVMCQ24042")');
        console.log('  2. It may be in a heading, label, or data attribute');
        console.log('  3. Inspect and copy its CSS selector');
        const questionIdSelector = await question('Question ID CSS Selector: ');
        if (questionIdSelector.trim()) {
            discoveredSelectors.questionId = questionIdSelector.trim();
        }

        // --- EDUCATIONAL OBJECTIVE ---
        console.log('\n📋 Step 6: Educational Objective');
        console.log('Instructions:');
        console.log('  1. Look for text labeled "Educational Objective" or similar');
        console.log('  2. Inspect and copy the CSS selector for that text/element');
        const educationalObjective = await question('Educational Objective CSS Selector: ');
        if (educationalObjective.trim()) {
            discoveredSelectors.educationalObjective = educationalObjective.trim();
        }

        // --- CARE TYPE ---
        console.log('\n📋 Step 7: Care Type');
        console.log('Instructions:');
        console.log('  1. Look for text labeled "Care Type" or similar metadata');
        console.log('  2. Inspect and copy its CSS selector');
        const careType = await question('Care Type CSS Selector: ');
        if (careType.trim()) {
            discoveredSelectors.careType = careType.trim();
        }

        // --- ANSWER AND CRITIQUE ---
        console.log('\n📋 Step 8: Answer and Critique');
        console.log('Instructions:');
        console.log('  1. Look for the explanation/critique section');
        console.log('  2. This usually contains the full answer explanation');
        console.log('  3. Inspect the container and copy its CSS selector');
        const critique = await question('Answer and Critique CSS Selector: ');
        if (critique.trim()) {
            discoveredSelectors.critique = critique.trim();
        }

        // --- KEY POINTS ---
        console.log('\n📋 Step 9: Key Points');
        console.log('Instructions:');
        console.log('  1. Look for "Key Points", "Key Concepts", or "Learning Objectives"');
        console.log('  2. Inspect and copy its CSS selector');
        const keyPoint = await question('Key Points CSS Selector: ');
        if (keyPoint.trim()) {
            discoveredSelectors.keyPoint = keyPoint.trim();
        }

        // --- REFERENCES ---
        console.log('\n📋 Step 10: References');
        console.log('Instructions:');
        console.log('  1. Look for "References", "Citation", or reference section');
        console.log('  2. Inspect and copy its CSS selector');
        const references = await question('References CSS Selector: ');
        if (references.trim()) {
            discoveredSelectors.references = references.trim();
        }

        // --- FIGURES/IMAGES ---
        console.log('\n📋 Step 11: Figures/Images');
        console.log('Instructions:');
        console.log('  1. Look for any figures or diagnostic images in the question');
        console.log('  2. Inspect and copy the CSS selector for those image elements');
        const figures = await question('Figures CSS Selector: ');
        if (figures.trim()) {
            discoveredSelectors.figures = figures.trim();
        }

        // --- TABLES ---
        console.log('\n📋 Step 12: Tables');
        console.log('Instructions:');
        console.log('  1. Look for any tables in the question content');
        console.log('  2. Inspect and copy the CSS selector for table elements');
        const tables = await question('Tables CSS Selector: ');
        if (tables.trim()) {
            discoveredSelectors.tables = tables.trim();
        }

        // --- RELATED TEXT LINK ---
        console.log('\n📋 Step 13: Related Text Link');
        console.log('Instructions:');
        console.log('  1. Look for a link labeled "Related Text" or "Syllabus"');
        console.log('  2. Inspect and copy its CSS selector');
        const relatedText = await question('Related Text Link CSS Selector: ');
        if (relatedText.trim()) {
            discoveredSelectors.relatedText = relatedText.trim();
        }

        // --- CLOSE BUTTON ---
        console.log('\n📋 Step 14: Close/Back Button');
        console.log('Instructions:');
        console.log('  1. Look for a button to close the question modal');
        console.log('  2. It may be an X button, "Back" button, or similar');
        console.log('  3. Inspect and copy its CSS selector');
        const closeBtn = await question('Close Button CSS Selector: ');
        if (closeBtn.trim()) {
            discoveredSelectors.closeBtn = closeBtn.trim();
        }

        // --- NEXT PAGE BUTTON ---
        console.log('\n📋 Step 15: Next Page Button (Pagination)');
        console.log('Instructions:');
        console.log('  1. Look for a "Next" or "Next Page" button in the list view');
        console.log('  2. Inspect and copy its CSS selector');
        const nextBtn = await question('Next Page Button CSS Selector: ');
        if (nextBtn.trim()) {
            discoveredSelectors.nextBtn = nextBtn.trim();
        }

        // --- SYLLABUS/RELATED TEXT PAGE ---
        console.log('\n📋 Step 16: Syllabus Content Body (Optional)');
        console.log('Instructions:');
        console.log('  1. If you clicked "Related Text", look for the main content area');
        console.log('  2. Inspect and copy its CSS selector');
        console.log('  3. Leave blank if not navigated to related text: ');
        const syllabusBody = await question('Syllabus Body CSS Selector: ');
        if (syllabusBody.trim()) {
            discoveredSelectors.syllabusBody = syllabusBody.trim();
        }

        console.log('\n✅ Selector discovery complete!\n');

        // Save to JSON file
        console.log('📁 Saving discovered selectors to config/selectors.json...');
        fs.writeFileSync(SELECTORS_OUTPUT, JSON.stringify(discoveredSelectors, null, 2));
        console.log('✓ Saved to config/selectors.json\n');

        // Generate updated selectors.js
        console.log('📝 Generating updated src/selectors.js...');
        const selectorsCode = generateSelectorsCode(discoveredSelectors);
        fs.writeFileSync(SELECTORS_FILE, selectorsCode);
        console.log('✓ Updated src/selectors.js\n');

        console.log('📋 Discovered Selectors Summary:');
        console.log('================================');
        Object.entries(discoveredSelectors).forEach(([key, value]) => {
            console.log(`  ${key}: ${value}`);
        });
        console.log('\n✨ You can now run: npm start');

    } catch (error) {
        console.error('❌ Error during discovery:', error);
    } finally {
        await context.close();
        await browser.close();
        rl.close();
    }
}

function generateSelectorsCode(discovered) {
    return `// scraper/src/selectors.js
// Auto-generated by discover-selectors.js

module.exports = {
    login: {
        loggedInIndicator: '${discovered.loginIndicator || '.user-profile'}'
    },

    list: {
        container: '${discovered.listContainer || '.question-list'}',
        questionItem: '${discovered.questionItem || '.question-item'}',
        nextPageBtn: '${discovered.nextBtn || 'button:has-text("Next")'}'
    },

    question: {
        container: '${discovered.questionContainer || '.question-container'}',
        closeBtn: '${discovered.closeBtn || 'button[aria-label="Close"]'}',

        questionId: '${discovered.questionId || '.question-id'}',
        educationalObjective: '${discovered.educationalObjective || '.educational-objective'}',
        careType: '${discovered.careType || '.care-type'}',

        critique: '${discovered.critique || '.critique-text'}',
        keyPoint: '${discovered.keyPoint || '.key-point'}',
        references: '${discovered.references || '.references'}',

        figures: '${discovered.figures || 'img.figure-image'}',
        tables: '${discovered.tables || 'table'}',

        syllabusLink: '${discovered.relatedText || 'a:has-text("Related Text")'}'
    },

    syllabus: {
        contentBody: '${discovered.syllabusBody || '.syllabus-content'}'
    }
};
`;
}

main().catch(console.error);
