/**
 * Error Diagnostician Skill
 *
 * Analyzes errors using Claude Code vision to diagnose root causes
 * and suggest intelligent fixes. Enables smart retry logic.
 *
 * Uses Claude Code headless mode - NO API KEY REQUIRED.
 *
 * @module errorDiagnostician
 */

const { claudeCodeAnalyze, isClaudeCodeAvailable, getUsageLimitStatus } = require('../ai/claudeCodeClient');
const { buildErrorDiagnosisPrompt } = require('../ai/promptTemplates');

/**
 * Diagnose scraper error using AI analysis
 *
 * @param {Object} params - Diagnosis parameters
 * @param {Error} params.error - Error object
 * @param {string} params.state - Current state machine state
 * @param {string} params.screenshot - Screenshot (base64 or file path)
 * @param {string} params.html - Page HTML (optional)
 * @param {Object} params.context - Additional context
 * @returns {Promise<Object>} Diagnosis result
 *
 * @throws {Error} 'USAGE_LIMIT_REACHED' when daily limit hit
 *
 * @example
 * const diagnosis = await diagnoseError({
 *   error: new Error('Timeout waiting for modal'),
 *   state: 'PROCESS_QUESTIONS',
 *   screenshot: screenshotBase64,
 *   context: { questionId: 'CVMCQ24042', systemCode: 'cv' }
 * });
 */
async function diagnoseError(params) {
  const {
    error,
    state = 'unknown',
    screenshot,
    html = null,
    context = {}
  } = params;

  // Check if Claude Code is available
  if (!isClaudeCodeAvailable()) {
    console.warn('[errorDiagnostician] Claude Code unavailable, using basic fallback');
    return basicErrorDiagnosis(error);
  }

  try {
    // Build diagnosis prompt
    const prompt = buildErrorDiagnosisPrompt({
      errorMessage: error.message,
      errorStack: error.stack,
      state,
      context
    });

    // Define expected schema
    const schema = {
      required: [
        'diagnosis',
        'likelyRootCause',
        'confidence',
        'suggestedFix',
        'shouldRetry',
        'suggestedRetryDelay',
        'reasoning'
      ]
    };

    // Call Claude Code headless mode with vision
    const diagnosis = await claudeCodeAnalyze({
      task: 'diagnose-error',
      prompt,
      screenshot,
      schema
    });

    // Normalize confidence to 0-1
    if (diagnosis.confidence > 1) {
      diagnosis.confidence = diagnosis.confidence / 100;
    }

    // Ensure retryDelay is number
    diagnosis.suggestedRetryDelay = Number(diagnosis.suggestedRetryDelay) || 0;

    diagnosis.originalError = error.message;

    return diagnosis;
  } catch (aiError) {
    // Handle usage limit reached
    if (aiError.message === 'USAGE_LIMIT_REACHED') {
      throw aiError; // Propagate to caller
    }

    console.warn(`[errorDiagnostician] AI analysis failed: ${aiError.message}`);
    return basicErrorDiagnosis(error);
  }
}

/**
 * Basic error diagnosis fallback (when AI unavailable)
 *
 * @param {Error} error - Error object
 * @returns {Object} Basic diagnosis
 */
function basicErrorDiagnosis(error) {
  return {
    diagnosis: error.message,
    likelyRootCause: 'unknown',
    confidence: 0,
    suggestedFix: 'Check logs and screenshot for details',
    shouldRetry: false,
    suggestedRetryDelay: 0,
    reasoning: 'AI analysis unavailable - manual inspection required',
    originalError: error.message
  };
}

/**
 * Smart retry wrapper with AI-powered diagnosis
 *
 * @param {Function} fn - Async function to execute
 * @param {Object} options - Retry options
 * @param {Page} options.page - Playwright page object
 * @param {string} options.state - State machine state
 * @param {Object} options.context - Additional context
 * @param {number} options.maxRetries - Max retry attempts (default: 3)
 * @returns {Promise<any>} Result of fn()
 *
 * @throws {Error} 'USAGE_LIMIT_REACHED' when daily limit hit
 *
 * @example
 * const result = await smartRetry(
 *   async () => await page.click('button.submit'),
 *   {
 *     page,
 *     state: 'PROCESS_QUESTIONS',
 *     context: { questionId: 'CVMCQ24042', operation: 'click_submit' },
 *     maxRetries: 3
 *   }
 * );
 */
async function smartRetry(fn, options = {}) {
  const {
    page,
    state = 'unknown',
    context = {},
    maxRetries = 3
  } = options;

  let lastError = null;
  let attempts = 0;

  while (attempts <= maxRetries) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      attempts++;

      // Check if we already hit usage limit
      const usageStatus = getUsageLimitStatus();
      if (usageStatus.limitReached) {
        console.error('[errorDiagnostician] Usage limit already reached, aborting retry');
        throw new Error('USAGE_LIMIT_REACHED');
      }

      if (attempts > maxRetries) {
        throw error;
      }

      console.warn(
        `[errorDiagnostician] Attempt ${attempts}/${maxRetries} failed: ${error.message}`
      );

      // Take screenshot for diagnosis
      let screenshot = null;
      try {
        screenshot = await page.screenshot({ encoding: 'base64' });
      } catch (screenshotError) {
        console.warn(`Failed to capture screenshot: ${screenshotError.message}`);
      }

      // Diagnose error with AI
      let diagnosis;
      try {
        diagnosis = await diagnoseError({
          error,
          state,
          screenshot,
          context
        });

        console.log(`[errorDiagnostician] Diagnosis: ${diagnosis.diagnosis}`);
        console.log(`[errorDiagnostician] Suggested fix: ${diagnosis.suggestedFix}`);
        console.log(`[errorDiagnostician] Should retry: ${diagnosis.shouldRetry}`);
      } catch (diagnosisError) {
        // Handle usage limit reached during diagnosis
        if (diagnosisError.message === 'USAGE_LIMIT_REACHED') {
          throw diagnosisError; // Propagate to scraper
        }

        // Use fallback diagnosis if AI fails
        diagnosis = basicErrorDiagnosis(error);
      }

      // Check if error is retryable
      if (!diagnosis.shouldRetry) {
        console.error(
          `[errorDiagnostician] Error is not retryable. Aborting. ` +
          `Reason: ${diagnosis.reasoning}`
        );
        throw error;
      }

      // Wait before retry
      if (diagnosis.suggestedRetryDelay > 0) {
        console.log(
          `[errorDiagnostician] Waiting ${diagnosis.suggestedRetryDelay}ms before retry...`
        );
        await new Promise(resolve => setTimeout(resolve, diagnosis.suggestedRetryDelay));
      }
    }
  }

  throw lastError;
}

module.exports = {
  diagnoseError,
  smartRetry
};
