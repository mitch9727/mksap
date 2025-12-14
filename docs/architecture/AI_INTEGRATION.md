# AI Integration Architecture

## Overview

The MKSAP scraper features a **hybrid AI-powered system** that leverages both Claude Code CLI and the Anthropic API for intelligent error diagnosis, authentication assistance, and progress management. This architecture provides resilience, cost-efficiency, and graceful degradation.

**Key Principle**: Free by default (Claude Code CLI), optional fallback to API (Anthropic), always works with basic fallback.

---

## Architecture Tiers

### Tier 1: Claude Code CLI (Primary - Free)

- **Entry Point**: `execSync("claude -p '...'")` from [scraper/src/ai/claudeCodeClient.js](../../scraper/src/ai/claudeCodeClient.js)
- **Cost**: $0 (uses your IDE subscription)
- **Features**: All AI capabilities (vision, analysis, suggestions)
- **Limitation**: Daily usage limit (varies by subscription)
- **Availability**: Requires Claude Code CLI installed

### Tier 2: Anthropic API (Fallback - Optional)

- **Entry Point**: `@anthropic-ai/sdk` from [scraper/config/ai_config.js](../../scraper/config/ai_config.js)
- **Cost**: ~$0.01-0.02 per error diagnosis
- **Features**: Same analysis capabilities
- **Requirement**: API key in `.env` file
- **Activation**: Automatic when Tier 1 unavailable/limit reached

### Tier 3: Basic Fallback (Always Available)

- **Entry Point**: Traditional try/catch logic in state handlers
- **Cost**: $0
- **Features**: Basic error handling, no AI analysis
- **Availability**: Always works
- **Graceful**: Allows scraping to continue without AI

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Scraper Core                             │
│  SystemScraper → WorkerPool → State Handlers                │
│                  (login, process_questions, etc.)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
   ┌─────────┐  ┌──────────┐  ┌──────────┐
   │ Error   │  │  Auth    │  │Checkpoint│
   │Diagnosis│  │Assistant │  │  Agent   │
   └────┬────┘  └────┬─────┘  └────┬─────┘
        │             │             │
        └─────────────┼─────────────┘
                      ↓
        ┌─────────────────────────────┐
        │  claudeCodeClient.js        │
        │  Hybrid AI Dispatcher       │
        └────────────┬────────────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   ┌─────────┐ ┌──────────┐ ┌──────────┐
   │Claude  │ │Anthropic │ │  Basic   │
   │Code CLI│ │   API    │ │ Fallback │
   └─────────┘ └──────────┘ └──────────┘
```

---

## Core Components

### 1. AI Client ([scraper/src/ai/claudeCodeClient.js](../../scraper/src/ai/claudeCodeClient.js))

**Responsibilities:**
- Detect Claude Code CLI availability
- Route requests to appropriate tier (CLI → API → Fallback)
- Handle tier-specific error cases
- Detect usage limit errors
- Track API costs

**Key Functions:**

```javascript
async claudeCodeAnalyze(options) {
  // Route through tiers based on availability
  // options: { screenshot, context, analysis_type }
  // Returns: AI analysis or basic fallback result
}

isClaudeCodeAvailable() {
  // Check if 'claude' command is in PATH
}

isUsageLimitReached(error) {
  // Detect "usage limit reached" error patterns
}
```

### 2. Error Diagnostician ([scraper/src/skills/errorDiagnostician.js](../../scraper/src/skills/errorDiagnostician.js))

**Triggered When:** Any error in PROCESS_QUESTIONS state

**Capabilities:**
- Analyzes error + screenshot
- Identifies root cause
- Suggests specific fix
- Determines if retry is appropriate
- Detects transient vs permanent errors

**Example Analysis:**
```
Error: Modal did not appear
Screenshot: [analyzed by Claude]
Diagnosis: "Button click failed - element not visible"
Fix: "Wait 2s for animation, then retry click with force:true"
Retry: true (transient error)
```

### 3. Authentication Assistant ([scraper/src/skills/authenticationAssistant.js](../../scraper/src/skills/authenticationAssistant.js))

**Triggered When:** Login fails, session expires, or CAPTCHA detected

**Capabilities:**
- Detects CAPTCHA/2FA challenges
- Identifies session expiration
- Diagnoses authentication state
- Suggests manual vs automatic resolution

**Example Analysis:**
```
Issue: Login failed
Screenshot: [analyzed by Claude]
Detection: "CAPTCHA challenge detected"
State: "Browser detected suspicious activity"
Action: "manual_login_required"
Instructions: "Complete CAPTCHA, press Enter to continue"
```

### 4. Checkpoint Agent ([scraper/src/agents/progressCheckpointAgent.js](../../scraper/src/agents/progressCheckpointAgent.js))

**Triggered:** Every 10 questions + on usage limit + on graceful shutdown

**Capabilities:**
- Saves progress state
- Detects checkpoint on restart
- Resumes from last checkpoint
- Cleans up on completion

**Checkpoint Structure:**
```json
{
  "systemFolder": "Cardiovascular",
  "systemCode": "cv",
  "currentPage": 3,
  "lastQuestionId": "CVMCQ24042",
  "processedQuestions": ["CVMCQ24001", "..."],
  "timestamp": "2025-01-15T14:30:00Z",
  "version": "1.0"
}
```

### 5. Prompt Templates ([scraper/src/ai/promptTemplates.js](../../scraper/src/ai/promptTemplates.js))

**Purpose:** Standardized, optimized prompts for consistent AI analysis

**Templates:**
- Error diagnosis prompt
- Authentication analysis prompt
- Content extraction prompts
- General analysis template

**Benefits:**
- Consistent output format
- Optimized for accuracy
- Reduces token usage
- Easy to update

### 6. Temp File Manager ([scraper/src/ai/tempFileManager.js](../../scraper/src/ai/tempFileManager.js))

**Responsibilities:**
- Creates temp directory on startup
- Saves screenshots for AI analysis
- Cleans up temp files on exit
- Handles file I/O errors

---

## Integration Points

### WorkerPool Integration

**Files Modified:** [scraper/src/WorkerPool.js](../../scraper/src/WorkerPool.js)

**Changes:**
- USAGE_LIMIT_REACHED error handling
- Emergency checkpoint on limit
- AI stats reporting at completion
- Temp file cleanup

**Example:**
```javascript
} catch (error) {
  if (error.message === 'USAGE_LIMIT_REACHED') {
    await checkpointAgent.emergencySave();
    // Clear exit with resume instructions
  }
}
```

### Login State Integration

**Files Modified:** [scraper/src/states/login.js](../../scraper/src/states/login.js)

**Changes:**
- Call authenticationAssistant on failure
- Detect CAPTCHA/2FA
- Suggest manual vs automatic resolution

**Example:**
```javascript
try {
  await page.click('login-button');
} catch (error) {
  const analysis = await authenticationAssistant.analyze({
    screenshot,
    pageUrl: page.url()
  });
  // Handle based on analysis
}
```

### Question Processing Integration

**Files Modified:** [scraper/src/states/process_questions.js](../../scraper/src/states/process_questions.js)

**Changes:**
- Wrap extraction in `smartRetry()`
- Call errorDiagnostician on failure
- Save checkpoint every 10 questions
- Resume from checkpoint on restart

**Example:**
```javascript
await smartRetry(
  async () => {
    // Extract MCQ data
  },
  {
    page: this.page,
    state: 'PROCESS_QUESTIONS',
    maxRetries: 3
  }
);
```

---

## Data Flow Examples

### Successful Question Extraction

```
1. process_questions.js calls smartRetry()
2. Opens MCQ modal → extracts JSON
3. Saves JSON to output/
4. Increments counter
5. Every 10th: saves checkpoint
6. Continue to next question
```

### Failed Question Extraction (with AI)

```
1. process_questions.js calls smartRetry()
2. Modal doesn't open → Error thrown
3. smartRetry() catches error
4. Takes screenshot
5. Calls errorDiagnostician.analyzeError()
6. claudeCodeClient routes to Claude Code CLI
7. Claude analyzes screenshot + error
8. Returns: "Modal selector changed, try new selector: ..."
9. smartRetry() applies suggestion
10. Retries extraction
11. Success → Continue
```

### Usage Limit Reached

```
1. process_questions.js in smartRetry()
2. Calls claudeCodeAnalyze() for error diagnosis
3. Claude Code CLI responds with limit error
4. claudeCodeClient detects: isUsageLimitReached()
5. Throws USAGE_LIMIT_REACHED error
6. smartRetry() doesn't retry (terminal error)
7. process_questions.js catches error
8. Calls checkpointAgent.emergencySave()
9. Saves current progress
10. Rethrows error up stack
11. WorkerPool catches USAGE_LIMIT_REACHED
12. Logs clear message with resume instructions
13. Exits gracefully
14. User runs same command next day
15. checkpointAgent detects checkpoint
16. Skips 42 processed questions
17. Continues from CVMCQ24043
```

---

## Configuration

### Enable/Disable AI Features

**Enable (Default):**
```javascript
// In claudeCodeClient.js
const CLAUDE_CODE_ENABLED = true;  // Auto-uses Claude Code if available
const API_FALLBACK_ENABLED = true;  // Auto-uses API if configured
```

**Disable AI (use basic fallback only):**
```javascript
const CLAUDE_CODE_ENABLED = false;
const API_FALLBACK_ENABLED = false;
```

### Configure API Fallback

**Create `.env` file:**
```bash
cp scraper/.env.example scraper/.env
```

**Add API key:**
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Adjust Checkpoint Frequency

**In progressCheckpointAgent.js:**
```javascript
// Save every N questions
this.checkpointFrequency = 10;  // Default: 10 questions
// Change to: 5 (more frequent), 20 (less frequent), etc.
```

---

## Error Handling

### Error Categories

| Category | Detection | Handling | Retry |
|----------|-----------|----------|-------|
| **Transient** | Network, timeout | Wait + retry | Yes |
| **Selector Changed** | Element not found | Update selector | Yes |
| **Session Expired** | 401/403, captcha | Re-login | Depends |
| **Usage Limit** | API response | Checkpoint + stop | No |
| **Unknown** | Unexpected error | Log + continue | No |

### Error Flow

```
Error Occurs
    ↓
Is it transient? → Yes → Wait + Retry
    ↓ No
Can we diagnose? → Yes → Get AI suggestion → Apply → Retry
    ↓ No
Is it recoverable? → Yes → Checkpoint + Continue
    ↓ No
Emergency Checkpoint → Exit Gracefully
```

---

## Cost Analysis

### Claude Code Subscription (Default)

**Included in subscription:**
- Unlimited AI analysis (within daily limit)
- Vision API for screenshots
- All checkpoint/resume features

**Cost**: $0 (uses existing IDE subscription)

**Typical Usage:**
- Scrape 2,000 questions with ~10% error rate = ~200 AI analyses
- All run against Claude Code (free)
- No API costs

### Anthropic API (Optional - Only if Fallback Triggered)

**Pricing:**
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

**Estimated Costs:**
- Error diagnosis: ~$0.005-0.015 per error
- Auth analysis: ~$0.003-0.010 per analysis
- Full scrape with API fallback: $2-10

**Cost Optimization:**
- Default: Use Claude Code (free)
- Only switch to API if Claude Code limit hit
- Typical: 95%+ of requests use Claude Code
- Actual API cost: $0-2 for full scrape

---

## Monitoring & Logging

### Key Log Messages

```
[AI] ℹ️ Claude Code CLI available
[AI] ℹ️ Using API fallback mode (limit reached)
[AI] ⚠️  Claude Code usage limit reached at 2025-01-15T14:30:00Z
[ProgressCheckpointAgent] ✓ Checkpoint found! Resuming from: CVMCQ24042
[errorDiagnostician] AI analysis: Modal selector changed
[authenticationAssistant] Detected: CAPTCHA challenge
```

### Statistics Reporting

At end of scrape, WorkerPool logs:

```
AI Usage Statistics:
  Mode: claude-code (free)
  OR
  Mode: api-key (fallback)
  Requests: 25
  Cost: $0.2150
```

---

## Future Enhancements

### Planned Features

- **Data Quality Validator**: Post-extraction validation with AI
- **Intelligent Extractor**: Adaptive extraction logic
- **Table Vision Converter**: Image → HTML conversion
- **Real-Time Monitor**: Metrics dashboard
- **Extraction Recovery**: Repair missing/incomplete fields

### Research Areas

- Prompt optimization for specific error types
- Cost reduction through better tier selection
- Pre-emptive error detection (predict failures)
- Batch analysis for efficiency

---

## Troubleshooting

### Claude Code Not Available

**Problem:** `which claude` returns nothing

**Solution:**
1. Install Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
2. Or let scraper fall back to API or basic mode
3. Scraper works in all modes

### Usage Limit Not Triggering

**Problem:** Scraper doesn't stop at limit

**Debug:**
```bash
# Check log for limit error
grep "usage limit" scraper/logs/scraper.log

# Verify checkpoint was saved
ls scraper/output/Cardiovascular/.checkpoint.json
```

### Checkpoint Not Resuming

**Problem:** Scraper starts from beginning

**Verify:**
```bash
# Check checkpoint exists
ls -la scraper/output/Cardiovascular/.checkpoint.json

# Check system code matches
cat scraper/output/Cardiovascular/.checkpoint.json | grep systemCode
npm start cv  # Must match systemCode

# Manually check JSON
cat scraper/output/Cardiovascular/.checkpoint.json | jq .
```

### Temp Files Accumulating

**Problem:** `.temp/` directory grows large

**Cleanup:**
```bash
# Manual cleanup
rm -rf scraper/.temp/*.png

# Automatic cleanup occurs on exit
# Check WorkerPool.cleanup() in logs
```

---

## Related Documentation

- [CLAUDE_CODE_SETUP.md](./CLAUDE_CODE_SETUP.md) - Claude Code CLI integration
- [TECHNICAL_SPEC.md](../scraper/TECHNICAL_SPEC.md) - Scraper architecture
- [AI_FEATURES.md](../scraper/AI_FEATURES.md) - AI features documentation
- [scraper/src/ai/claudeCodeClient.js](../../scraper/src/ai/claudeCodeClient.js) - Main AI client implementation
- [.env.example](../../scraper/.env.example) - Environment configuration template

---

**Last Updated:** December 13, 2025
