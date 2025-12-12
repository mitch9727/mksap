/**
 * Authentication Assistant Skill
 *
 * Analyzes authentication state using Claude Code vision to diagnose login issues,
 * detect challenges (CAPTCHA, 2FA), and suggest appropriate actions.
 *
 * Uses Claude Code headless mode - NO API KEY REQUIRED.
 *
 * @module authenticationAssistant
 */

const { claudeCodeAnalyze, isClaudeCodeAvailable } = require('../ai/claudeCodeClient');
const { buildAuthAnalysisPrompt } = require('../ai/promptTemplates');

/**
 * Analyze authentication state from screenshot and page context
 *
 * @param {Object} params - Analysis parameters
 * @param {string} params.screenshot - Screenshot (base64 or file path)
 * @param {string} params.pageUrl - Current page URL
 * @param {string} params.html - Page HTML content (optional)
 * @param {string} params.authState - Current auth state (optional)
 * @param {string} params.error - Error message if login failed (optional)
 * @param {Array} params.previousAttempts - History of previous login attempts (optional)
 * @returns {Promise<Object>} Analysis result
 *
 * @throws {Error} 'USAGE_LIMIT_REACHED' when daily limit hit
 * @throws {Error} 'CLAUDE_CODE_UNAVAILABLE' when CLI not found
 *
 * @example
 * const analysis = await analyzeAuthenticationState({
 *   screenshot: screenshotBase64,
 *   pageUrl: 'https://mksap.acponline.org/login',
 *   authState: 'login_failed'
 * });
 */
async function analyzeAuthenticationState(params) {
  const {
    screenshot,
    pageUrl = 'unknown',
    html = null,
    authState = 'unknown',
    error = null,
    previousAttempts = []
  } = params;

  // Check if Claude Code is available
  if (!isClaudeCodeAvailable()) {
    console.warn('[authenticationAssistant] Claude Code unavailable, using basic fallback');
    return basicAuthFallback(authState);
  }

  try {
    // Build analysis prompt
    const prompt = buildAuthAnalysisPrompt({
      pageUrl,
      authState,
      error,
      previousAttempts
    });

    // Define expected schema
    const schema = {
      required: [
        'diagnosis',
        'authState',
        'confidence',
        'detectedChallenges',
        'suggestedAction',
        'canAutoResolve',
        'reasoning',
        'instructions'
      ]
    };

    // Call Claude Code headless mode with vision
    const analysis = await claudeCodeAnalyze({
      task: 'analyze-authentication',
      prompt,
      screenshot,
      schema
    });

    // Normalize confidence to 0-1
    if (analysis.confidence > 1) {
      analysis.confidence = analysis.confidence / 100;
    }

    return analysis;
  } catch (aiError) {
    // Handle usage limit reached
    if (aiError.message === 'USAGE_LIMIT_REACHED') {
      throw aiError; // Propagate to caller
    }

    console.warn(`[authenticationAssistant] AI analysis failed: ${aiError.message}`);
    return basicAuthFallback(authState);
  }
}

/**
 * Basic authentication fallback (when AI unavailable)
 *
 * @param {string} authState - Current auth state
 * @returns {Object} Basic auth analysis
 */
function basicAuthFallback(authState) {
  return {
    diagnosis: 'Unable to analyze authentication state (AI unavailable)',
    authState: authState || 'unknown',
    confidence: 0,
    detectedChallenges: [],
    suggestedAction: 'manual_login_required',
    canAutoResolve: false,
    reasoning: 'Claude Code unavailable - manual inspection required',
    instructions: 'Check login page manually and ensure cookies are valid'
  };
}

/**
 * Check session health during scraping
 *
 * @param {Page} page - Playwright page object
 * @param {Object} options - Check options
 * @param {string} options.loginSelector - CSS selector for login indicator
 * @returns {Promise<Object>} Session health status
 *
 * @example
 * const health = await checkSessionHealth(page, {
 *   loginSelector: 'span[data-testid="greeting"]'
 * });
 *
 * if (health.sessionExpired) {
 *   // Trigger re-authentication
 * }
 */
async function checkSessionHealth(page, options = {}) {
  const { loginSelector = 'span[data-testid="greeting"]' } = options;

  try {
    // Check if login indicator is present
    const isLoggedIn = await page.locator(loginSelector).count() > 0;

    if (isLoggedIn) {
      return {
        sessionExpired: false,
        isHealthy: true,
        message: 'Session is active'
      };
    }

    // Not logged in - take screenshot and analyze
    const screenshot = await page.screenshot({ encoding: 'base64' });

    const analysis = await analyzeAuthenticationState({
      screenshot,
      pageUrl: page.url(),
      authState: 'session_check'
    });

    return {
      sessionExpired: analysis.authState === 'session_expired' || analysis.authState === 'requires_relogin',
      isHealthy: analysis.authState === 'logged_in',
      analysis
    };
  } catch (error) {
    // Handle usage limit
    if (error.message === 'USAGE_LIMIT_REACHED') {
      throw error; // Propagate to scraper
    }

    console.error(`[authenticationAssistant] Session health check failed: ${error.message}`);

    return {
      sessionExpired: false,
      isHealthy: false,
      error: error.message,
      message: 'Unable to determine session health'
    };
  }
}

module.exports = {
  analyzeAuthenticationState,
  checkSessionHealth
};
