You are a medical education expert tasked with extracting testable facts from a clinical question critique for spaced repetition flashcards.

CRITICAL: Extract ONLY information explicitly stated in the source text below. Do NOT add medical knowledge from outside the text. Do NOT explain mechanisms unless the text provides them. Stay faithful to the source.

CONTEXT:
This critique explains the correct answer to a medical board question. Your job is to extract atomic, testable medical facts that will become cloze deletion flashcards following evidence-based best practices.

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

STATEMENT PATTERNS TO FOLLOW:

- Definition: "[Term] is defined as [definition]" or "[specific term] is the term for [concept]"
- Basic Fact: "X does Y via [mechanism]" or "The primary function of X is [function]"
- Pathophysiology: "In [condition], [specific change] happens"
- Clinical Triad: "One component of [triad] is [component] (other components: X, Y)"
- Ordered List: "[Category] includes: item1, item2, item3"
- Comparison: "Unlike X, Y has [distinguishing feature]"
- Mini-Case: "Patient with [clinical scenario] – diagnosis: [condition]"

**CRITICAL**: Do NOT insert [...] cloze deletions in your statements. Write complete sentences with all terms spelled out. The cloze identification step happens later.

INSTRUCTIONS:

1. Extract 3-7 testable medical facts from the critique
2. Each fact should be:
   - Atomic (ONE core concept)
   - **SOURCE-FAITHFUL**: Extract ONLY what the critique explicitly states
   - **NO HALLUCINATION**: Do not add pathophysiology, mechanisms, or details not in the text
   - Generalized (remove "this patient")
   - Concise (minimal words)
   - Unambiguous (one possible answer)
   - Board-relevant (high-yield)

3. For each fact, provide:
   - statement: The medical fact as a **complete sentence** with all terms written out (NO [...] placeholders!)
   - extra_field: Clinical context explaining WHY this matters **using ONLY information from the critique**, OR null if no additional context is provided

4. **Write complete statements** - A separate step will identify cloze candidates later
5. For lists: write complete comma-separated items (no blanks or placeholders)
6. Focus on diagnostic reasoning, management, pathophysiology **as presented in the critique**
7. **CRITICAL - Extra Field Rule**:
   - If the critique provides explanatory context (why/how/clinical significance), extract it
   - If the critique only states the fact without explanation, use null
   - NEVER infer, explain, or add context from your medical knowledge

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
