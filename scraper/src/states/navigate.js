// scraper/src/states/navigate.js
const BaseState = require('./base');
const selectors = require('../selectors');

class NavigateState extends BaseState {
    async execute() {
        const systemCode = this.machine.systemCode;
        const systemName = this.machine.systemConfig.name;
        this.logger.info(`🔄 Navigating to ${systemName}...`);

        // 1. Ensure we're on MKSAP homepage
        if (!this.page.url().includes('mksap.acponline.org')) {
            this.logger.info('Navigating to MKSAP homepage...');
            await this.page.goto('https://mksap.acponline.org');
            await this.page.waitForLoadState('networkidle');
        }

        // 2. Click Question Bank link
        try {
            this.logger.info('Clicking Question Bank link...');
            await this.page.click(selectors.nav.questionBankLink);
            await this.page.waitForLoadState('networkidle');
        } catch (e) {
            this.logger.error('Failed to click Question Bank link');
            throw e;
        }

        // 3. Click system-specific link (e.g., Cardiovascular, Pulmonary, etc.)
        try {
            this.logger.info(`Clicking ${systemName}...`);
            const systemLinkSelector = selectors.nav.systemLink(systemCode);
            await this.page.click(systemLinkSelector);
            await this.page.waitForLoadState('networkidle');
        } catch (e) {
            this.logger.error(`Failed to click ${systemName}`);
            throw e;
        }

        // 4. Click Answered Questions for this system
        try {
            this.logger.info('Clicking Answered Questions...');
            const answeredQuestionsSelector = selectors.nav.answeredQuestionsLink(systemCode);
            await this.page.click(answeredQuestionsSelector);
            await this.page.waitForLoadState('networkidle');
        } catch (e) {
            this.logger.error('Failed to click Answered Questions');
            throw e;
        }

        // 5. Validate we are on the question list page
        try {
            this.logger.info('Validating question list loaded...');
            await this.page.waitForSelector(selectors.list.questionItem, { timeout: 30000 });
            this.logger.info(`✓ Question List loaded successfully for ${systemName}!`);
        } catch (e) {
            this.logger.error('Failed to load Question List.');
            throw e;
        }

        return 'PROCESS_QUESTIONS';
    }
}

module.exports = NavigateState;
