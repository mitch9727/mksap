# PHASE 1: Complete Data Extraction - Detailed Implementation Plan

**Phase Goal:** Ensure all 2,198 valid MKSAP questions are extracted with complete context and media (invalidated
questions excluded).

**Current Status:** 2,198 questions extracted (100% of target)

**Expected Duration:** 2-4 weeks (dependent on API rate limiting and extraction speed)

**Success Criteria:**
- All 2,198 questions extracted and validated
- 100% media files downloaded
- Zero critical deserialization errors
- Validation report shows 100% pass rate

---

## Task Breakdown

### Task 1: Finalize Question Count & Discovery Algorithm

**Objective:** Determine exact question count and implement discovery algorithm to find all 2,198 questions.

**Current Situation:**
- PROJECT_STATUS.md claims 1,810 total questions
- Question ID Discovery.md documents 2,198 total questions (accounting for 6 question types)
- Discrepancy: 423 questions (19.6%) are missing from current extraction targets

**Action Items:**

1. Read `docs/Question ID Discovery.md` completely
   - Understand the 6 question type suffixes: cor, mcq, qqq, mqq, vdx, sq
   - Review complete question distribution table (16 specialties × 6 types)
   - Note the metadata-first discovery approach recommended

2. Research API metadata endpoint
   - Document recommends: `/api/content_metadata.json`
   - Test if this endpoint returns authoritative question list
   - If available: Use as source of truth
   - If not: Implement ID pattern discovery algorithm from Question ID Discovery.md

3. Determine exact question count per system
   - Execute discovery against live API
   - Generate final counts: System → Total Questions
   - Compare to current configuration targets
   - Identify which systems are missing question types

4. Document findings
   - Create `docs/PHASE_1_DISCOVERY_RESULTS.md`
   - Include: Authoritative question count per system
   - Note any API inconsistencies discovered
   - Record timestamp of discovery (for reproducibility)

**Deliverable:** Final question count verified and documented. Ready for configuration update.

**Success Check:** Confirm totals match 2,198 using discovery metadata or validation output.

**Risk:** API endpoint may have changed or be unavailable. Fallback: Use pattern-based discovery algorithm from Question
ID Discovery.md.

**Dependencies:** Must complete before moving to Task 2.

---

### Task 2: Update Configuration with Accurate Counts

**Objective:** Update Rust extractor configuration to target all 2,198 questions.

**Current Module:** System configuration

**Action Items:**

1. Open the system configuration list
   - Locate the `ORGAN_SYSTEMS` array (should be 16 system codes)
   - Each system has: `id`, `name`, `url_slug`, `api_code`, `total_questions`

2. Update `total_questions` for each system
   - Use results from Task 1
   - Example: If cv (cardiovascular) should be 240 instead of 216, update the value
   - Document reasoning for any changes in code comments

3. Add support for missing question types if needed
   - Current config may only target `mcq` type
   - If discovery revealed `vdx`, `cor`, `qqq`, `mqq`, `sq` questions, ensure extraction logic targets these
   - Check extraction logic for question type handling
   - Update question ID pattern matching if needed

4. Test configuration ```bash cd extractor cargo build --release # Should compile without errors ```

5. Verify changes
   - Generate list of all target question IDs
   - Compare total against 2,198
   - Should match exactly

**Deliverable:** System configuration updated with accurate counts. Code compiles successfully.

**Success Check:**
```bash
./target/release/mksap-extractor --list-all | wc -l
# Should output approximately 2,198
```

**Risk:** If question type handling is not in extractor logic, extraction will still miss new types. Check Task 3.

**Dependencies:** Requires Task 1 results.

---

### Task 3: Verify Question Type Extraction Support

**Objective:** Ensure extractor handles all 6 question types (cor, mcq, qqq, mqq, vdx, sq).

**Current Module:** Extraction pipeline

**Action Items:**

1. Review extractor logic for question type handling
   - Search for "question type" or "suffix" patterns in the extraction logic
   - Identify how question IDs are generated/validated
   - Check if it hardcodes "mcq" or supports variable types

2. Test extraction for each question type
   - Pick one test question ID for each type:
     - mcq: cvmcq24001
     - vdx: cvvdx24001 (video diagnosis)
     - cor: cvcor24001 (case of rounds)
     - qqq: cvqqq24001 (quality of questions)
     - mqq: cvmqq24001 (multiple question queue)
     - sq: cvsq24001 (standard question)
   - Manually curl the API for each to verify they exist:
     ```bash
     curl -s https://mksap.acponline.org/api/questions/cvmcq24001.json | jq '.question_id'
     curl -s https://mksap.acponline.org/api/questions/cvvdx24001.json | jq '.question_id'
     # etc.
     ```

3. If extractor doesn't support all types
   - Identify where type filtering happens
   - Update logic to include all 6 types
   - If using hardcoded patterns: Make configurable

4. Document findings
   - Create `docs/rust/QUESTION_TYPES_SUPPORT.md`
   - Note which types are supported
   - Document any API differences between types (if discovered)

**Deliverable:** Verified that extractor can handle all 6 question types. Any code updates made and tested.

**Risk:** Some question types might have different API response format. Document in DESERIALIZATION_ISSUES.md.

**Dependencies:** Requires Task 2 to be started (configuration in place).

---

### Task 4: Complete Question Extraction

**Objective:** Extract all 2,198 questions and store in mksap_data/ directory.

**Estimated Time:** 10-30 hours (depending on rate limiting: 500ms per request × 2,198 = ~30 hours minimum, plus
overhead)

**Action Items:**

1. Prepare extraction environment ```bash cd /path/to/MKSAP

# Ensure session cookie is set export MKSAP_SESSION=<your_valid_session_cookie>

# Optional: Override request delay for faster extraction # Update the request delay setting in extraction configuration
   ```

2. Start extraction
   ```bash
./target/release/mksap-extractor
   ```

3. Monitor progress
   - Watch mksap_data/ directory growth
   - Check checkpoint progress: `ls mksap_data/.checkpoints/`
   - Monitor logs for errors
   - Track time to completion

4. Handle interruptions gracefully
   - If Ctrl+C during extraction: Safe to stop (checkpoints preserve progress)
   - If session expires: Restart with new session cookie
   - If rate limited (HTTP 429): Automatic backoff kicks in (60-second wait)
   - Resume extraction by running command again

5. Periodically validate during extraction
   ```bash
# Count extracted questions find mksap_data -type d -name "*mcq*" -o -name "*vdx*" -o -name "*cor*" | wc -l

# Check for failures ls mksap_data_failed/ | wc -l
   ```

6. Complete extraction
   - Wait for all 2,198 questions to extract
   - Verify zero (or minimal) failures in mksap_data_failed/
   - Record time taken and any issues encountered

**Deliverable:** Complete mksap_data/ directory with all 2,198 questions.

**Success Check:**
```bash
# Should show ~2,198 question directories
find mksap_data -maxdepth 2 -type d ! -name ".*" ! -name "mksap_data" | wc -l
# Should be ~2,198

# Should show minimal or zero failures
ls -1 mksap_data_failed/ 2>/dev/null | wc -l
# Should be < 10 (acceptable failure rate)
```

**Common Issues & Solutions:**

| Issue | Solution |
|-------|----------|
| Slow extraction (hours) | Normal due to rate limiting. Run overnight or in background. |
| Session expires mid-extraction | Restart with fresh session cookie. Checkpoints preserve progress. |
| HTTP 429 (rate limit) | Automatic backoff. Or increase the request delay setting. |
| Connection timeout | Check network. Retry operation. |
| Deserialization error | Document in DESERIALIZATION_ISSUES.md. May need data model update. |

**Dependencies:** Requires Tasks 1-3 to be complete.

---

### Task 5: Monitor Extraction & Handle Issues

**Objective:** Actively monitor extraction process, handle errors, maintain progress.

**Concurrent with Task 4**

**Action Items:**

1. Set up monitoring
   - Terminal window 1: Run extractor (Task 4)
   - Terminal window 2: Monitor progress
   ```bash
watch -n 10 'find mksap_data -maxdepth 2 -type d ! -name ".*" | wc -l && echo "---" && ls mksap_data_failed/ 2>/dev/null
| wc -l && echo "failed"'
   ```

2. Handle session expiration
   - If extractor stops with auth error:
     - Get new session cookie from browser (DevTools → Application → Cookies)
     - `export MKSAP_SESSION=<new_cookie>`
     - Restart extractor (it will resume from checkpoint)

3. Handle rate limiting
   - If HTTP 429 errors appear: Normal, automatic backoff active
   - If persistent 429s: Increase the request delay setting
     - Current: 500ms (conservative)
     - Try: 750ms or 1000ms if needed
     - Recompile and retry failed extraction

4. Document issues
   - Create `docs/PHASE_1_EXTRACTION_LOG.md`
   - Record any errors encountered
   - Note times and solutions applied
   - Update DESERIALIZATION_ISSUES.md if new patterns found

5. Verify checkpoint system
   - Checkpoints stored in `mksap_data/.checkpoints/`
   - Each system has a checkpoint file showing last successful ID
   - If extraction halts, restart command resumes from last checkpoint

**Deliverable:** Extraction monitoring log. Issues documented.

**Risk:** Long extraction time (30+ hours). Plan to run overnight or in background.

---

### Task 6: Validate All Extracted Questions

**Objective:** Verify data quality and completeness of extracted questions.

**Estimated Time:** 30 minutes to 2 hours

**Action Items:**

1. Run built-in validator
   ```bash
./target/release/mksap-extractor validate
   ```
   - This scans all extracted questions
   - Checks JSON structure, required fields, data integrity
   - Generates `mksap_data/validation_report.txt`

2. Review validation report
   ```bash
cat mksap_data/validation_report.txt
   ```
   - Check for errors, warnings, or anomalies
   - Note any fields with missing data
   - Document any systematic issues

3. Validate specific criteria
   ```bash
# All questions should have 'critique' field (needed for Phase 2) for file in mksap_data/*/*.json; do if ! jq -e
'.critique' "$file" > /dev/null 2>&1; then echo "Missing critique: $file" fi done
   ```

4. Check question count matches target
   ```bash
# Count total extracted questions find mksap_data -name "*.json" ! -path "*/.checkpoints/*" | wc -l # Should be exactly
2,198
   ```

5. Sample validation
   - Spot-check 20 random questions from different systems
   - Manually verify JSON structure
   - Ensure key fields present: question_id, critique, options, media_refs

6. Document validation results
   - Create `docs/PHASE_1_VALIDATION_REPORT.md`
   - Include: Pass/fail criteria, any anomalies, remediation steps
   - Note date of validation

**Deliverable:** Validation report confirming data quality. Any issues documented.

**Success Check:**
```bash
# Validation should complete without critical errors
grep -i "error\|critical" mksap_data/validation_report.txt
# Should return minimal or zero results
```

**Common Issues & Remediation:**

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing 'critique' field | API didn't return it | Re-extract that question using retry logic |
| Invalid JSON structure | Deserialization issue | Document in DESERIALIZATION_ISSUES.md, update data models if needed |
| Missing media references | Media extraction didn't run | See Task 7 |
| Count < 2,198 | Extraction incomplete | Verify all systems processed, re-run failed extractions |

**Dependencies:** Requires Task 4 to complete extraction.

---

### Task 7: Verify Media Files

**Objective:** Ensure all referenced media downloaded and properly organized.

**Estimated Time:** 1-3 hours

**Action Items:**

1. Understand current media structure
   - Media should be in: `mksap_data/{system}/{question_id}/figures/`
   - Check existing media:
   ```bash
find mksap_data -path "*/figures/*" -type f | head -20
   ```

2. Verify media references in JSON
   ```bash
# Extract all media refs from a sample question jq '.media' mksap_data/cv/cvmcq24001/cvmcq24001.json
   ```

3. Check media download completion
   ```bash
# Count total media files downloaded find mksap_data -path "*/figures/*" -type f | wc -l

# This should be non-zero and substantial (hundreds of files)
   ```

4. Audit for missing media
   ```bash
# For each question, check if referenced media exists for qdir in mksap_data/*/*/; do qid=$(basename "$qdir") refs=$(jq
'.media? | length' "$qdir/$qid.json" 2>/dev/null || echo 0) files=$(find "$qdir/figures" -type f 2>/dev/null | wc -l) if
[ "$refs" -gt 0 ] && [ "$files" -eq 0 ]; then echo "Missing media in $qid (expected: $refs, found: $files)" fi done
   ```

5. Organize media by type
   - Media should include: Images (JPG, PNG), SVGs, possibly videos
   - Verify file extensions match types

6. Check media file integrity
   ```bash
# Spot-check a few image files for corruption file mksap_data/*/*/figures/*.jpg | head -5 # Should show "JPEG image
data"
   ```

7. Document media audit
   - Create `docs/PHASE_1_MEDIA_AUDIT.md`
   - Include: Total media files, types, any missing or corrupt files
   - Note: Expected media coverage (not all questions have media)

**Deliverable:** Media audit report. All found media organized correctly.

**Success Check:**
```bash
# Should have substantial media files (1000+ typical)
find mksap_data -path "*/figures/*" -type f | wc -l
# Expected: 5,000-15,000 files (varies by question coverage)
```

**Risk:** Some questions may not have media. This is normal and expected.

**Dependencies:** Requires Task 4 extraction completion.

---

### Task 8: Audit for Deserialization Issues

**Objective:** Identify and document any new JSON deserialization patterns not previously seen.

**Estimated Time:** 1-2 hours

**Action Items:**

1. Review existing DESERIALIZATION_ISSUES.md
   - Read `docs/rust/DESERIALIZATION_ISSUES.md`
   - Understand previously documented issues
   - Note fixes already applied

2. Scan for JSON inconsistencies
   ```bash
# Sample 50 random question JSONs for structure analysis for file in $(find mksap_data -name "*.json" ! -path
"*/.checkpoints/*" | shuf | head -50); do echo "=== $(basename $file) ===" jq 'keys' "$file" done
   ```

3. Check for type variations
   ```bash
# Look for fields that sometimes are strings, sometimes objects # Example: options[].text might be string or object

# Sample different questions from different systems jq '.options[0].text | type' mksap_data/cv/*/*.json | sort | uniq -c
jq '.options[0].text | type' mksap_data/en/*/*.json | sort | uniq -c # If you see multiple types (string and object),
that's a deserialization issue
   ```

4. Document any new issues
   - If new patterns found: Create entry in DESERIALIZATION_ISSUES.md
   - Include: Field name, possible values/structures, example questions
   - Note: Workaround or planned fix

5. Validate data models handle variations
   - If issues found, check if flexible deserialization is in use
   - Anyhow/serde should handle most variations
   - Document if manual fix needed

**Deliverable:** Updated DESERIALIZATION_ISSUES.md with any new patterns. Confidence in data structure consistency.

**Success Check:**
```bash
# All sampled JSONs should parse cleanly
jq . mksap_data/*/*.json > /dev/null echo $?  # Should return 0 (success)
```

**Dependencies:** Requires Task 4 extraction and Task 6 validation.

---

### Task 9: Final Phase 1 Completion Report

**Objective:** Verify all Phase 1 goals met. Generate comprehensive report. Prepare for Phase 2.

**Estimated Time:** 2-3 hours

**Action Items:**

1. Verify all tasks 1-8 complete
   - Check: ✅ Question count finalized
   - Check: ✅ Config updated
   - Check: ✅ Extraction complete (2,198 questions)
   - Check: ✅ Validation passed
   - Check: ✅ Media verified
   - Check: ✅ Deserialization audit done

2. Generate statistics
   ```bash
# Total questions extracted find mksap_data -maxdepth 2 -type d ! -name ".*" | wc -l

# Total media files find mksap_data -path "*/figures/*" -type f | wc -l

# Total storage used du -sh mksap_data/

# Breakdown by system for system in mksap_data/*/; do count=$(find "$system" -maxdepth 1 -type d ! -name ".*" | wc -l)
echo "$(basename $system): $count" done
   ```

3. Create final report: `docs/PHASE_1_COMPLETION_REPORT.md`
   - Title: PHASE 1 Complete ✅
   - Date: [today]
   - Summary:
     - Questions extracted: 2,198
     - Media files: [count]
     - Storage: [size]
     - Validation: 100% pass
     - Issues found: [list] or None
   - Per-system breakdown table
   - Key findings and recommendations
   - Next phase readiness: Phase 2 Ready ✅

4. Create Phase 2 input validation checklist
   ```markdown
## Phase 2 Prerequisites - Validation Checklist

   - [ ] All 2,198 questions extracted
   - [ ] All questions have 'critique' field populated
   - [ ] All questions have valid JSON structure
   - [ ] Media verified downloaded
   - [ ] Related content references added
   - [ ] Validation report shows 0 critical errors
   - [ ] mksap_data/ directory backed up
   ```

5. Backup Phase 1 data
   - Create compressed backup: `mksap_data.backup.tar.gz`
   - Store safely (external drive or cloud)
   - Note: This is your source data for all future phases

6. Document lessons learned
   - Create `docs/PHASE_1_LESSONS_LEARNED.md`
   - What went well
   - What was challenging
   - Recommendations for future phases
   - Known limitations discovered

7. Prepare Phase 2 kickoff
   - Review Phase 2 plan: `docs/PHASE_2_PLAN.md` (to be created)
   - Identify any dependencies or blockers
   - Schedule Phase 2 start

**Deliverable:** Phase 1 completion report. Backup created. Phase 2 prerequisites met.

**Success Check:**
```bash
# Phase 1 complete when:
# 1. File count matches target
find mksap_data -name "*.json" ! -path "*/.checkpoints/*" | wc -l
# Returns: 2,198

# 2. All have critique field
find mksap_data -name "*.json" ! -path "*/.checkpoints/*" -exec jq -e '.critique' {} \; 2>/dev/null | wc -l
# Returns: 2,198

# 3. Validation report exists and shows 0 critical errors
cat mksap_data/validation_report.txt | grep -i critical | wc -l
# Returns: 0
```

**Dependencies:** Requires Tasks 1-9 complete.

---

## Phase 1 Success Criteria Summary

**All of the following must be true:**

1. ✅ Question count finalized at 2,198 (all 16 systems, all 6 question types)
2. ✅ All 2,198 questions extracted to mksap_data/{system}/{question_id}/ directories
3. ✅ Each question has complete JSON with: question_id, critique, options, media_refs
4. ✅ All referenced media downloaded and organized in figures/ subdirectories
5. ✅ Validation report shows 100% pass (zero critical errors)
6. ✅ Deserialization issues documented (if any found)
7. ✅ Related content references extracted and added to each question JSON
8. ✅ Phase 1 completion report generated
9. ✅ Data backed up
10. ✅ Phase 2 prerequisites validated

**When all criteria met:** Phase 1 ✅ COMPLETE. Ready for Phase 2: Intelligent Fact Extraction.

---

## Risk Management & Decision Points

### Risk: Extraction Takes Longer Than Expected

**If extraction > 1 week:**
- This is normal due to rate limiting
- Run extraction in background (tmux/screen session)
- Proceed with other tasks in parallel if needed
- No action required unless errors occur

### Risk: Deserialization Errors Discovered

**If errors > 10% of questions:**
- PAUSE extraction
- Investigate error pattern
- Update data models to handle variation
- Recompile and re-run extraction on failed questions

### Risk: Media Not Fully Downloaded

**If media files < 50% of expected:**
- Check if media extraction ran (should happen automatically)
- If not: Run media_extractor binary separately
- Verify media URLs are valid (not broken links)
- Document media coverage in audit

### Risk: Validation Fails

**If validation report shows errors:**
- Review validation_report.txt for error details
- If < 5% of questions fail: Acceptable, document known issues
- If > 5% fail: STOP, investigate root cause before proceeding

### Risk: Session Expires During Extraction

**If Auth fails mid-extraction:**
- Get fresh session cookie from browser
- Set environment variable: `export MKSAP_SESSION=<new_cookie>`
- Restart extractor (resumes from checkpoint, no data loss)
- Normal occurrence, expected to happen every 24 hours

---

## Parallel Work Opportunities

While extraction runs (Task 4), you can work on:
- Task 5: Monitoring
- Task 8: Auditing JSON structure (once some questions extracted)
- Task 9: Completion report preparation (drafts, stats templates)

These can happen in parallel. Extraction is I/O bound (waiting for API), so multiple tasks can run concurrently.

---

## Next Steps

**Once Phase 1 Complete:**

1. Review Phase 1 completion report
2. Ensure all success criteria met
3. Create Phase 2 detailed plan (Intelligent Fact Extraction)
4. Begin Phase 2 task 1: LLM prompt design for fact extraction
5. Start fact extraction batches

---

**Document Last Updated:** December 25, 2025
**Phase Status:** Ready to execute
**Est. Completion:** January 8-20, 2026 (dependent on extraction speed)
