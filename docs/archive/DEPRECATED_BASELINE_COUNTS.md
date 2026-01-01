# Deprecated Baseline Counts

This file archives historical baseline question counts from the initial MKSAP 2024
release. These values previously lived in the extractor configuration module as
`baseline_2024_count` and were used as a fallback when discovery metadata was
missing.

Why deprecated:
- Discovery metadata from API HEAD requests is the source of truth.
- Baselines included estimates for split systems and drifted over time.
- Validation now requires discovery metadata instead of silently falling back.

Archived baselines (historical, informational only):

| System code | System | Baseline 2024 |
|-------------|--------|---------------|
| cv | Cardiovascular Medicine | 216 |
| en | Endocrinology and Metabolism | 136 |
| fc | Foundations of Clinical Practice | 0 |
| cs | Common Symptoms | 98 |
| gi | Gastroenterology | 77 |
| hp | Hepatology | 77 |
| hm | Hematology | 125 |
| id | Infectious Disease | 205 |
| in | Interdisciplinary Medicine | 100 |
| dm | Dermatology | 99 |
| np | Nephrology | 155 |
| nr | Neurology | 118 |
| on | Oncology | 103 |
| pm | Pulmonary Medicine | 131 |
| cc | Critical Care Medicine | 55 |
| rm | Rheumatology | 131 |
