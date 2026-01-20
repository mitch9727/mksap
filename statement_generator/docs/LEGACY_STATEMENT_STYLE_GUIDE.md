# Legacy Statement Style Guide

**Last Updated**: January 13, 2026

## Purpose

This guide captures key excerpts from the former legacy statement set to calibrate statement quality, extras, and
tags. The original legacy folder has been removed to keep the docs lean. Use the examples below as reference only.
Do not overwrite current `true_statements`.

## How to Use the Old Method

1. Compare current outputs to the legacy excerpts in this guide.
2. Note differences in statement phrasing, extras, and tags.
3. Translate those differences into prompt or validation updates.
4. Re-run a small test batch and re-compare until outputs converge.

## Style Patterns to Preserve

### Statement tone and structure

- Atomic, stand-alone facts with minimal extra context.
- Verbatim-leaning phrasing; avoid synonyms unless required for clarity.
- Preserve modality ("recommended" vs "may be considered") and thresholds verbatim.
- Remove patient-specific details from statements; move them to extras.
- Keep explicit terms (replace pronouns and deictic phrases).
- Include "Key Point" content as a statement when present.

### Extra(s) / extra_field usage

- Use for clarifications, edge cases, and case-specific details.
- Keep short and tied to a single parent statement.
- Do not introduce new facts not present in the source.

### Related text

- Treat related text as a separate source of statements.
- Do not blend critique statements with related text statements.
- Tag related text separately when tags are added.

### Tables and supplemental material

- Derive statements directly from row-level table content.
- Preserve units, comparators, and footnote constraints verbatim.
- Do not invent derived statements for figures or videos.

## Legacy Examples (Excerpted)

### Main block excerpt (Critical Care)

```markdown
### Critical Care Medicine: Opioid Toxicity Treatment

#### True Statements
1. Opioid toxicity is characterized by respiratory depression, depressed level of consciousness, and miotic pupils.
2. Naloxone, an opioid antagonist, is the treatment of choice in opioid toxicity.
3. Naloxone has a short half-life, and its antidote effects often subside before the effects of the opioid.

#### Extra(s)
1. This patient suspected of having opioid toxicity responded to naloxone but developed recurrent respiratory
   depression, requiring additional naloxone.

#### Tags
#CriticalCare #Toxicology #OpioidToxicity #Naloxone #RespiratoryDepression
```

### Main + related text excerpt (Pulmonary)

```markdown
### Pulmonary Medicine: Obesity Hypoventilation Syndrome

#### True Statements
1. Obesity hypoventilation syndrome (OHS) is characterized by daytime hypercapnia, defined as an arterial partial
   pressure of carbon dioxide (Pco2) greater than 45 mm Hg (6.0 kPa).
2. A serum bicarbonate level >27 mEq/L (27 mmol/L) is a clue to the diagnosis of OHS.
3. The diagnosis of OHS requires exclusion of other causes of chronic hypoventilation, such as chronic obstructive
   pulmonary disease (COPD).

#### Extra(s)
2. Pulmonary function testing showing a normal FEV1/FVC ratio helps exclude COPD in suspected OHS.

#### Related Text Derivations
1. The hallmark of OHS is daytime hypercapnia (Pco2 >45 mm Hg [6.0 kPa]).
2. Positive airway pressure (PAP) therapy is indicated in OHS, with continuous positive airway pressure (CPAP)
   recommended for stable ambulatory patients.

#### Related Text Tags
#PulmonaryMedicine #SleepMedicine #ObesityHypoventilationSyndrome #OSA #CPAP
```

### Table-derived excerpt

```markdown
#### True Statements (from Table: Toxic Syndromes and Their Manifestations)
1. Sympathomimetic toxidrome manifests with tachycardia, hypertension, diaphoresis, agitation, seizures, and mydriasis.

#### Optional Extra(s)
1. Representative sympathomimetic drugs include cocaine, amphetamines, ephedrine, and caffeine.
```

## Tagging Guidance (Proposed)

### Canonical format

- PascalCase with no spaces, slashes, or punctuation.
- Acronyms remain uppercase (COPD, ARDS, OSA, ICU).
- 3-8 tags per block, anchored to explicit terms in the source.
- Always include a system tag and, when present, a care setting tag.

### Normalize common variants

- Prefer `#PulmonaryMedicine` + `#CriticalCare` over `#Pulm/CC` or `#PulmCC`.
- Use one care setting label consistently: `#AmbulatoryCare`, `#HospitalCare`, `#ICU`, `#EmergentCare`.
- Avoid mixing `#Pulmonary` with `#PulmonaryMedicine`; choose one canonical system tag.

### Example tag bundles (legacy-style)

- `#CriticalCare #Toxicology #OpioidToxicity #Naloxone #RespiratoryDepression`
- `#PulmonaryMedicine #AmbulatoryCare #SleepMedicine #ObesityHypoventilationSyndrome #Hypercapnia #CPAP`
- `#PulmonaryMedicine #ICU #ARDS #MechanicalVentilation #PEEP`
- `#PulmonaryMedicine #COPD #Spirometry #Bronchodilators #Exacerbation`
- `#CriticalCare #Sepsis #SepticShock #Antibiotics #Vasopressors`
- `#PulmonaryMedicine #PulmonaryHypertension #Echocardiography #RightHeartFailure`

## Prompt and Validation Alignment

Use the legacy style as a checklist when refining prompts and checks:

- `statement_generator/prompts/critique_extraction.md`:
  - Emphasize verbatim-leaning phrasing and minimal paraphrase.
  - Keep modality and thresholds exact; avoid inferred mechanisms.
  - Move case-specific language to `extra_field`.
- `statement_generator/prompts/keypoints_extraction.md`:
  - Keep key points intact unless multi-fact; split only when needed.
  - Preserve original modality and qualifiers.
- `statement_generator/prompts/table_extraction.md`:
  - Prefer row-level statements; keep units and footnotes verbatim.
- Validation checks:
  - Flag paraphrase drift (synonyms not present in source).
  - Flag missing key point content when provided in the input.

## Suggested Next Step

Choose 5 legacy files, run the current statement generator on their question IDs, and note differences. Apply the
prompt adjustments above to close the gaps, then re-test.
