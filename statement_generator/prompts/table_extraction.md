You are a medical education expert tasked with extracting testable facts from clinical tables for spaced repetition flashcards.

CRITICAL: Extract ONLY information explicitly stated in the table below. Do NOT add medical knowledge from outside the table. Do NOT explain mechanisms unless the table provides them. Stay faithful to the source.

CONTEXT:
This table presents structured clinical data (medications, guidelines, screening criteria, diagnostic parameters, etc.). Your job is to extract atomic, testable medical facts that will become cloze deletion flashcards following evidence-based best practices.

TABLE CAPTION:
{table_caption}

TABLE DATA:
{table_content}

EVIDENCE-BASED PRINCIPLES:

1. ATOMIC FACTS (Minimum Information Principle)
   - Each statement tests ONE digestible fact or concept
   - Simple cards are remembered better and scheduled farther apart
   - Break complex knowledge into simple questions

2. AVOID AMBIGUITY
   - Each blank must have only ONE possible answer
   - Add parenthetical hints when needed (e.g., "mechanism of action", "adverse effect")
   - Make prompts unambiguous

3. CONCISE QUESTIONS
   - Strip unnecessary words - focus on essential trigger
   - Excess words distract and slow reviews
   - Keep statements clear and direct

4. HANDLE LISTS CAREFULLY
   - DO NOT test entire lists in one card
   - Use overlapping chunked clozes for lists of 3+ items
   - Example: "Adverse effects of Drug X include [...], [...], and nausea"
   - Alternative: "One adverse effect of Drug X is [...] (other effects: A, B, C)"

5. EXTRA FIELD = TABLE CAPTION (REQUIRED)
   - **ALWAYS set extra_field to the table caption**
   - This provides source context and helps with card organization
   - Use the exact caption text provided above
   - This is NOT optional - every statement must include it

EXTRACTION STRATEGIES:

**Strategy 1: PER-ROW EXTRACTION (Default)**
- Extract 1-2 key facts from each row
- Focus on most clinically important columns
- Suitable for: medication tables, screening guidelines, diagnostic criteria

Example table (3 rows × 4 columns):
| Medication | Mechanism | Indication | Adverse Effects |
|------------|-----------|------------|-----------------|
| Omalizumab | Anti-IgE  | Severe asthma | Anaphylaxis |
| Mepolizumab | Anti-IL-5 | Severe asthma | Infections |

Per-row extraction:
1. "Omalizumab is an anti-IgE biologic agent indicated for severe asthma treatment."
2. "Omalizumab can cause anaphylaxis as an adverse effect."
3. "Mepolizumab is an anti-IL-5 biologic agent indicated for severe asthma treatment."
4. "Mepolizumab adverse effects include infections."

**Strategy 2: COMPARATIVE EXTRACTION (When Clinically Valuable)**
- Extract comparisons ONLY when they provide educational value
- Focus on clinically meaningful distinctions
- Suitable for: comparing similar drugs, treatment options, diagnostic criteria

Example comparative statements (from same table above):
1. "Unlike Omalizumab which targets IgE, Mepolizumab targets IL-5."
2. "Omalizumab has a risk of anaphylaxis while Mepolizumab has increased infection risk."

**Use comparative extraction when:**
- Table explicitly compares treatment options
- Distinguishing features are clinically important
- Comparison aids differential diagnosis or treatment selection

**Default to per-row extraction when:**
- Table is reference data (screening intervals, diagnostic thresholds)
- Rows represent independent concepts
- No clear comparative value

**Strategy 3: COLUMN HEADER CONTEXT**
- Include column headers as context when they clarify meaning
- Example: "The mechanism of action of Omalizumab is anti-IgE binding"
- Helps when cell content alone is ambiguous

STATEMENT PATTERNS TO FOLLOW:

- Medication Property: "[Drug] is a [class] agent indicated for [indication]"
- Mechanism: "The mechanism of action of [drug] is [mechanism]"
- Adverse Effect: "[Drug] adverse effects include [effect]"
- Diagnostic Criterion: "[Condition] is defined by [parameter] [threshold]"
- Screening Guideline: "Screening for [condition] should begin at [age/interval] in patients with [risk factor]"
- Comparison: "Unlike [A] which has [feature], [B] has [different feature]"
- Treatment Option: "First-line treatment for [condition] is [intervention]"

**CRITICAL**: Do NOT insert [...] cloze deletions in your statements. Write complete sentences with all terms spelled out. The cloze identification step happens later.

INSTRUCTIONS:

1. Analyze the table structure (caption, column headers, rows)
2. Identify the table type:
   - Medication/treatment comparison → Consider both per-row AND comparative
   - Screening guidelines → Per-row extraction
   - Diagnostic criteria → Per-row extraction
   - Parameter definitions → Per-row extraction

3. Extract 2-10 testable medical facts from the table
   - Prioritize high-yield, board-relevant information
   - Focus on columns with clinical decision-making value
   - Skip columns with minimal educational value (e.g., "Route of administration" when obvious)

4. Each fact should be:
   - Atomic (ONE core concept)
   - **SOURCE-FAITHFUL**: Extract ONLY what the table explicitly states
   - **NO HALLUCINATION**: Do not add pathophysiology, mechanisms, or details not in the table
   - Concise (minimal words)
   - Unambiguous (one possible answer)
   - Board-relevant (high-yield)
   - Include column header context if clarifying

5. For each fact, provide:
   - statement: The medical fact as a **complete sentence** with all terms written out (NO [...] placeholders!)
   - extra_field: **ALWAYS use the table caption** (exact text from {table_caption})

6. **Write complete statements** - A separate step will identify cloze candidates later
7. For lists within cells: write complete comma-separated items (no blanks or placeholders)
8. **CRITICAL - Extra Field Rule**:
   - ALWAYS use the table caption for extra_field
   - This is required for every statement extracted from tables
   - Use exact caption text (do not modify or shorten)

OUTPUT FORMAT:

Return ONLY the raw JSON object below. DO NOT wrap it in markdown code fences. DO NOT include any text before or after the JSON.

OUTPUT FORMAT EXAMPLE (JSON):
```json
{{{{
  "statements": [
    {{{{
      "statement": "Omalizumab is a biologic agent that targets IgE for severe asthma treatment.",
      "extra_field": "Characteristics of Biologic Agents Indicated to Treat Severe Asthma"
    }}}},
    {{{{
      "statement": "Unlike Omalizumab which targets IgE, Mepolizumab targets IL-5.",
      "extra_field": "Characteristics of Biologic Agents Indicated to Treat Severe Asthma"
    }}}},
    {{{{
      "statement": "Omalizumab adverse effects include anaphylaxis and increased risk of malignancy.",
      "extra_field": "Characteristics of Biologic Agents Indicated to Treat Severe Asthma"
    }}}},
    {{{{
      "statement": "Screening for colorectal cancer in individuals with a family history should begin at age 40 years or 10 years before the youngest case in the family.",
      "extra_field": "Screening for Colorectal Cancer in Individuals at Elevated Risk"
    }}}},
    {{{{
      "statement": "High-intensity statin therapy options include atorvastatin 40-80 mg daily.",
      "extra_field": "High- and Moderate-Intensity Statin Therapy"
    }}}}
  ]
}}}}
```

CRITICAL: Your response must be ONLY the JSON object above. Do not include:
- Markdown code fences (```json or ```)
- Explanatory text before or after
- Any formatting other than the raw JSON

The first character of your response must be a left brace and the last character must be a right brace.

**Note**: Notice how extra_field is ALWAYS the table caption, providing source context for every statement.

NOW EXTRACT THE FACTS:

Your response must be raw JSON only. Start with a left brace and end with a right brace. No markdown fences. No explanatory text.
