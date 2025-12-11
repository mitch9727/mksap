/**
 * MKSAP Autonomous Question Scraper - Main Entry Point
 *
 * This script launches a worker pool-based browser automation tool to extract
 * medical multiple-choice questions from MKSAP (mksap.acponline.org) into
 * structured JSON format organized by medical system.
 *
 * Architecture: Worker Pool with Shared Browser
 * - Single Playwright browser instance (resource efficient)
 * - Multiple concurrent workers (default: 2)
 * - Each worker: INIT → LOGIN → NAVIGATE → PROCESS_QUESTIONS → EXIT
 * - Each system's questions saved to: output/{SystemFolder}/{QuestionID}/
 *
 * Output Structure:
 * ```
 * output/
 * ├── Cardiovascular/
 * │   ├── CVMCQ24001/
 * │   │   ├── CVMCQ24001.json
 * │   │   ├── figure_1.jpg
 * │   │   └── Table_Name.html
 * │   └── ...
 * ├── Pulmonary/
 * │   └── ...
 * └── logs/
 * ```
 *
 * First Run:
 *   - Browser opens in HEADFUL mode (visible window)
 *   - You manually log in to MKSAP (credentials saved to config/auth.json)
 *   - First system scrapes with manual login, subsequent systems use saved auth
 *
 * Subsequent Runs:
 *   - Browser runs HEADLESS (background)
 *   - Uses saved authentication automatically
 *   - Scrapes all systems autonomously with 2 concurrent workers
 *
 * Usage:
 *   npm start              # Scrape all 12 systems
 *   npm start cv en pmcc   # Scrape specific systems
 *
 * Documentation:
 *   - README.md - Quick start guide
 *   - SELECTORS_REFERENCE.md - All CSS selectors
 *   - CODEBASE_GUIDE.md - Architecture details
 */

const WorkerPool = require('./src/WorkerPool');
const SYSTEMS = require('./config/systems');
const fs = require('fs');
const path = require('path');

/**
 * Parse command-line arguments to determine which systems to scrape
 * Usage: npm start [system1] [system2] ...
 * @returns {Array<string>} Array of system codes to scrape
 */
function getSystemsToScrape() {
    // Arguments come after 'node main.js'
    // In npm scripts, after 'npm start --'
    const args = process.argv.slice(2);

    if (args.length === 0) {
        // Default: scrape all systems
        return Object.keys(SYSTEMS);
    }

    // Validate that provided system codes exist
    const validSystems = args.filter(code => {
        if (SYSTEMS[code]) {
            return true;
        } else {
            console.warn(`⚠️  Unknown system code: ${code}`);
            return false;
        }
    });

    if (validSystems.length === 0) {
        console.error('❌ No valid system codes provided');
        console.error('Available systems:');
        Object.entries(SYSTEMS).forEach(([code, config]) => {
            console.error(`  ${code}: ${config.emoji} ${config.name}`);
        });
        process.exit(1);
    }

    return validSystems;
}

/**
 * Setup required directories
 */
function ensureDirectories() {
    const dirs = [
        'logs',      // Execution logs
        'config',    // Auth & configuration
        'output'     // Scraped JSON data and assets by system
    ];

    dirs.forEach(d => {
        const fullPath = path.join(__dirname, d);
        if (!fs.existsSync(fullPath)) {
            fs.mkdirSync(fullPath, { recursive: true });
        }
    });
}

/**
 * Main entry point
 */
async function main() {
    console.log('');
    console.log('═══════════════════════════════════════════════════════');
    console.log('MKSAP Autonomous Question Scraper');
    console.log('═══════════════════════════════════════════════════════');

    // Setup
    ensureDirectories();
    const systemsToScrape = getSystemsToScrape();

    console.log(`📋 Systems to scrape: ${systemsToScrape.map(code => `${SYSTEMS[code].emoji} ${SYSTEMS[code].name}`).join(', ')}`);
    console.log('');

    // Configuration
    const authFile = path.join(__dirname, 'config/auth.json');
    const outputDir = path.join(__dirname, 'output');
    const concurrency = 2; // User-specified concurrent workers

    // Launch worker pool
    const pool = new WorkerPool(systemsToScrape, authFile, outputDir, concurrency);

    try {
        const results = await pool.run();

        // Exit with appropriate code
        if (results.failed.length > 0) {
            console.error(`\n❌ ${results.failed.length} system(s) failed`);
            process.exit(1);
        } else {
            console.log(`\n✓ All ${results.completed.length} system(s) completed successfully`);
            process.exit(0);
        }
    } catch (error) {
        console.error(`\n❌ Fatal error: ${error.message}`);
        process.exit(1);
    }
}

main();
