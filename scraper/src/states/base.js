// scraper/src/states/base.js
class BaseState {
    constructor(machine) {
        this.machine = machine;
    }

    get logger() {
        return this.machine.logger;
    }

    get page() {
        return this.machine.page;
    }

    async execute() {
        throw new Error('Execute method must be implemented by subclass');
    }

    async safeClick(selector, timeout = 5000) {
        try {
            await this.page.waitForSelector(selector, { timeout });
            await this.page.click(selector);
            return true;
        } catch (e) {
            this.logger.warn(`Failed to click ${selector}: ${e.message}`);
            return false;
        }
    }
}

module.exports = BaseState;
