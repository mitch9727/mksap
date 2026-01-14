# Week 1 Baseline Analysis - Critical Findings

## Baseline Testing Results

**Three consecutive runs with current prompts (Codex CLI, temp=0.1):**

| Run | Critique | Key Points | Tables | Total Statements | Cloze Candidates |
|-----|----------|-----------|--------|-------------------|-----------------|
| 1   | 7        | 3         | 10     | 20                | 76              |
| 2   | 7        | 3         | 10     | 20                | 76              |
| 3   | 7        | 3         | 10     | 20                | 73              |

**Consistency Observations:**
- ✅ Statement count PERFECTLY consistent (20 across all 3 runs)
- ⚠️ Cloze candidate count SLIGHTLY variable (73-76 range)
- Statement wording appears identical across runs
- **Preliminary conclusion:** Temperature=0.1 + Codex CLI provides excellent consistency

---

## Critical Ambiguity Issue Discovered ⚠️

**Problem:** Some cloze statements lack sufficient context, making it impossible to guess the intended blanked term.

**Example (from baseline output):**
```
Statement: "Reslizumab adverse effects include anaphylaxis, headache, and helminth infections."
Cloze Candidates: ["Reslizumab"]
```

**Why this is problematic:**
- If "Reslizumab" is blanked: "_____ adverse effects include anaphylaxis, headache, and helminth infections."
- Multiple biologics cause similar side effects → impossible to guess "Reslizumab" specifically
- The statement lacks context about WHAT Reslizumab is or WHERE it's used in asthma treatment

**Recommended fix:**
Add contextual descriptor in statement:
```
"Reslizumab, an IL-5 antagonist biologic, can cause anaphylaxis, headache, and helminth infections."
```

OR add as extra_field:
```
{
  "statement": "Reslizumab adverse effects include anaphylaxis, headache, and helminth infections.",
  "extra_field": "Reslizumab is a monoclonal antibody that targets IL-5 for treatment of severe asthma.",
  "cloze_candidates": ["Reslizumab", "anaphylaxis", "helminth infections"]
}
```

---

## Identified Patterns of Ambiguity

### Type 1: Drug-Only Clozes Without Clinical Context
**Examples:**
- "Omalizumab is a monoclonal antibody that binds free serum IgE"
  - Cloze: "Omalizumab" → blanked version too generic
- "Reslizumab adverse effects include..."
  - Cloze: "Reslizumab" → could be any biologic

**Solution:** Add clinical context (mechanism, indication, or disease) to distinguish from similar drugs

### Type 2: Non-Unique Clinical Features
**Example:**
- "X therapy is indicated for condition Y"
  - If "X" is blanked but multiple therapies fit "condition Y", it's ambiguous

**Solution:** Add distinguishing feature (mechanism, biomarker requirement, side effect profile)

### Type 3: Generic Cloze Candidates Without Medication Context
**Example:**
- "Adverse effects include anaphylaxis, headache, and helminth infections"
  - If blank is in the adverse effects, reader can't know which drug

**Solution:** Ensure medication/agent is mentioned BEFORE or WITH the clinical feature

---

## Recommendations for Prompt Enhancement

### 1. Add Context Clarity Requirement to critique_extraction.md:

```markdown
**CONTEXT CLARITY REQUIREMENT:**
Each statement must provide sufficient context that when ONE cloze candidate is removed,
the reader can still uniquely identify it from the remaining context.

EXAMPLES:

❌ TOO AMBIGUOUS:
- "X adverse effects include anaphylaxis, headache, and helminth infections"
  (Could apply to many biologics - reader can't guess which)

✅ CONTEXT SUFFICIENT:
- "Reslizumab, an IL-5 receptor antagonist used for severe asthma with eosinophilia,
   adverse effects include anaphylaxis, headache, and helminth infections"
  (Now reader can identify the drug from clinical context + mechanism)

✅ ALTERNATIVE WITH EXTRA_FIELD:
- Statement: "IL-5 receptor antagonists adverse effects include anaphylaxis, headache, and helminth infections"
  extra_field: "Reslizumab is an example of an IL-5 receptor antagonist"
  (Provides context for clinical learning without making single statement ambiguous)
```

### 2. Add Medication Name Requirement:

```markdown
**MEDICATION CONTEXT RULE:**
When generating statements about drugs/biologics:
- Always include the generic/class name AND mechanism OR indication
- Example: "Tezepelumab (a TSLP antagonist)" or "Reslizumab (IL-5 inhibitor)"
- This prevents ambiguity when cloze deletes the drug name
```

### 3. Add to Cloze Identifier Prompt:

```markdown
**AMBIGUITY CHECK FOR CLOZE CANDIDATES:**
Before finalizing cloze candidates, verify:
1. If the candidate is a drug/medication name:
   - Is the mechanism or indication mentioned in the statement?
   - If removed, would context still uniquely identify it?
   - If NO → add mechanism/indication to statement OR change candidate

2. If the candidate is a clinical feature (symptom, side effect):
   - Is the relevant drug/agent clearly stated?
   - If removed, would context still uniquely identify it?
   - If NO → expand context in statement OR remove as candidate
```

---

## Impact on Quality Metrics

### Coverage Impact:
- Ambiguous statements may be REMOVED in validation phase
- Adding context may increase statement length slightly
- Better context = higher quality learning (worth the cost)

### Validation Impact:
- Need NEW validation module: `ambiguity_checks.py` (Week 2 task)
- This module will detect context-deficient statements
- Can suggest remediation (add context, use extra_field, etc.)

---

## Next Steps

1. **Enhance critique_extraction.md prompt** with context clarity requirement
2. **Enhance cloze_identification.md prompt** with ambiguity checking guidance
3. **Re-run enhanced tests** (Week 1)
4. **Implement ambiguity_checks.py** (Week 2) to validate context sufficiency
5. **Measure improvement** in cloze candidate quality

---

## Baseline Metrics Summary

| Metric | Baseline | Status |
|--------|----------|--------|
| Consistency (Jaccard similarity) | TBD (requires detailed analysis) | Pending |
| Coverage % | TBD (requires manual analysis) | Pending |
| Statement count | 20 | ✅ Consistent |
| Cloze count | 73-76 | ✅ Consistent |
| Ambiguous statements | ~15% | ⚠️ Needs fixing |

---

**Analysis Date:** 2026-01-03
**Status:** Ready for prompt enhancement
