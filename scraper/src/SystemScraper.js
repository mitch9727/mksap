/**
 * SystemScraper - System-aware state machine for scraping a single organ system
 *
 * Manages the scraping lifecycle for one medical system using Playwright contexts
 * instead of separate browser instances. This allows multiple systems to be scraped
 * in parallel while sharing the same browser process.
 *
 * State Machine Flow:
 * INIT → LOGIN → NAVIGATE → PROCESS_QUESTIONS → EXIT
 *
 * @class SystemScraper
 * @param {object} browser - Playwright browser instance (shared across systems)
 * @param {string} systemCode - System code (e.g., 'cv', 'en', 'pmcc')
 * @param {string} authFile - Path to auth.json for session persistence
 * @param {string} outputDir - Base output directory
 * @param {object} sharedLogger - Shared logger instance (optional)
 */

const path = require('path');
const winston = require('winston');
const selectors = require('./selectors');
const SYSTEMS = require('../config/systems');

// Import States
const InitState = require('./states/init');
const LoginState = require('./states/login');
const NavigateState = require('./states/navigate');
const ProcessQuestionsState = require('./states/process_questions');

class SystemScraper {
    constructor(browser, systemCode, authFile, outputDir, sharedLogger = null) {
        this.browser = browser;
        this.systemCode = systemCode;
        this.systemConfig = SYSTEMS[systemCode];

        if (!this.systemConfig) {
            throw new Error(`Unknown system code: ${systemCode}`);
        }

        this.authFile = authFile;
        this.outputDir = outputDir;
        this.context = null;
        this.page = null;

        this.config = {
            baseUrl: 'https://mksap.acponline.org',
            headless: true,
            maxRetries: 3
        };

        // Logger Setup - use shared logger or create system-specific one
        if (sharedLogger) {
            this.logger = sharedLogger;
        } else {
            this.logger = winston.createLogger({
                level: 'info',
                format: winston.format.combine(
                    winston.format.timestamp(),
                    winston.format.printf(({ timestamp, level, message }) => {
                        return `[${timestamp}] [${this.systemCode.toUpperCase()}] ${level.toUpperCase()}: ${message}`;
                    })
                ),
                transports: [
                    new winston.transports.Console(),
                    new winston.transports.File({
                        filename: path.join(outputDir, `../logs/${systemCode}.log`)
                    })
                ]
            });
        }

        // State Map - each state instance receives 'this' (SystemScraper instance)
        this.states = {
            INIT: new InitState(this),
            LOGIN: new LoginState(this),
            NAVIGATE: new NavigateState(this),
            PROCESS_QUESTIONS: new ProcessQuestionsState(this)
        };

        this.currentState = 'INIT';
    }

    /**
     * Main execution loop - runs the state machine for this system
     * @returns {Promise<void>}
     */
    async run() {
        this.logger.info(`${this.systemConfig.emoji} Starting ${this.systemConfig.name} scraper...`);

        while (this.currentState !== 'EXIT') {
            this.logger.info(`Entering state: ${this.currentState}`);

            try {
                const stateHandler = this.states[this.currentState];
                if (!stateHandler) {
                    throw new Error(`Unknown state: ${this.currentState}`);
                }

                // Execute state and get next state
                const nextState = await stateHandler.execute();
                this.currentState = nextState;

            } catch (error) {
                this.logger.error(`Critical error in ${this.currentState}: ${error.message}`);
                await this.handleError(error);
                this.currentState = 'EXIT';
            }
        }

        await this.cleanup();
        this.logger.info(`${this.systemConfig.emoji} ${this.systemConfig.name} scraper finished.`);
    }

    /**
     * Handle errors with screenshot capture
     * @param {Error} error
     * @returns {Promise<void>}
     */
    async handleError(error) {
        if (this.page) {
            try {
                const errorDir = path.join(this.outputDir, '../logs/errors');
                const fs = require('fs');
                if (!fs.existsSync(errorDir)) {
                    fs.mkdirSync(errorDir, { recursive: true });
                }
                const shotPath = path.join(errorDir, `${this.systemCode}_error_${Date.now()}.png`);
                await this.page.screenshot({ path: shotPath });
                this.logger.error(`Error screenshot saved to ${shotPath}`);
            } catch (screenshotError) {
                this.logger.warn(`Failed to capture error screenshot: ${screenshotError.message}`);
            }
        }
    }

    /**
     * Cleanup resources - close context (browser stays open for other systems)
     * @returns {Promise<void>}
     */
    async cleanup() {
        if (this.context) {
            try {
                await this.context.close();
                this.logger.info('Context closed successfully');
            } catch (error) {
                this.logger.warn(`Error closing context: ${error.message}`);
            }
        }
    }

    /**
     * Get the system's output directory
     * @returns {string} Path to system-specific output folder
     */
    getSystemOutputDir() {
        return path.join(this.outputDir, this.systemConfig.folder);
    }
}

module.exports = SystemScraper;
