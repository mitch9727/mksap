/**
 * AI Configuration for MKSAP Scraper
 *
 * Configures AI skills and agents for enhanced scraping capabilities.
 * Uses Claude Code CLI (headless mode) by default - NO API KEY REQUIRED.
 *
 * Optional: Add ANTHROPIC_API_KEY to .env for fallback when Claude Code limit hit.
 */

module.exports = {
  // Agent configurations
  agents: {
    progressCheckpointAgent: {
      enabled: true,
      checkpointFrequency: 10,  // Save checkpoint every 10 questions
      checkpointDir: './output',
      autoResume: true
    },

    extractionRecoveryAgent: {
      enabled: true,
      requiredFieldsStrict: ['ID', 'Answer and Critique']
    },

    realTimeMonitorAgent: {
      enabled: true,
      metricsInterval: 30000  // 30 seconds
    }
  },

  // Skill configurations
  skills: {
    errorDiagnostician: {
      enabled: true,
      autoRetry: true,
      maxRetries: 3
    },

    authenticationAssistant: {
      enabled: true,
      detectChallenges: ['captcha', '2fa', 'session_expired']
    },

    dataQualityValidator: {
      enabled: true,
      strictMode: false,  // Don't throw on validation errors
      logIssues: true
    },

    intelligentExtractor: {
      enabled: true,
      confidenceThreshold: 0.8,
      fallbackOnly: true  // Only use when selectors fail
    },

    selectorValidator: {
      enabled: true,
      confidenceThreshold: 0.7,
      cacheResults: true
    },

    tableVisionConverter: {
      enabled: true,
      confidenceThreshold: 0.85,
      maxConcurrent: 2
    }
  },

  // Cost control (for API key fallback mode)
  costControl: {
    maxCostPerQuestion: 0.01,  // $0.01 per question max
    alertOnHighCost: true
  },

  // Rate limiting (for API key fallback mode)
  rateLimiting: {
    requestsPerMinute: 50,
    burstSize: 10
  }
};
