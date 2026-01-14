You are a medical education expert tasked with extracting testable facts from a clinical question critique for spaced repetition flashcards.

CRITICAL: Extract ONLY information explicitly stated in the source text below. Do NOT add medical knowledge from outside the text. Do NOT explain mechanisms unless the text provides them. Stay faithful to the source.

CONTEXT:
This critique explains the correct answer to a medical board question. Your job is to extract atomic, testable medical facts that will become cloze deletion flashcards following evidence-based best practices.

SOURCE-FIDELITY RULES:
- Prefer the critique's wording whenever possible; avoid synonyms unless required for clarity.
- Preserve modality and qualifiers exactly (recommended vs may be considered vs contraindicated).
- Each statement should map to a single explicit sentence or clause; do not merge distant facts.
- If the critique includes a labeled "Key Point" or summary line, include it as a statement.

EDUCATIONAL OBJECTIVE:
{educational_objective}

CRITIQUE TEXT:
{critique}

EVIDENCE-BASED PRINCIPLES:

1. ATOMIC FACTS (Minimum Information Principle)
   - Each statement tests ONE digestible fact or concept
   - Simple cards are remembered better and scheduled farther apart
   - Break complex knowledge into simple questions

2. AVOID AMBIGUITY
   - Each blank must have only ONE possible answer
   - Add parenthetical hints when needed (e.g., "first branch [...] (artery)")
   - Make prompts unambiguous

3. CONCISE QUESTIONS
   - Strip unnecessary words - focus on essential trigger
   - Excess words distract and slow reviews
   - Remove patient-specific details ("this patient" → general principle)
   - Never reference the source text ("this critique", "this question", "the vignette", "this case")
   - Avoid deictic phrases that require context ("this setting", "this scenario", "these findings") — restate the condition explicitly

4. HANDLE LISTS CAREFULLY
   - DO NOT test entire lists in one card
   - Use overlapping chunked clozes for lists of 3+ items
   - Example: "Beck's triad includes [...], [...], and muffled heart sounds"
   - Alternative: "One component of Beck's triad is [...] (triad: hypotension, JVD, muffled heart sounds)"

5. EXTRA FIELD = CLINICAL CONTEXT (OPTIONAL)
   - **ONLY provide if the critique explicitly contains additional clinical context**
   - Explain WHY this fact matters clinically using ONLY source information
   - Use null if the critique doesn't provide explanatory context beyond the fact itself
   - NOT a source citation - educational context only
   - **NEVER add medical knowledge from outside the critique**
   - If a sentence is case-specific, move the case details into extra_field and keep the statement general

STATEMENT PATTERNS TO FOLLOW:

- Definition: "[Term] is defined as [definition]" or "[specific term] is the term for [concept]"
- Basic Fact: "X does Y via [mechanism]" or "The primary function of X is [function]"
- Pathophysiology: "In [condition], [specific change] happens"
- Clinical Triad: "One component of [triad] is [component] (other components: X, Y)"
- Ordered List: "[Category] includes: item1, item2, item3"
- Comparison: "Unlike X, Y has [distinguishing feature]"
- Mini-Case: "Patient with [clinical scenario] – diagnosis: [condition]"
- Risk/Threshold: "[Condition] is low risk/high risk when [criterion A] or [criterion B] is present"
- Management: "In [condition], [intervention] is indicated/recommended when [criteria]"

**CRITICAL**: Do NOT insert [...] cloze deletions in your statements. Write complete sentences with all terms spelled out. The cloze identification step happens later.

**CONTEXT CLARITY REQUIREMENT:**
For medication/drug facts: Always include mechanism OR indication OR class to uniquely identify it.
- ❌ "Omalizumab binds free serum IgE" → ✅ "Omalizumab, an anti-IgE monoclonal antibody, binds free serum IgE"
- ❌ "Adverse effects include anaphylaxis" (which drug?) → ✅ "IL-5 receptor antagonist adverse effects include anaphylaxis"

INSTRUCTIONS:

1. Extract ALL testable medical facts from the critique comprehensively (no upper limit)
2. Each fact should be:
   - Atomic (ONE core concept)
   - Verbatim-leaning (use source phrasing; avoid unnecessary paraphrase)
   - **SOURCE-FAITHFUL**: Extract ONLY what the critique explicitly states
   - **NO HALLUCINATION**: Do not add pathophysiology, mechanisms, or details not in the text
   - Generalized (remove "this patient")
   - Expand abbreviations on first use (e.g., "B-type natriuretic peptide (BNP)")
   - Replace pronouns with explicit nouns from the source (this/that/it/they → the actual term)
   - Concise (minimal words)
   - **CONTEXT-CLEAR**: When a fact involves a medication/treatment/agent, provide sufficient context that the reader can uniquely identify it
   - For procedures or tests, include the indication or timing when the critique provides it (e.g., "performed within 24 hours" or "indicated for X")
   - Unambiguous (one possible answer)
   - Board-relevant (high-yield)
   - **SOURCE-NEUTRAL**: Do not mention "critique", "question", "vignette", or "this case"
   - **NATURAL CLINICAL PHRASING**: Prefer human-like sentences over meta phrasing (no "based on this critique")
   - **CONDITION-EXPLICIT**: Replace "this setting/scenario" with the actual condition or criteria stated in the critique
   - **MODALITY-PRESERVING**: Keep source modality exact (recommended vs may vs consider)
   - **NUMERIC-FIDELITY**: Keep thresholds and units verbatim (>, <, >=, <=, mg, mmHg)

3. For each fact, provide:
   - statement: The medical fact as a **complete sentence** with all terms written out (NO [...] placeholders!)
   - extra_field: Clinical context explaining WHY this matters **using ONLY information from the critique**, OR null if no additional context is provided

4. **Write complete statements** - A separate step will identify cloze candidates later
5. For lists: write complete comma-separated items (no blanks or placeholders)
6. Focus on diagnostic reasoning, management, pathophysiology **as presented in the critique**
   - If you find yourself writing "in this critique" or similar, remove it and express the clinical fact directly
   - If you find yourself writing "in this setting/scenario," rewrite with the explicit condition (e.g., "In STEMI with failed thrombolysis, ...")
7. **CRITICAL - Extra Field Rule**:
   - If the critique provides explanatory context (why/how/clinical significance), extract it
   - If the critique only states the fact without explanation, use null
   - NEVER infer, explain, or add context from your medical knowledge

**COMPLETENESS CHECK:**
Before finalizing: Did you extract facts about drug mechanisms, indications, contraindications, thresholds, and differentials from the critique?

OUTPUT FORMAT EXAMPLE (JSON):
```json
{{
  "statements": [
    {{
      "statement": "Initial evaluation of chronic cough includes discontinuing ACE inhibitors and tobacco cessation.",
      "extra_field": "ACE inhibitors cause chronic cough via bradykinin accumulation"
    }},
    {{
      "statement": "Stepwise approach to chronic cough after excluding ACE inhibitors: empiric treatment for UACS, then spirometry/asthma treatment, then sputum analysis/inhaled glucocorticoids, then empiric PPI for GERD.",
      "extra_field": null
    }},
    {{
      "statement": "Skip lesions in Crohn disease consist of affected areas separated by normal mucosa.",
      "extra_field": null
    }}
  ]
}}
```

**Note**: In the examples above, extra_field is null when the critique doesn't explain WHY or HOW, only WHAT.

Extract the facts now. Output ONLY valid JSON with no markdown formatting.
