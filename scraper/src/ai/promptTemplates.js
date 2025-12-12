/**
 * Prompt Templates
 *
 * Reusable prompt templates for Claude Code analysis tasks.
 * Standardizes prompts for error diagnosis, authentication analysis, etc.
 *
 * @module promptTemplates
 */

/**
 * Build error diagnosis prompt
 *
 * @param {Object} params - Prompt parameters
 * @param {string} params.errorMessage - Error message
 * @param {string} params.errorStack - Error stack trace (optional)
 * @param {string} params.state - Current scraper state
 * @param {Object} params.context - Additional context
 * @returns {string} Formatted prompt
 */
function buildErrorDiagnosisPrompt({ errorMessage, errorStack, state, context = {} }) {
  return `You are an expert web scraping debugger analyzing a Playwright automation error.

**Error Details:**
- Error Message: ${errorMessage}
- State Machine State: ${state}
- Question ID: ${context.questionId || 'unknown'}
- System: ${context.systemCode || 'unknown'}
- Operation: ${context.operation || 'unknown'}

${errorStack ? `**Stack Trace (first 5 lines):**\n${errorStack.split('\n').slice(0, 5).join('\n')}\n` : ''}

**Your Task:**
Analyze the screenshot (if provided) and error details to diagnose the root cause and suggest a fix.

**Common Scraping Error Patterns:**
1. **Modal/Dialog Errors:** Modal didn't open, wrong modal selected, content not loaded
2. **Selector Errors:** Element not found, not visible, multiple matches
3. **Timing Errors:** Timeout, network delay, animation in progress
4. **Navigation Errors:** Page navigated, session expired, rate limited
5. **Content Extraction:** Element empty, unexpected HTML structure

**Output Requirements:**
Return ONLY valid JSON with this structure:
{
  "diagnosis": "Brief description (e.g., 'Modal did not open')",
  "likelyRootCause": "one of: modal_not_opened | selector_not_found | timeout_network | session_expired | unknown",
  "confidence": 0.0-1.0,
  "suggestedFix": "Specific code fix (e.g., 'Add waitForLoadState(networkidle) before clicking')",
  "shouldRetry": true/false,
  "suggestedRetryDelay": milliseconds (0 if shouldRetry is false),
  "reasoning": "Explain what you see and why this is the root cause"
}`;
}

/**
 * Build authentication analysis prompt
 *
 * @param {Object} params - Prompt parameters
 * @param {string} params.pageUrl - Current page URL
 * @param {string} params.authState - Current auth state
 * @param {string} params.error - Error message (optional)
 * @param {Array} params.previousAttempts - Previous login attempts (optional)
 * @returns {string} Formatted prompt
 */
function buildAuthAnalysisPrompt({ pageUrl, authState, error, previousAttempts = [] }) {
  return `You are an authentication diagnostician analyzing a login page screenshot.

**Context:**
- Page URL: ${pageUrl}
- Current Auth State: ${authState}
${error ? `- Error Message: ${error}` : ''}
${previousAttempts.length > 0 ? `- Previous Attempts: ${previousAttempts.length} failed` : ''}

**Your Task:**
Analyze the screenshot to determine the current authentication state and detect any challenges.

**Detection Tasks:**
1. **Logged In Status:** Look for greeting text, dashboard elements, profile icons
2. **Challenge Detection:** Identify CAPTCHA, 2FA, email verification, security questions
3. **Login Form State:** Check for error messages, validation warnings
4. **Session State:** Detect expired session, invalid cookies, re-authentication needed

**Output Requirements:**
Return ONLY valid JSON with this structure:
{
  "diagnosis": "Brief description (e.g., 'Session expired - cookie timeout', 'CAPTCHA present')",
  "authState": "one of: logged_in | requires_login | requires_relogin | captcha_required | 2fa_required | session_expired | unknown",
  "confidence": 0.0-1.0,
  "detectedChallenges": ["array of: captcha, 2fa, email_verification, security_questions, rate_limit"],
  "suggestedAction": "one of: proceed | manual_login_required | wait_and_retry | clear_cookies",
  "canAutoResolve": true/false,
  "reasoning": "Explain what you see in the screenshot",
  "instructions": "Specific instructions for user/system"
}`;
}

/**
 * Build data validation prompt
 *
 * @param {Object} params - Prompt parameters
 * @param {Object} params.data - Extracted data
 * @param {Object} params.schema - Expected schema
 * @param {string} params.questionId - Question ID
 * @returns {string} Formatted prompt
 */
function buildDataValidationPrompt({ data, schema, questionId }) {
  return `You are a data quality validator for medical MCQ extraction.

**Task:** Validate the extracted data for completeness and correctness.

**Question ID:** ${questionId}

**Extracted Data:**
${JSON.stringify(data, null, 2)}

**Expected Schema:**
Required fields: ${schema.required.join(', ')}
Optional fields: ${schema.optional.join(', ')}

**Validation Checks:**
1. **Presence:** All required fields present and non-empty
2. **Format:** Fields match expected patterns (ID format, date format, etc.)
3. **Completeness:** Text fields are not truncated or suspiciously short
4. **Semantic:** Content makes medical sense (e.g., Reference has PMID/DOI)

**Output Requirements:**
Return ONLY valid JSON with this structure:
{
  "isValid": true/false,
  "completeness": 0.0-1.0,
  "issues": [
    {
      "field": "field name",
      "severity": "error | warning",
      "message": "description of issue",
      "suggestion": "how to fix"
    }
  ],
  "semanticChecks": {
    "referencePresent": true/false,
    "educationalObjectiveMakesSense": true/false,
    "answerAndCritiqueIsComplete": true/false
  }
}`;
}

/**
 * Build selector validation prompt
 *
 * @param {Object} params - Prompt parameters
 * @param {string} params.selector - CSS selector to validate
 * @param {string} params.expectedType - Expected element type
 * @param {number} params.foundCount - Number of elements found
 * @returns {string} Formatted prompt
 */
function buildSelectorValidationPrompt({ selector, expectedType, foundCount }) {
  return `You are a CSS selector validator for web scraping.

**Task:** Validate if the selector correctly identifies the target element.

**Selector:** \`${selector}\`
**Expected Element Type:** ${expectedType}
**Elements Found:** ${foundCount}

**Analysis Required:**
1. Does the selector uniquely identify the target element?
2. Is the selector robust (won't break with minor HTML changes)?
3. If multiple elements found, are they all of the expected type?
4. If no elements found, what alternative selectors might work?

**Look at the screenshot to:**
- Verify the element exists on the page
- Check if it's visible or hidden
- Identify unique attributes (data-testid, aria-label, etc.)

**Output Requirements:**
Return ONLY valid JSON with this structure:
{
  "isValid": true/false,
  "confidence": 0.0-1.0,
  "suggestedSelector": "alternative selector if current is invalid, otherwise null",
  "reasoning": "explanation of validation result",
  "alternatives": ["array of alternative selectors"]
}`;
}

module.exports = {
  buildErrorDiagnosisPrompt,
  buildAuthAnalysisPrompt,
  buildDataValidationPrompt,
  buildSelectorValidationPrompt
};
