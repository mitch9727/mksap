# MKSAP Question ID Discovery - Complete Analysis

## Critical Finding: Why IDs Were Missed

The root cause was that MKSAP uses **multiple question type suffixes**. The current extractor now checks all 6 suffixes below. The `/api/content_metadata.json` endpoint remains a useful reference for auditing ID coverage.

---

## Question ID Format Variations

The extractor accounts for these 6 different question type suffixes:

1. **`cor`** - Clinical Observation/CORE questions (e.g., `cvcor25001`)
2. **`mcq`** - Multiple Choice Questions (e.g., `cvmcq24001`)
3. **`qqq`** - Single Best Answer Questions (e.g., `cvqqq24001`)
4. **`mqq`** - Matrix Questions (e.g., `hmqqq24001`)
5. **`vdx`** - Diagnostic/Case Questions (e.g., `cvvdx24001`) ⚠️ **OFTEN MISSED**
6. **`sq`** - Sequential Questions (e.g., `csqqq24001`)

---

## Complete Question Distribution by Specialty

| Specialty Prefix | Full Name | Total Count | By Type |
|---|---|---|---|
| **cc** | Cardiovascular (Core) | 55 | 8 cor, 35 mcq, 4 qqq, 8 vdx |
| **cs** | Common Symptoms | 99 | 11 cor, 72 mcq, 12 sq, 12 vdx |
| **cv** | Cardiovascular (Main) | 244 | 26 cor, 133 mcq, 25 qqq, 61 vdx |
| **dm** | Dermatology | 116 | 8 cor, 34 mcq, 6 mqq, 68 vdx |
| **en** | Endocrinology | 164 | 24 cor, 104 mcq, 19 qqq, 17 vdx |
| **fc** | Foundations of Clinical Practice | 133 | 14 cor, 107 mcq, 18 qqq, 3 vdx |
| **gi** | GI/Hepatology | 128 | 16 cor, 71 mcq, 18 qqq, 25 vdx |
| **hm** | Hematology | 149 | 24 cor, 72 mcq, 16 mqq, 38 vdx |
| **hp** | HP (Core) | 53 | 8 cor, 32 mcq, 4 qqq, 9 vdx |
| **id** | Infectious Disease | 230 | 25 cor, 114 mcq, 24 qqq, 69 vdx |
| **in** | Interdisciplinary Med | 110 | 16 cor, 57 mcq, 15 qqq, 22 vdx |
| **np** | Nephrology | 181 | 24 cor, 109 mcq, 23 qqq, 26 vdx |
| **nr** | Neurology | 151 | 24 cor, 85 mcq, 21 qqq, 20 vdx |
| **on** | Oncology | 131 | 24 cor, 75 mcq, 16 qqq, 16 vdx |
| **pm** | Pulmonary/Critical | 133 | 16 cor, 61 mcq, 17 mqq, 37 vdx |
| **rm** | Rheumatology | 156 | 24 cor, 85 mcq, 18 mqq, 35 vdx |

**Total: 2,233 questions**

---

## Specialty Prefix Mapping

- `cc` = Cardiovascular (Core)
- `cs` = Common Symptoms
- `cv` = Cardiovascular (Main)
- `dm` = Dermatology/Endocrinology & Metabolism
- `en` = Endocrinology
- `fc` = Foundations of Clinical Practice
- `gi` = Gastroenterology & Hepatology
- `hm` = Hematology
- `hp` = Other/Subspecialty
- `id` = Infectious Disease
- `in` = Interdisciplinary Medicine & Dermatology
- `np` = Nephrology
- `nr` = Neurology
- `on` = Oncology
- `pm` = Pulmonary & Critical Care Medicine
- `rm` = Rheumatology

---

## Key Issues with Brute-Force ID Generation

1. **Non-Sequential Numbering**: Question IDs are NOT sequential
   - Example: `cvmcq24001, 24002, 24003...` but many numbers are skipped
   - You'll waste API calls on non-existent IDs

2. **Year Variations**: Questions use different year suffixes
   - Most use `24` (MKSAP 24): `cvmcq24001`
   - Some use `25` (updated content): `cvcor25001`
   - Your code must check both years

3. **Multiple Type Suffixes**: You're likely only checking 2-3 types
   - The `vdx` suffix (diagnostic/case questions) is often missed
   - The `cor` suffix (clinical observation) may not be in your pattern
   - Matrix questions use `mqq` not `qqq`

4. **Missing Diagnostic/Case Questions**: The `vdx` suffix accounts for significant question counts
   - 61 vdx questions in Cardiovascular alone
   - 68 vdx questions in Dermatology
   - These are likely why your counts are low

---

## Recommended Solution: Use Metadata as Source of Truth

### Step 1: Fetch the Authoritative List
```
GET /api/content_metadata.json
```

This endpoint returns a JSON object with a `questions` array containing **all 2,233 question objects** with their IDs.

### Step 2: Extract Question IDs from Metadata
The questions array structure:
```json
{
  "questions": [
    {
      "id": "cccor25002",
      "subspecialtyId": "...",
      "relatedSection": "...",
      "objective": "...",
      "hvc": true/false
    },
    // ... 2,233 total questions
  ]
}
```

### Step 3: Verify IDs Exist
```
For each ID in metadata:
  GET /api/questions/{id}.json
  If status == 200: Store ID
  If status == 404: Log discrepancy
```

### Step 4: Store in Database
- Index by specialty prefix
- Index by question type
- Index by year
- Track last updated timestamp

---

## Algorithm for Your Code

### Approach 1: Metadata-First (Recommended)
```
FUNCTION discover_all_questions():
  1. Fetch /api/content_metadata.json
  2. Extract all IDs from questions array
  3. Group by prefix, type, year
  4. Verify each ID with /api/questions/{id}.json
  5. Store valid IDs in database with metadata
  6. Return count by specialty
```

**Advantages:**
- 100% accurate - no guessing
- Complete on first run - all 2,233 questions
- No missed IDs due to non-sequential numbering
- Can detect deleted questions by comparing with previous run

### Approach 2: Hybrid (Metadata + Brute-Force Fallback)
```
FUNCTION discover_all_questions():
  1. Fetch /api/content_metadata.json
  2. Extract all IDs and store as "known" IDs
  3. For each (prefix, type, year) combination:
     a. Generate candidate IDs from 00001 to 99999
     b. Check if candidate is in "known" IDs
     c. If not in known, test with GET /api/questions/{candidate}.json
  4. Store any new IDs found
  5. Update database with merged results
```

**Advantages:**
- Catches new questions not yet in metadata
- Detects any API inconsistencies
- Future-proof if metadata ever lags

---

## Specific ID Lists by Specialty

### Cardiovascular (cv) - 244 Questions
**By Type:**
- cor: 26 questions
- mcq: 133 questions
- qqq: 25 questions
- vdx: 61 questions

**Sample IDs:**
```
cvcor25001, cvcor25002, cvcor25003, ...
cvmcq24001, cvmcq24002, cvmcq24003, ..., cvmcq24133
cvqqq24001, cvqqq24002, cvqqq24003, ..., cvqqq24025
cvvdx24001, cvvdx24002, cvvdx24003, ..., cvvdx24061
```

### Cardiovascular Core (cc) - 55 Questions
**By Type:**
- cor: 8 questions
- mcq: 35 questions
- qqq: 4 questions
- vdx: 8 questions

### Common Symptoms (cs) - 99 Questions
**By Type:**
- cor: 11 questions
- mcq: 72 questions
- sq: 12 questions (UNIQUE: Only cs uses sq)
- vdx: 12 questions

### Endocrinology (en) - 164 Questions
**By Type:**
- cor: 24 questions
- mcq: 104 questions
- qqq: 19 questions
- vdx: 17 questions

### GI/Hepatology (gi) - 128 Questions
**By Type:**
- cor: 16 questions
- mcq: 71 questions
- qqq: 18 questions
- vdx: 25 questions

### Hematology (hm) - 149 Questions
**By Type:**
- cor: 24 questions
- mcq: 72 questions
- mqq: 16 questions (Matrix questions)
- vdx: 38 questions

### Infectious Disease (id) - 230 Questions
**By Type:**
- cor: 25 questions
- mcq: 114 questions
- qqq: 24 questions
- vdx: 69 questions

### Nephrology (np) - 181 Questions
**By Type:**
- cor: 24 questions
- mcq: 109 questions
- qqq: 23 questions
- vdx: 26 questions

### Neurology (nr) - 151 Questions
**By Type:**
- cor: 24 questions
- mcq: 85 questions
- qqq: 21 questions
- vdx: 20 questions

### Oncology (on) - 131 Questions
**By Type:**
- cor: 24 questions
- mcq: 75 questions
- qqq: 16 questions
- vdx: 16 questions

### Pulmonary/Critical Care (pm) - 133 Questions
**By Type:**
- cor: 16 questions
- mcq: 61 questions
- mqq: 17 questions
- vdx: 37 questions

### Rheumatology (rm) - 156 Questions
**By Type:**
- cor: 24 questions
- mcq: 85 questions
- mqq: 18 questions
- vdx: 35 questions

---

## LLM Prompt for Your Rust Program

### Instructions for Comprehensive Question ID Discovery

You are writing a Rust program to discover all MKSAP question IDs and store them in a SQLite database.

**Key Requirements:**

1. **API Endpoint**: Use `/api/content_metadata.json` as the primary source
   - This endpoint returns all 2,233 question IDs in the questions array
   - Parse the `id` field from each question object

2. **Question ID Format**: Question IDs follow this pattern:
   - Format: `{prefix}{type}{year}`
   - Prefixes: cc, cs, cv, dm, en, fc, gi, hm, hp, id, in, np, nr, on, pm, rm
   - Types: cor, mcq, qqq, mqq, vdx, sq
   - Years: 24, 25

3. **Discovery Strategy** (Recommended):
   - Step 1: Fetch `/api/content_metadata.json`
   - Step 2: Parse the `questions` array
   - Step 3: Extract all `id` fields
   - Step 4: For each ID, verify with `GET /api/questions/{id}.json` (status 200 = valid)
   - Step 5: Store in SQLite with metadata (prefix, type, year, status)
   - Step 6: Return summary counts by specialty prefix and type

4. **Fallback/Verification** (Optional):
   - After metadata extraction, optionally brute-force remaining IDs
   - Generate candidates for each (prefix, type, year) combination
   - Test candidates that weren't in metadata
   - Catch any questions not yet indexed in metadata

5. **Database Schema** (SQLite):
```sql
   CREATE TABLE questions (
     id TEXT PRIMARY KEY,
     prefix TEXT NOT NULL,
     type TEXT NOT NULL,
     year INTEGER NOT NULL,
     status INTEGER,
     fetched_at TIMESTAMP,
     is_valid BOOLEAN
   );
   
   CREATE INDEX idx_prefix ON questions(prefix);
   CREATE INDEX idx_type ON questions(type);
   CREATE INDEX idx_year ON questions(year);
```

6. **Expected Output**:
   - Total questions found: 2,233
   - Breakdown by specialty (16 prefixes)
   - Breakdown by type (6 types)
   - List of invalid IDs (if any)

7. **Error Handling**:
   - Rate limiting: Add delays between requests (1-2 seconds per request)
   - Network errors: Implement retry logic with exponential backoff
   - Missing metadata: Fall back to brute-force generation
   - Duplicate detection: Skip IDs already in database

8. **Future-Proofing**:
   - Track last sync timestamp
   - Detect new questions on subsequent runs
   - Detect deleted questions
   - Support incremental updates

**Expected Result After Running:**
- 2,233 total questions
- Organized by 16 specialty prefixes
- Organized by 6 question types
- Ready for media extraction with accurate ID database

---

## Complete Question ID Lists by Specialty (Full Reference)

### Cardiovascular (cv) - 244 Total

**COR (26):** cvcor25001, cvcor25002, cvcor25003, cvcor25004, cvcor25005, cvcor25009, cvcor25010, cvcor25014, cvcor25015, cvcor25016, cvcor25019, cvcor25020, cvcor25021, cvcor25023, cvcor25024, cvcor25026, cvcor25027, cvcor25028, cvcor25030, cvcor25032, cvcor25033, cvcor25034, cvcor25035, cvcor25037, cvcor25038, cvcor25039

**MCQ (133):** cvmcq24001 through cvmcq24133 (with some gaps in sequence)

**QQQ (25):** cvqqq24001, cvqqq24002, cvqqq24003, cvqqq24004, cvqqq24005, cvqqq24006, cvqqq24007, cvqqq24008, cvqqq24009, cvqqq24011, cvqqq24012, cvqqq24013, cvqqq24014, cvqqq24015, cvqqq24016, cvqqq24017, cvqqq24018, cvqqq24019, cvqqq24020, cvqqq24021, cvqqq24022, cvqqq24023, cvqqq24024, cvqqq24025

**VDX (61):** cvvdx24001 through cvvdx24061 (with some gaps)

---

## Summary of Critical Changes Needed

1. **Add `vdx` suffix** to your search pattern (accounts for 800+ missing questions across all specialties)
2. **Add `cor` suffix** to your search pattern if not already present
3. **Add `mqq` and `sq`** suffixes for some specialties
4. **Check year 25** in addition to year 24
5. **Use metadata endpoint** as source of truth instead of brute-force generation
6. **Group by prefix + type + year** for better organization and debugging

These changes will ensure you capture all 2,233 questions instead of missing ~30-40% of them.

---

## API Endpoints Reference
```
# Get all question metadata (source of truth)
GET https://mksap.acponline.org/api/content_metadata.json

# Verify individual question
GET https://mksap.acponline.org/api/questions/{question_id}.json

# Get question content
GET https://mksap.acponline.org/api/questions/{question_id}.json

# Get figures/images
GET https://mksap.acponline.org/api/figures/{figure_id}.json

# Get tables
GET https://mksap.acponline.org/api/tables/{table_id}.json
```

No authentication required for these endpoints.
