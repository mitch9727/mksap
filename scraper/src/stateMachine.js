// scraper/src/stateMachine.js
const { chromium } = require('playwright');
const path = require('path');
const winston = require('winston');
const selectors = require('./selectors');
const fs = require('fs');

// Import States (to be created)
const InitState = require('./states/init');
const LoginState = require('./states/login');
const NavigateState = require('./states/navigate');
const ProcessQuestionsState = require('./states/process_questions');

class ScraperStateMachine {
    constructor() {
        this.browser = null;
        this.context = null;
        this.page = null;
        this.config = {
            baseUrl: 'https://mksap.acponline.org', // Confirm URL
            headless: true, // Default to true, overridden by Auth check
            authFile: path.join(__dirname, '../config/auth.json'),
            outputDir: path.join(__dirname, '../output'),
            maxRetries: 3
        };
        
        // Logger Setup
        this.logger = winston.createLogger({
            level: 'info',
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.simple()
            ),
            transports: [
                new winston.transports.Console(),
                new winston.transports.File({ filename: 'scraper/logs/scraper.log' })
            ]
        });

        // State Map
        this.states = {
            INIT: new InitState(this),
            LOGIN: new LoginState(this),
            NAVIGATE: new NavigateState(this),
            PROCESS_QUESTIONS: new ProcessQuestionsState(this)
        };
        
        this.currentState = 'INIT';
    }

    async run() {
        this.logger.info('Starting Scraper State Machine...');
        
        while (this.currentState !== 'EXIT') {
            this.logger.info(`Entering State: ${this.currentState}`);
            
            try {
                const stateHandler = this.states[this.currentState];
                if (!stateHandler) {
                    throw new Error(`Unknown state: ${this.currentState}`);
                }

                // Execute Step
                const nextState = await stateHandler.execute();
                
                // Transition
                this.currentState = nextState;

            } catch (error) {
                this.logger.error(`Critical Error in ${this.currentState}: ${error.message}`);
                await this.handleError(error);
                // For now, exit on critical error locally
                this.currentState = 'EXIT';
            }
        }

        await this.cleanup();
        this.logger.info('Scraper Finished.');
    }

    async handleError(error) {
        // Screenshot capability
        if (this.page) {
            const shotPath = path.join(this.config.outputDir, 'logs', `error_${Date.now()}.png`);
            await this.page.screenshot({ path: shotPath }).catch(() => {});
            this.logger.error(`Screenshot saved to ${shotPath}`);
        }
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
    }
}

module.exports = ScraperStateMachine;
