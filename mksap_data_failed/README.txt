MKSAP Data Failure Logs and Archives

This directory contains:

1. ACTIVE LOGS (current session):
   - (generated during extraction runs)

2. ARCHIVED LOGS (from previous extraction attempts):
   - missing_ids.txt.archive - Questions identified as missing in prior extraction
   - remaining_gaps.txt.archive - Gap analysis from prior extraction attempt
   - remaining_ids.txt.archive - List of remaining question IDs from prior attempt

3. VALIDATION REPORTS:
   - validation_report.txt - Current validation report of extracted data

NOTES:
- All .archive files are from earlier extraction attempts and contain historical data
- Fresh failure logs are generated when extraction is run with --validate flag
- Archived data is kept for reference but should not be used for active work
- Current valid questions: 1,802 (1,539 from 2024 + 289 from 2025)

Last updated: December 25, 2025
