// scraper/src/states/login.js
const BaseState = require('./base');
const fs = require('fs');
const path = require('path');
const selectors = require('../selectors');
const { analyzeAuthenticationState } = require('../skills/authenticationAssistant');

class LoginState extends BaseState {
    async execute() {
        const authFile = this.machine.authFile;

        // Check if auth exists
        if (fs.existsSync(authFile)) {
            this.logger.info('Loading existing auth state...');

            try {
                // Close the current context and recreate it with storageState
                // This ensures both cookies and localStorage are properly restored
                await this.machine.context.close();

                this.machine.context = await this.machine.browser.newContext({
                    storageState: authFile,
                    viewport: { width: 1280, height: 800 }
                });

                this.machine.page = await this.machine.context.newPage();

                // Validate Session by checking for logged-in indicator
                await this.page.goto(this.machine.config.baseUrl);
                try {
                    await this.page.waitForSelector(selectors.login.loggedInIndicator, { timeout: 5000 });
                    this.logger.info('✓ Session valid, using saved auth.');
                    return 'NAVIGATE';
                } catch (e) {
                    this.logger.warn('Session invalid or expired. Re-login required.');

                    // Use AI to diagnose auth state
                    try {
                        const screenshot = await this.page.screenshot({ encoding: 'base64' });
                        const analysis = await analyzeAuthenticationState({
                            screenshot,
                            pageUrl: this.page.url(),
                            authState: 'session_expired'
                        });

                        this.logger.info(`Auth diagnosis: ${analysis.diagnosis}`);

                        if (analysis.detectedChallenges && analysis.detectedChallenges.length > 0) {
                            this.logger.warn(`Detected challenges: ${analysis.detectedChallenges.join(', ')}`);
                        }
                    } catch (aiError) {
                        // AI diagnosis failed - continue with manual login
                        this.logger.debug(`Auth analysis skipped: ${aiError.message}`);
                    }

                    // Fallthrough to manual login
                }
            } catch (error) {
                this.logger.warn(`Error loading auth: ${error.message}. Proceeding with manual login.`);
                // Fallthrough to manual login
            }
        }

        // --- Manual Login Flow ---
        this.logger.info('--- MANUAL LOGIN REQUIRED ---');
        this.logger.info('Please log in to MKSAP in the browser window.');
        this.logger.info('You have 5 minutes to complete login.');

        // Navigate to MKSAP (will redirect to login if needed)
        await this.page.goto(this.machine.config.baseUrl);

        // Wait for user to log in by detecting the logged-in indicator
        try {
            await this.page.waitForSelector(selectors.login.loggedInIndicator, { timeout: 300000 }); // 5 mins
        } catch (e) {
            // Login timed out - use AI to diagnose why
            try {
                const screenshot = await this.page.screenshot({ encoding: 'base64' });
                const analysis = await analyzeAuthenticationState({
                    screenshot,
                    pageUrl: this.page.url(),
                    authState: 'login_timeout',
                    error: 'User did not complete login within 5 minutes'
                });

                this.logger.error(`Login timeout diagnosis: ${analysis.diagnosis}`);

                if (analysis.detectedChallenges && analysis.detectedChallenges.includes('captcha')) {
                    throw new Error('Login failed: CAPTCHA detected. Please complete CAPTCHA and try again.');
                }

                if (analysis.suggestedAction) {
                    this.logger.info(`Suggested action: ${analysis.suggestedAction}`);
                }
            } catch (aiError) {
                // AI diagnosis failed
                this.logger.debug(`Auth analysis failed: ${aiError.message}`);
            }

            throw new Error('Login timed out. Please run the scraper again and complete login within 5 minutes.');
        }

        this.logger.info('✓ Login detected! Saving session...');
        await this.page.waitForTimeout(2000); // Wait for cookies to settle

        // Save auth state for future runs
        try {
            const state = await this.machine.context.storageState();
            // Ensure directory exists
            const authDir = path.dirname(authFile);
            if (!fs.existsSync(authDir)) {
                fs.mkdirSync(authDir, { recursive: true });
            }
            fs.writeFileSync(authFile, JSON.stringify(state, null, 2));
            this.logger.info(`Auth state saved to ${authFile}`);
        } catch (error) {
            this.logger.warn(`Failed to save auth state: ${error.message}. You may need to login again next time.`);
        }

        return 'NAVIGATE';
    }
}

module.exports = LoginState;
