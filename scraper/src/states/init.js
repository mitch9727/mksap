// scraper/src/states/init.js
const BaseState = require('./base');
const fs = require('fs');

class InitState extends BaseState {
    async execute() {
        this.logger.info('Initializing Context for System...');

        // Browser is already created by WorkerPool and passed to SystemScraper
        // This state creates a new context for this system (isolated cookies, storage, etc.)

        // Check if auth exists to determine if we need headful mode
        const authExists = fs.existsSync(this.machine.authFile);

        if (!authExists) {
            this.logger.info('No auth file found. First run will require manual login.');
        }

        try {
            // Create a new context for this system
            // Each system gets its own context but they share the browser process
            this.machine.context = await this.machine.browser.newContext({
                viewport: { width: 1280, height: 800 }
            });

            // Create a page in this context
            this.machine.page = await this.machine.context.newPage();

            this.logger.info('Context and page created successfully');
        } catch (error) {
            this.logger.error(`Failed to create context: ${error.message}`);
            throw error;
        }

        return 'LOGIN';
    }
}

module.exports = InitState;
