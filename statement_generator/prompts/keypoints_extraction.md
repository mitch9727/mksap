You are a medical education expert tasked with refining pre-formatted clinical key points into testable flashcard statements.

CRITICAL: Extract ONLY information explicitly stated in the key points below. Do NOT add medical knowledge from outside the text. Stay faithful to the source.

CONTEXT:
These "key points" are already structured clinical takeaways from a medical question. Your job is to ensure they are formatted as clear, testable statements suitable for cloze deletion flashcards.

KEY POINTS:
{key_points}

EVIDENCE-BASED PRINCIPLES:

1. ATOMIC FACTS
   - Each statement tests ONE core concept
   - Keep it simple and focused

2. CONCISE
   - Key points may already be well-formatted; preserve good structure
   - Strip unnecessary words if present
   - Remove patient-specific references ("this patient" → general)

3. UNAMBIGUOUS
   - Ensure one clear answer for any blank
   - Add hints if needed (e.g., "(drug class)", "(organism)")

4. EXTRA FIELD = CLINICAL CONTEXT (OPTIONAL)
   - **ONLY provide if the key points explicitly contain additional clinical context**
   - Explain WHY this fact matters clinically using ONLY source information
   - Use null if the key points don't provide explanatory context beyond the fact itself
   - **NEVER add medical knowledge from outside the key points**

INSTRUCTIONS:

1. Process each key point into a testable statement
2. Minimal rewriting - key points are often high-quality already
3. If a key point contains multiple facts, consider splitting
4. Each statement should be:
   - Atomic (one core concept)
   - Generalized (no "this patient")
   - Clinically accurate
   - Board-relevant

5. For each statement, provide:
   - statement: The refined medical fact
   - extra_field: Clinical context from source OR null if not provided

6. **CRITICAL - Extra Field Rule**:
   - If the key points provide explanatory context (why/how/clinical significance), extract it
   - If the key points only state the fact without explanation, use null
   - NEVER infer, explain, or add context from your medical knowledge

OUTPUT FORMAT (JSON):
```json
{{
  "statements": [
    {{
      "statement": "Initial management of chronic cough includes tobacco cessation and discontinuation of ACE inhibitor therapy.",
      "extra_field": "ACE inhibitors are a common reversible cause of chronic cough"
    }},
    {{
      "statement": "Empiric stepwise approach to chronic cough begins with treatment for upper airway cough syndrome.",
      "extra_field": null
    }},
    {{
      "statement": "Mild hypercalcemia is treated by avoiding dehydration.",
      "extra_field": null
    }}
  ]
}}
```

**Note**: Use null when the key point doesn't explain WHY or HOW, only WHAT.

Process the key points now. Output ONLY valid JSON with no markdown formatting.