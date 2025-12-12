# MKSAP Scraper - Claude Code Integration Guide

## ✅ NO API KEY REQUIRED

This scraper uses **Claude Code's headless mode** - leveraging your existing Claude Code IDE subscription instead of external API calls. This means:

✅ **No API key setup needed**
✅ **No external API costs**
✅ **Uses your Claude Code subscription**
✅ **Automatic usage limit detection**
✅ **Resume from checkpoint when limits reset**

---

## How It Works

```
┌──────────────────────────────────────┐
│   Playwright Scraper (npm start)    │
│                                      │
│   When error/auth analysis needed:   │
│   ↓                                  │
│   execSync("claude -p '...'          │
│            --output-format json")    │
└──────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────┐
│   Claude Code CLI (Headless Mode)   │
│   Uses your IDE session              │
│                                      │
│   - Analyzes screenshots             │
│   - Diagnoses errors                 │
│   - Detects auth challenges          │
│   - Returns structured JSON          │
└──────────────────────────────────────┘
                  ↓
         JSON result back to scraper
```

---

## Features

### 1. AI-Powered Error Diagnosis
When scraping errors occur, the scraper:
1. Captures screenshot
2. Sends to Claude Code CLI for analysis
3. Gets diagnosis with specific fix suggestions
4. Automatically retries if error is transient

### 2. Authentication Assistant
Detects login challenges:
- CAPTCHA detection
- 2FA requirements
- Session expiration
- Suggests manual vs automatic resolution

### 3. Checkpoint & Resume
- Saves progress every 10 questions
- Detects when Claude Code usage limit hit
- Stops gracefully and saves checkpoint
- Resume exactly where you left off when limits reset

---

## Usage Limit Handling

### What Happens When You Hit Your Daily Limit

1. **Detection**: Scraper detects usage limit error from Claude Code CLI
2. **Stop**: Scraper stops immediately (doesn't waste progress)
3. **Checkpoint**: Automatically saves current progress
4. **Notification**: Logs detailed message showing:
   - When limit was hit
   - How many questions were processed
   - Where to resume from

### Example Output When Limit Hit

```
[claudeCodeClient] ⚠️  USAGE LIMIT REACHED at 2025-01-15T14:30:00Z
[WorkerPool] ⚠️⚠️⚠️ CLAUDE CODE USAGE LIMIT REACHED ⚠️⚠️⚠️
[WorkerPool] Scraping stopped to preserve progress
[WorkerPool] Processed: 42 questions
[WorkerPool] Last question: CVMCQ24042
[WorkerPool] Checkpoint saved to: output/Cardiovascular/.checkpoint.json
[WorkerPool]
[WorkerPool] To resume when usage resets:
[WorkerPool]   npm start cv
[WorkerPool]
[WorkerPool] The scraper will automatically resume from the checkpoint.
```

### Resuming After Limit Resets

Simply run the same command:

```bash
npm start cv
```

The scraper will:
1. Detect existing checkpoint
2. Load progress state
3. Skip already-processed questions
4. Continue from where it left off

---

## Running the Scraper

### Basic Usage (Same as Before)

```bash
cd scraper
npm install
npm start cv  # Scrape Cardiovascular system
```

### Scrape All Systems

```bash
npm start all
```

### AI Features Are Automatic

No setup required! If Claude Code CLI is available:
- ✅ AI error diagnosis activates automatically
- ✅ Auth challenge detection works out of the box
- ✅ Checkpoint & resume enabled by default

If Claude Code CLI is unavailable:
- ⚠️  Falls back to basic error handling
- ⚠️  Basic auth logic (cookies only)
- ✅ Checkpoints still work (don't use AI)

---

## Checkpoint Files

### Location

```
scraper/output/{System}/.checkpoint.json
```

### Structure

```json
{
  "systemFolder": "Cardiovascular",
  "systemCode": "cv",
  "currentPage": 3,
  "questionCount": 42,
  "lastQuestionId": "CVMCQ24042",
  "processedQuestions": ["CVMCQ24001", "CVMCQ24002", ...],
  "timestamp": "2025-01-15T14:30:00Z",
  "version": "1.0"
}
```

### Manual Management

```bash
# View checkpoint
cat scraper/output/Cardiovascular/.checkpoint.json

# Delete checkpoint (start fresh)
rm scraper/output/Cardiovascular/.checkpoint.json

# Resume from checkpoint
npm start cv
```

---

## AI Skills Available

### 1. Error Diagnostician

**Triggers:** When extraction fails
**Analysis:**
- Screenshot of error state
- Error message and stack trace
- Suggests specific code fixes
- Determines if retry is safe

**Example Output:**
```json
{
  "diagnosis": "Modal did not open - button click may have failed",
  "likelyRootCause": "modal_not_opened",
  "suggestedFix": "Try clicking button with force: true option",
  "shouldRetry": true,
  "suggestedRetryDelay": 2000
}
```

### 2. Authentication Assistant

**Triggers:** Login failures, session checks (every 50 questions)
**Analysis:**
- Screenshot of login page
- Detects CAPTCHA, 2FA, session expiry
- Suggests manual vs automatic actions

**Example Output:**
```json
{
  "diagnosis": "CAPTCHA challenge present",
  "authState": "captcha_required",
  "detectedChallenges": ["captcha"],
  "suggestedAction": "manual_login_required",
  "canAutoResolve": false,
  "instructions": "Complete CAPTCHA manually and re-run scraper"
}
```

---

## Configuration

### Enable/Disable AI Features

AI features are controlled in code. Currently **always enabled** if Claude Code CLI is available.

To disable AI features, you can modify:

```javascript
// In src/ai/claudeCodeClient.js
function isClaudeCodeAvailable() {
  return false; // Force disable
}
```

### Checkpoint Frequency

Change how often checkpoints are saved:

```javascript
// In src/agents/progressCheckpointAgent.js
this.checkpointFrequency = 10; // Every 10 questions (default)
// Change to: 5, 20, 50, etc.
```

---

## Troubleshooting

### "Claude Code CLI not available"

**Issue:** Scraper can't find `claude` command

**Fix:**
```bash
# Check if Claude Code CLI is installed
which claude

# If not found, install Claude Code CLI
# (Follow Claude Code installation instructions)
```

**Workaround:** Scraper will still work with basic error handling (no AI features)

### Usage Limit Reached But Scraper Doesn't Stop

**Issue:** Scraper continues after limit hit

**Check:**
1. Are you seeing `USAGE_LIMIT_REACHED` errors in logs?
2. Is checkpoint being saved?

**Debug:**
```bash
# Check checkpoint exists
ls -la scraper/output/*/checkpoint.json

# View last checkpoint
cat scraper/output/Cardiovascular/.checkpoint.json
```

### Resume Doesn't Work

**Issue:** Scraper starts from beginning instead of checkpoint

**Check:**
1. Checkpoint file exists: `output/{System}/.checkpoint.json`
2. Checkpoint file is valid JSON
3. System code matches (e.g., `npm start cv` for Cardiovascular)

**Fix:**
```bash
# Verify checkpoint
cat scraper/output/Cardiovascular/.checkpoint.json | jq .

# If invalid, delete and restart
rm scraper/output/Cardiovascular/.checkpoint.json
```

### Temporary Screenshot Files Pile Up

**Issue:** `.temp/` directory fills with screenshots

**Cleanup:**
```bash
# Manual cleanup
rm -rf scraper/.temp/*.png

# Automatic cleanup happens on scraper exit
# But can be manually triggered in code:
const { cleanupAllTempFiles } = require('./src/ai/tempFileManager');
await cleanupAllTempFiles();
```

---

## Performance Impact

### With AI Features Enabled

- **Error diagnosis**: +2-5s per error (only when errors occur)
- **Auth analysis**: +2-5s per login check (minimal, done once per session)
- **Checkpoint save**: <0.1s every 10 questions (negligible)

**Estimated overhead:** 5-10% slower overall (acceptable for resilience gains)

### Without AI Features (Fallback)

- **No overhead** - runs at normal speed
- Basic error handling
- Checkpoints still work

---

## Cost Analysis

### Claude Code Subscription

**Included in your Claude Code subscription:**
- AI error diagnosis
- Authentication analysis
- Vision API for screenshots

**Not included (but handled):**
- External API calls (none used)
- Anthropic API key (not needed)

### Usage Limit Strategy

1. **Scrape during off-peak hours** when you're not heavily using Claude Code
2. **Batch scraping**: Run full scrapes overnight
3. **Monitor usage**: Check Claude Code usage dashboard
4. **Resume next day**: Checkpoints ensure no progress lost

---

## Example Session

### First Run (Hits Limit After 42 Questions)

```bash
$ npm start cv

[WorkerPool] Starting scrape for Cardiovascular (cv)
[ProgressCheckpointAgent] No checkpoint found. Starting fresh.
[SystemScraper] Processing page 1...
[SystemScraper] Extracted CVMCQ24001
[SystemScraper] Extracted CVMCQ24002
...
[SystemScraper] Extracted CVMCQ24042
[ProgressCheckpointAgent] Checkpoint saved: 42 questions

[errorDiagnostician] AI analysis for error...
[claudeCodeClient] ⚠️  USAGE LIMIT REACHED at 2025-01-15T14:30:00Z

[WorkerPool] ⚠️⚠️⚠️ CLAUDE CODE USAGE LIMIT REACHED ⚠️⚠️⚠️
[WorkerPool] Checkpoint saved to: output/Cardiovascular/.checkpoint.json
[WorkerPool] Resume command: npm start cv
```

### Resume Next Day (After Limit Resets)

```bash
$ npm start cv

[WorkerPool] Starting scrape for Cardiovascular (cv)
[ProgressCheckpointAgent] ✅ Checkpoint found!
[ProgressCheckpointAgent] Resuming from: CVMCQ24042 (42 questions processed)
[SystemScraper] Skipping already processed questions...
[SystemScraper] Processing page 4...
[SystemScraper] Extracted CVMCQ24043
...
[WorkerPool] ✅ Scrape completed for Cardiovascular
[ProgressCheckpointAgent] Checkpoint deleted (successful completion)
```

---

## Summary

✅ **No API key required** - Uses Claude Code IDE subscription
✅ **Automatic usage limit detection** - Stops when limit hit
✅ **Checkpoint & resume** - Never lose progress
✅ **AI-powered error diagnosis** - Smart retry logic
✅ **Authentication assistance** - Detects CAPTCHA, 2FA, session issues
✅ **Graceful fallback** - Works without AI if unavailable

**Next steps:** Run `npm start cv` and watch the magic happen! 🚀
