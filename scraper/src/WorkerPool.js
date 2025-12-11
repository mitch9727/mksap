/**
 * WorkerPool - Manages parallel execution of SystemScraper instances
 *
 * Orchestrates multi-system scraping with configurable concurrency:
 * - Launches shared Playwright browser once
 * - Creates queue of systems to scrape
 * - Maintains N concurrent workers (default: 2)
 * - Routes completed workers to process next system in queue
 * - Tracks progress and aggregates results
 *
 * @class WorkerPool
 * @param {Array<string>} systemCodes - Array of system codes (e.g., ['cv', 'en', 'pmcc'])
 * @param {string} authFile - Path to auth.json file
 * @param {string} outputDir - Base output directory
 * @param {number} concurrency - Number of concurrent workers (default: 2)
 * @param {object} sharedLogger - Shared logger instance (optional)
 */

const { chromium } = require('playwright');
const path = require('path');
const winston = require('winston');
const SystemScraper = require('./SystemScraper');
const SYSTEMS = require('../config/systems');

class WorkerPool {
    constructor(systemCodes, authFile, outputDir, concurrency = 2, sharedLogger = null) {
        this.systemCodes = systemCodes;
        this.authFile = authFile;
        this.outputDir = outputDir;
        this.concurrency = concurrency;

        // Setup shared logger
        if (sharedLogger) {
            this.logger = sharedLogger;
        } else {
            this.logger = winston.createLogger({
                level: 'info',
                format: winston.format.combine(
                    winston.format.timestamp(),
                    winston.format.printf(({ timestamp, level, message }) => {
                        return `[${timestamp}] [POOL] ${level.toUpperCase()}: ${message}`;
                    })
                ),
                transports: [
                    new winston.transports.Console(),
                    new winston.transports.File({
                        filename: path.join(outputDir, '../logs/pool.log')
                    })
                ]
            });
        }

        // State
        this.browser = null;
        this.queue = [...systemCodes]; // Copy of system codes to process
        this.activeWorkers = new Map(); // { systemCode: SystemScraper }
        this.completedSystems = [];
        this.failedSystems = [];
    }

    /**
     * Main execution - launches browser and starts worker pool
     * @returns {Promise<object>} Results with completed and failed systems
     */
    async run() {
        this.logger.info(`🚀 Starting WorkerPool with ${this.concurrency} concurrent workers`);
        this.logger.info(`📋 Queue: ${this.systemCodes.join(', ')}`);

        try {
            // 1. Launch browser once (shared across all systems)
            await this.launchBrowser();

            // 2. Fill initial workers
            while (this.activeWorkers.size < this.concurrency && this.queue.length > 0) {
                await this.spawnWorker();
            }

            // 3. Wait for all workers to complete
            await this.waitForCompletion();

            // 4. Cleanup
            await this.cleanup();

            // 5. Report results
            this.reportResults();

            return {
                completed: this.completedSystems,
                failed: this.failedSystems
            };
        } catch (error) {
            this.logger.error(`Critical pool error: ${error.message}`);
            await this.cleanup();
            throw error;
        }
    }

    /**
     * Launch browser once for all workers
     * @returns {Promise<void>}
     */
    async launchBrowser() {
        this.logger.info('🌐 Launching Playwright browser...');
        this.browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        this.logger.info('✓ Browser launched');
    }

    /**
     * Spawn a new worker for the next system in queue
     * @returns {Promise<void>}
     */
    async spawnWorker() {
        if (this.queue.length === 0) {
            return; // No more systems
        }

        const systemCode = this.queue.shift();
        const systemConfig = SYSTEMS[systemCode];

        this.logger.info(`▶️  Spawning worker for ${systemConfig.emoji} ${systemConfig.name}`);

        const scraper = new SystemScraper(
            this.browser,
            systemCode,
            this.authFile,
            this.outputDir,
            this.logger
        );

        this.activeWorkers.set(systemCode, scraper);

        // Run scraper and handle completion
        scraper.run()
            .then(() => {
                this.logger.info(`✓ Completed: ${systemConfig.emoji} ${systemConfig.name}`);
                this.completedSystems.push(systemCode);
                this.activeWorkers.delete(systemCode);
                // Spawn next worker if queue has items
                if (this.queue.length > 0) {
                    this.spawnWorker().catch(e => {
                        this.logger.error(`Failed to spawn next worker: ${e.message}`);
                    });
                }
            })
            .catch(error => {
                this.logger.error(`✗ Failed: ${systemConfig.emoji} ${systemConfig.name} - ${error.message}`);
                this.failedSystems.push(systemCode);
                this.activeWorkers.delete(systemCode);
                // Spawn next worker even if this one failed
                if (this.queue.length > 0) {
                    this.spawnWorker().catch(e => {
                        this.logger.error(`Failed to spawn next worker: ${e.message}`);
                    });
                }
            });
    }

    /**
     * Wait for all workers to complete
     * @returns {Promise<void>}
     */
    async waitForCompletion() {
        return new Promise((resolve) => {
            const checkCompletion = () => {
                if (this.activeWorkers.size === 0 && this.queue.length === 0) {
                    resolve();
                } else {
                    // Check again in 1 second
                    setTimeout(checkCompletion, 1000);
                }
            };
            checkCompletion();
        });
    }

    /**
     * Cleanup - close browser
     * @returns {Promise<void>}
     */
    async cleanup() {
        if (this.browser) {
            try {
                this.logger.info('🔌 Closing browser...');
                await this.browser.close();
                this.logger.info('✓ Browser closed');
            } catch (error) {
                this.logger.warn(`Error closing browser: ${error.message}`);
            }
        }
    }

    /**
     * Report final results
     */
    reportResults() {
        this.logger.info('');
        this.logger.info('═══════════════════════════════════════════════════════');
        this.logger.info('SCRAPING COMPLETE');
        this.logger.info('═══════════════════════════════════════════════════════');

        if (this.completedSystems.length > 0) {
            this.logger.info(`✓ Completed (${this.completedSystems.length}):`);
            this.completedSystems.forEach(code => {
                const config = SYSTEMS[code];
                this.logger.info(`  ${config.emoji} ${config.name}`);
            });
        }

        if (this.failedSystems.length > 0) {
            this.logger.info(`✗ Failed (${this.failedSystems.length}):`);
            this.failedSystems.forEach(code => {
                const config = SYSTEMS[code];
                this.logger.info(`  ${config.emoji} ${config.name}`);
            });
        }

        this.logger.info('═══════════════════════════════════════════════════════');
        this.logger.info(`Total: ${this.completedSystems.length} completed, ${this.failedSystems.length} failed`);
        this.logger.info('═══════════════════════════════════════════════════════');
    }
}

module.exports = WorkerPool;
