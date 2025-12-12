/**
 * Hybrid AI Client - Claude Code + API Key Fallback
 *
 * Primary: Claude Code CLI (headless mode) - NO API KEY REQUIRED
 * Fallback: Anthropic API (when Claude Code limit hit or unavailable)
 *
 * Handles:
 * - Automatic mode switching (CLI → API)
 * - Screenshot temp file management
 * - Usage limit detection (daily limits)
 * - Cost tracking for API usage
 * - Graceful degradation
 *
 * @module claudeCodeClient
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const { saveTempScreenshot, cleanupTempFile } = require('./tempFileManager');

// Anthropic SDK (lazy loaded)
let Anthropic = null;
let anthropicClient = null;

// Track usage limit state
let claudeCodeLimitReached = false;
let limitReachedTimestamp = null;

// Track which mode is active
let currentMode = 'claude-code'; // 'claude-code' | 'api-key' | 'fallback'

// Cost tracking (API key usage only)
let apiCostTotal = 0;
let apiRequestCount = 0;

/**
 * Analyze task using AI (automatically chooses best available method)
 *
 * Priority:
 * 1. Claude Code CLI (free, uses IDE subscription)
 * 2. Anthropic API (paid, requires API key)
 * 3. Basic fallback (no AI)
 *
 * @param {Object} params - Analysis parameters
 * @param {string} params.task - Task identifier
 * @param {string} params.prompt - Analysis prompt
 * @param {string} params.screenshot - Screenshot path or base64 (optional)
 * @param {Object} params.schema - Expected output schema (optional)
 * @param {number} params.timeout - Timeout in ms (default: 120000)
 * @returns {Promise<Object>} Parsed result with metadata
 *
 * @throws {Error} 'USAGE_LIMIT_REACHED' when all methods exhausted
 */
async function claudeCodeAnalyze({ task, prompt, screenshot, schema, timeout = 120000 }) {
  let screenshotPath = null;
  let tempFile = null;

  try {
    // Handle screenshot conversion
    if (screenshot) {
      if (screenshot.startsWith('data:image') || screenshot.startsWith('/9j/')) {
        tempFile = await saveTempScreenshot(screenshot);
        screenshotPath = tempFile;
      } else {
        screenshotPath = screenshot;
      }
    }

    // Try Claude Code CLI first (if not already hit limit)
    if (!claudeCodeLimitReached && isClaudeCodeAvailable()) {
      try {
        console.log(`[AI] Using Claude Code CLI for: ${task}`);
        const result = await analyzeWithClaudeCode({ prompt, screenshotPath, schema, timeout });
        currentMode = 'claude-code';
        return { ...result, mode: 'claude-code', cost: 0 };
      } catch (error) {
        if (error.message === 'USAGE_LIMIT_REACHED') {
          claudeCodeLimitReached = true;
          limitReachedTimestamp = new Date().toISOString();
          console.warn(`[AI] ⚠️  Claude Code usage limit reached at ${limitReachedTimestamp}`);

          // Try API key fallback
          if (hasAPIKey()) {
            console.log('[AI] Switching to API key fallback (Claude Code limit reached)');
            const result = await analyzeWithAPIKey({ prompt, screenshotPath, schema });
            currentMode = 'api-key';
            return result;
          }

          // No API key available
          throw error;
        }

        // Other error - try API key fallback
        console.warn(`[AI] Claude Code failed: ${error.message}`);
        if (hasAPIKey()) {
          console.log('[AI] Switching to API key fallback (Claude Code error)');
          const result = await analyzeWithAPIKey({ prompt, screenshotPath, schema });
          currentMode = 'api-key';
          return result;
        }

        throw error;
      }
    }

    // Claude Code unavailable or limit reached - try API key
    if (hasAPIKey()) {
      console.log(`[AI] Using API key for: ${task} (Claude Code unavailable)`);
      const result = await analyzeWithAPIKey({ prompt, screenshotPath, schema });
      currentMode = 'api-key';
      return result;
    }

    // No AI available
    throw new Error('CLAUDE_CODE_UNAVAILABLE');
  } finally {
    // Clean up temp screenshot
    if (tempFile) {
      await cleanupTempFile(tempFile);
    }
  }
}

/**
 * Analyze with Claude Code CLI (subprocess)
 */
async function analyzeWithClaudeCode({ prompt, screenshotPath, schema, timeout }) {
  const promptWithScreenshot = screenshotPath
    ? `![Screenshot](${screenshotPath})\n\n${prompt}`
    : prompt;

  const schemaInstruction = schema
    ? `\n\nIMPORTANT: Respond with ONLY valid JSON matching this schema:\n${JSON.stringify(schema, null, 2)}`
    : '';

  const fullPrompt = promptWithScreenshot + schemaInstruction;

  // Escape for shell
  const escapedPrompt = fullPrompt
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n');

  const command = `claude -p "${escapedPrompt}" --output-format json`;

  try {
    const output = execSync(command, {
      encoding: 'utf8',
      cwd: path.join(__dirname, '../../'),
      timeout: timeout,
      maxBuffer: 10 * 1024 * 1024,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    const result = parseStructuredResponse(output, schema);
    return result;
  } catch (error) {
    if (isUsageLimitError(error)) {
      throw new Error('USAGE_LIMIT_REACHED');
    }
    throw error;
  }
}

/**
 * Analyze with Anthropic API (external API key)
 */
async function analyzeWithAPIKey({ prompt, screenshotPath, schema }) {
  // Lazy load Anthropic SDK
  if (!Anthropic) {
    Anthropic = require('@anthropic-ai/sdk');
  }

  // Initialize client if needed
  if (!anthropicClient) {
    anthropicClient = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY
    });
  }

  try {
    const messages = [];

    // Build message content
    const content = [];

    // Add screenshot if present
    if (screenshotPath) {
      const imageBuffer = fs.readFileSync(screenshotPath);
      const base64Image = imageBuffer.toString('base64');

      content.push({
        type: 'image',
        source: {
          type: 'base64',
          media_type: 'image/png',
          data: base64Image
        }
      });
    }

    // Add prompt
    content.push({
      type: 'text',
      text: schema
        ? `${prompt}\n\nIMPORTANT: Respond with ONLY valid JSON matching this schema:\n${JSON.stringify(schema, null, 2)}`
        : prompt
    });

    messages.push({
      role: 'user',
      content
    });

    // Call API
    const response = await anthropicClient.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4096,
      temperature: 0,
      messages
    });

    // Calculate cost
    const inputTokens = response.usage.input_tokens;
    const outputTokens = response.usage.output_tokens;
    const cost = (inputTokens / 1_000_000 * 3) + (outputTokens / 1_000_000 * 15);

    apiCostTotal += cost;
    apiRequestCount++;

    console.log(`[AI] API usage: ${inputTokens} in, ${outputTokens} out, $${cost.toFixed(4)}`);

    // Parse response
    const text = response.content[0].text;
    const result = parseStructuredResponse(text, schema);

    return {
      ...result,
      mode: 'api-key',
      cost,
      usage: { inputTokens, outputTokens }
    };
  } catch (error) {
    console.error(`[AI] API call failed: ${error.message}`);
    throw error;
  }
}

/**
 * Check if Claude Code CLI is available
 */
function isClaudeCodeAvailable() {
  try {
    execSync('which claude', { encoding: 'utf8', stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if API key is available
 */
function hasAPIKey() {
  return !!process.env.ANTHROPIC_API_KEY;
}

/**
 * Detect if error is due to usage limit
 */
function isUsageLimitError(error) {
  const errorMessage = error.message || '';
  const errorOutput = error.stderr || error.stdout || '';

  const usageLimitPatterns = [
    /usage limit/i,
    /rate limit/i,
    /quota exceeded/i,
    /too many requests/i,
    /limit reached/i,
    /daily limit/i,
    /hourly limit/i,
    /429/,
    /overloaded_error/i
  ];

  return usageLimitPatterns.some(pattern =>
    pattern.test(errorMessage) || pattern.test(errorOutput)
  );
}

/**
 * Parse structured JSON response
 */
function parseStructuredResponse(output, schema) {
  try {
    // Try parsing entire output first
    try {
      return JSON.parse(output);
    } catch {
      // Fall back to extraction
    }

    // Extract JSON from markdown code blocks
    const jsonMatch = output.match(/```json\s*(\{[\s\S]*?\})\s*```/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[1]);
    }

    // Extract any JSON object
    const objectMatch = output.match(/\{[\s\S]*\}/);
    if (objectMatch) {
      return JSON.parse(objectMatch[0]);
    }

    throw new Error('No JSON found in output');
  } catch (parseError) {
    console.error(`[AI] Parse failed: ${parseError.message}`);
    return {
      error: 'parse_failed',
      message: parseError.message,
      rawOutput: output.substring(0, 1000)
    };
  }
}

/**
 * Get usage status and statistics
 */
function getUsageStatus() {
  return {
    claudeCodeLimitReached,
    limitReachedTimestamp,
    currentMode,
    apiCostTotal,
    apiRequestCount,
    avgCostPerRequest: apiRequestCount > 0 ? apiCostTotal / apiRequestCount : 0,
    hasAPIKeyConfigured: hasAPIKey(),
    hasClaudeCodeCLI: isClaudeCodeAvailable()
  };
}

/**
 * Get usage limit status (backward compatibility)
 */
function getUsageLimitStatus() {
  return {
    limitReached: claudeCodeLimitReached,
    timestamp: limitReachedTimestamp
  };
}

/**
 * Reset usage limits (for testing or manual reset)
 */
function resetUsageLimit() {
  claudeCodeLimitReached = false;
  limitReachedTimestamp = null;
  console.log('[AI] Usage limit flag reset');
}

/**
 * Reset API cost tracking
 */
function resetCostTracking() {
  apiCostTotal = 0;
  apiRequestCount = 0;
  console.log('[AI] Cost tracking reset');
}

module.exports = {
  claudeCodeAnalyze,
  isClaudeCodeAvailable,
  hasAPIKey,
  getUsageStatus,
  getUsageLimitStatus, // Backward compatibility
  resetUsageLimit,
  resetCostTracking,
  isUsageLimitError // Export for testing
};
