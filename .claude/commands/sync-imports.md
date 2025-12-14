# /sync-imports - Import Path Synchronizer

## Purpose

Automatically detect and fix broken import paths in JavaScript files after reorganization or file moves. Ensures all imports reference correct locations.

## Usage

```bash
/sync-imports                          # Check all imports
/sync-imports scraper/src/             # Check specific directory
/sync-imports --verify                 # Just validate, no changes
/sync-imports --all --execute          # Fix all broken imports
/sync-imports --verbose                # Detailed output
```

## Implementation

This command:

1. **Scans JavaScript Files**:
   - Finds all import/require statements
   - Identifies imported files
   - Checks if imports reference existing files

2. **Detects Broken Imports**:
   - Tests if imported files exist
   - Checks for typos in paths
   - Identifies circular references

3. **Updates Import Paths**:
   - Changes old paths to new paths
   - Maintains import style (ES6 or CommonJS)
   - Preserves destructuring syntax

4. **Validates Results**:
   - Verifies syntax is still valid
   - Checks all imports now work
   - Reports success/failure

## Import Patterns Supported

```javascript
// ES6 imports
import { skill } from '../skills/errorDiagnostician.js';
import * as utils from '../utils/index.js';
import config from '../config/ai_config.js';

// CommonJS requires
const { analyzeError } = require('../skills/errorDiagnostician.js');
const config = require('../config/ai_config.js');
```

## Output Example

```
Import Path Synchronization Report
===================================

🔍 Scanning JavaScript Files
  Found: 45 files
  Imports: 127 total
  Potentially broken: 0

✅ All Imports Valid
  No broken imports detected
  All references are correct

Result: PASS - No changes needed
```

## Error Examples

```
Broken Imports Found (2):

1. scraper/src/states/process_questions.js:12
   Current: const skills = require('../skills');
   Issue: File moved/doesn't exist
   Available: scraper/src/skills/index.js
   Fix: require('../skills/index.js')

2. scraper/src/ai/claudeCodeClient.js:5
   Current: const templates = require('./promptTemplates');
   Issue: Missing file extension
   Available: scraper/src/ai/promptTemplates.js
   Fix: require('./promptTemplates.js')
```

## Important Notes

- **Implementation Code**: Imports in `scraper/src/` typically don't change (code structure is stable)
- **Skills/Agents**: Remain in `scraper/src/skills/` and `scraper/src/agents/` (tightly coupled)
- **Documentation**: Links in `.md` files are handled by `/update-docs`, not `/sync-imports`

## Safety Features

- Dry-run by default (use `--verify` to check, `--execute` to apply)
- Preserves import style and syntax
- Handles both relative and absolute paths
- Validates syntax after changes

## Related Commands

- `/validate-structure` - Check overall organization
- `/organize-codebase` - Move files and auto-update
- `/update-docs` - Fix documentation links

## Integration

Should be run:
- After file reorganization
- After renaming directories
- After moving modules
- As part of CI/CD validation

## See Also

- `.claude/organization-rules.json` - Organization rules
- `/docs/architecture/CODEBASE_GUIDE.md` - Code structure guide
- `scraper/src/` - Implementation code
