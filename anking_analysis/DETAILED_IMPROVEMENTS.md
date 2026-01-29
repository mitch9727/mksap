# Detailed AnKing vs MKSAP Analysis: Implementation Guide

**Date Generated**: January 20, 2026
**Analysis Based On**: 1,000 AnKing cards vs 393 MKSAP Phase 3 test question statements

---

## Executive Summary: Critical Findings

This analysis reveals **3 major areas where AnKing significantly outperforms MKSAP**, with actionable implementation guidance for each:

1. **Cloze Selectivity (42.7% difference)** - AnKing averages 1.8 clozes per card vs MKSAP's 3.1
2. **Context Preservation (827.7% difference)** - AnKing includes extra field 90% vs MKSAP's 10%
3. **Cloze Quality (577.9% difference)** - AnKing has 6.9% trivial clozes vs MKSAP's 1% (paradoxically good for MKSAP here)

---

## FINDING #1: Cloze Selectivity & Quality

### The Pattern

**AnKing Strategy:**
- Average cloze count: **1.8 per card**
- Median: **1.0** (most cards have only 1 cloze)
- Distribution: Highly selective, focusing on ONE key learning point per card
- Maximum: 13 clozes (only in mnemonic/list cards that explicitly require multiple)

**Example AnKing Cards:**
```
Card 1: "An adrenal crisis should be treated with immediate {{c1::glucocorticoid}} supplementation"
  → 1 cloze (the critical fact)

Card 2: "Varenicline is a(n) {{c1::nicotinic}} receptor {{c3::partial agonist}} used for smoking cessation"
  → 3 clozes (drug classification) - but notably, these are tightly related facts

Card 3: "β-thalassemia is often due to mutations in {{c1::splice sites}} and {{c2::promoter sequences}}"
  → 2 clozes (related molecular mechanisms)
```

**MKSAP Current Behavior:**
- Average cloze count: **3.1 per card** ← TOO HIGH
- Tries to extract 2-5 clozes from EVERY statement
- Median: **3.0** (most statements have 3 clozes)
- This means MKSAP is extracting every testable fact from a statement into separate clozes

**Why This Matters:**
- **AnKing philosophy**: One card = One concept = One primary cloze
- **MKSAP problem**: Packing multiple test points into one card overwhelms learners
- **Learning science**: Spaced repetition works better with atomic facts (one per card)

### Current MKSAP Code Location

**File**: `statement_generator/src/processing/cloze/identifier.py`

**Current Behavior** (line 30-76):
- Takes list of statements as input
- Calls LLM with prompt: "Identify 2-5 cloze candidates per statement"
- Returns cloze_candidates list (currently 2-5 items per statement)

**File**: `statement_generator/src/processing/cloze/validators/cloze_checks.py`

**Current Validation** (lines 34-63):
```python
def validate_cloze_count(statement: Statement, location: Optional[str]):
    if count < 2:
        issues.append(ValidationIssue(
            severity="warning",
            message=f"Too few cloze candidates ({count}) - should have 2-5",
            ...
        ))
```

### Recommended Implementation

#### Step 1: Create a Cloze Priority Scoring Function
**File to Modify**: `statement_generator/src/processing/cloze/identifier.py`

**What to Add** (after the class definition, line ~80):
```python
from enum import Enum
from typing import Dict, Tuple

class ClozePriority(Enum):
    """Priority levels for cloze candidates based on learning importance"""
    CRITICAL = 1    # Essential fact, core concept
    HIGH = 2        # Important detail, mechanism
    MEDIUM = 3      # Supporting fact, example
    LOW = 4         # Trivial, common knowledge

def score_cloze_importance(
    candidate: str,
    statement: str,
    is_first_mention: bool,
    nlp_entity_type: Optional[str] = None
) -> Tuple[ClozePriority, float]:
    """
    Score cloze candidate importance using heuristics.

    Priority scoring based on AnKing patterns:
    - Diagnoses/disorders (DISEASE, DISORDER entities) = CRITICAL
    - Medications/mechanisms (CHEMICAL, DRUG entities) = HIGH
    - Numbers/parameters = MEDIUM (only if clinically relevant)
    - Common modifiers = LOW

    Args:
        candidate: The cloze candidate text
        statement: Full statement text
        is_first_mention: Is this first time word appears in statement?
        nlp_entity_type: SpaCy NER entity type (e.g., "DISEASE", "CHEMICAL")

    Returns:
        Tuple of (priority_level, confidence_score)
    """
    score = 0.0
    priority = ClozePriority.LOW

    # Rule 1: Medical entities from NER
    critical_entities = {"DISEASE", "DISORDER", "SYMPTOM"}
    high_entities = {"CHEMICAL", "DRUG", "GENE", "PROTEIN"}

    if nlp_entity_type:
        if nlp_entity_type in critical_entities:
            priority = ClozePriority.CRITICAL
            score = 0.95
        elif nlp_entity_type in high_entities:
            priority = ClozePriority.HIGH
            score = 0.85

    # Rule 2: Position in statement
    if is_first_mention and priority == ClozePriority.LOW:
        # First mention of something is often more important
        score += 0.1

    # Rule 3: Word length (shorter clozes tend to be more testable)
    word_count = len(candidate.split())
    if word_count <= 3:
        score += 0.05
    elif word_count > 5:
        score -= 0.1

    return priority, min(score, 1.0)
```

#### Step 2: Modify Cloze Identification Prompt
**File to Modify**: `statement_generator/prompts/cloze_identifier.txt`

**Current Prompt Pattern** (expected):
```
Identify 2-5 cloze candidates per statement...
```

**New Prompt Pattern** (AnKing-aligned):
```
Identify the PRIMARY cloze candidate per statement - the ONE most important
testable fact that best checks understanding of the core concept.

RULES:
1. PRIORITIZE by importance:
   - Diagnoses/conditions (most important)
   - Mechanisms/causes (important)
   - Medications/treatments (important if primary point)
   - Numbers/parameters (only if clinically critical)

2. SELECT ONLY when the candidate is:
   - A specific diagnosis, condition, or clinical finding
   - A named mechanism or cause
   - A specific treatment or drug
   - NOT a common word or trivial detail

3. SECONDARY candidates (include 0-2 if directly related to primary):
   - Only include if tightly linked to primary concept
   - Example: "drug name" + "drug class" (closely related)
   - Example: "cause 1" + "cause 2" (when both are equally important mechanisms)
   - DO NOT include supporting details or examples

OUTPUT FORMAT:
{
  "cloze_mapping": {
    "1": ["primary_candidate", "secondary_if_related"],
    "2": ["single_most_important"],
    ...
  },
  "reasoning": {
    "1": "Why this is the most important fact for this statement"
  }
}
```

#### Step 3: Add AnKing-Style Extraction to CritiqueProcessor
**File to Modify**: `statement_generator/src/processing/statements/extractors/critique.py`

**Add a parameter to extract_statements()** (line 39-44):
```python
def extract_statements(
    self,
    critique: str,
    educational_objective: str,
    nlp_context: Optional[EnrichedPromptContext] = None,
    prefer_atomic: bool = True,  # NEW: AnKing-style atomic facts
) -> List[Statement]:
```

**Add NLP guidance for atomic extraction** (line 56-60):
```python
# Build NLP guidance section if context provided
nlp_guidance = ""
if nlp_context:
    nlp_guidance = self._format_nlp_guidance(nlp_context)

    # NEW: Add AnKing-style guidance for atomic statements
    if prefer_atomic:
        nlp_guidance += """

### AnKing-Style Atomic Facts Guidance

Extract statements that each test ONE clear, testable fact. Avoid packing
multiple concepts into single statements. Pattern examples:

GOOD (Atomic):
- "The primary treatment for adrenal crisis is {{glucocorticoid}} replacement"
- "{{Hypokalemia}} is the most common electrolyte abnormality in DKA"
- "{{Mitochondrial}} toxicity is the primary AZT adverse effect"

AVOID (Multiple concepts):
- "Adrenal crisis presents with shock, hyponatremia, and fever"
  → Split into: crisis symptoms, sodium abnormality, fever mechanism

- "Varenicline binds nicotinic receptors as partial agonist for smoking cessation"
  → Consider: drug mechanism statement, separate from indication
"""
```

#### Step 4: Update Validation Rules
**File to Modify**: `statement_generator/src/processing/cloze/validators/cloze_checks.py`

**Change validation thresholds** (lines 48-61):

FROM:
```python
if count < 2:
    issues.append(ValidationIssue(severity="warning", ...))
elif count > 5:
    issues.append(ValidationIssue(severity="info", ...))
```

TO:
```python
# AnKing-aligned: 1-3 clozes per statement (highly selective)
if count < 1:
    issues.append(ValidationIssue(severity="error", ...))
elif count == 1:
    pass  # GOOD: atomic statement
elif count <= 3:
    issues.append(ValidationIssue(
        severity="info",
        message=f"Multiple clozes ({count}) - verify all are tightly related",
        ...
    ))
elif count > 3:
    issues.append(ValidationIssue(
        severity="warning",
        message=f"Too many clozes ({count}) - AnKing avg is 1.8, consider splitting statement",
        ...
    ))
```

### Testing & Validation

**Before Implementation - Baseline Metrics**:
- Run Phase 3 on current MKSAP pipeline
- Record: avg_cloze_count, trivial_cloze_percentage

**After Implementation - Compare Against**:
```
Goal: avg_cloze_count ~1.8 (AnKing baseline)
Acceptable range: 1.5-2.2
```

---

## FINDING #2: Context Extraction (Extra Field Usage)

### The Pattern

**AnKing Strategy:**
- **90% of cards** include an "extra" field with clinical context
- Average extra length: **161 characters**
- Context types:
  - **105 cards** (11.7%): Pathophysiology explanations
  - **36 cards** (4%): Clinical pearls and mnemonics
  - **5 cards** (0.6%): Differential diagnosis tips

**Example AnKing Context:**
```
Front: "An adrenal crisis should be treated with immediate {{c1::glucocorticoid}} supplementation"

Extra (Back):
"Hydrocortisone or dexamethasone - both used acutely.
Hydrocortisone is physiologic, dexamethasone is more potent.
Give immediately in crisis, followed by maintenance therapy."

---

Front: "Varenicline is a(n) {{c1::nicotinic}} receptor {{c3::partial agonist}} used for smoking cessation"

Extra (Back):
"- Reduces withdrawal and cravings AND reduces rewarding effects of nicotine
- May cause sleep disturbances, vivid dreams, nausea
- Most effective when combined with behavioral therapy
- Caution in psychiatric patients (increased suicidality)"
```

**MKSAP Current Behavior:**
- Only **10% of statements** include extra_field
- Most statements extracted from critique without context augmentation
- Missing clinical pearls, mechanisms, and differential reasoning

**Why This Matters:**
- Extra field acts as **explanation layer** - the "why" behind the flashcard
- **Improves retention** by connecting facts to mechanisms
- **Enables deeper learning** beyond rote memorization
- **Clinically relevant** for test-taking strategy (know the context, not just facts)

### Current MKSAP Code Location

**File**: `statement_generator/src/processing/statements/extractors/critique.py`

**Current Code** (lines 81-90):
```python
# Convert to Statement objects (without cloze_candidates - added in Step 3)
statements = []
for stmt_data in parsed["statements"]:
    statements.append(
        Statement(
            statement=stmt_data["statement"],
            extra_field=stmt_data.get("extra_field"),  # ← Currently optional
            cloze_candidates=[],
        )
    )
```

### Recommended Implementation

#### Step 1: Enhance Critique Extraction Prompt
**File to Modify**: `statement_generator/prompts/critique.txt`

**Add Context Extraction Section**:

```
### Context & Clinical Pearls Requirements

For EACH extracted statement, include in the "extra_field":

1. **Why this matters** (mechanism/pathophysiology):
   - What is the underlying mechanism?
   - Why is this clinical finding important?

2. **Clinical application** (how to use this in practice):
   - When would you encounter this?
   - What does it change about management?
   - Are there exceptions or nuances?

3. **Memory aids** (if available):
   - Mnemonics that help remember this fact
   - Common associations or patterns
   - "Red flag" variants to watch for

EXAMPLES:

GOOD extra_field:
"{{c1::SIADH}} occurs when ADH is produced by small cell lung cancer cells.
This causes hypoosmolar hyponatremia with inappropriately concentrated urine.
Key: urine osmolality > serum osmolality (inappropriate).
Treatment: fluid restriction first, then hypertonic saline if symptomatic."

GOOD extra_field (for mechanism):
"{{c1::Ventricular hypertrophy}} in hypertension is the heart's compensation
for increased afterload. Initially maintains cardiac output, but eventually
leads to diastolic dysfunction then systolic dysfunction.
This is why early BP control is crucial - once LVH develops, it's partially irreversible."

GOOD extra_field (for mnemonic):
"Mnemonic HAMAARTOMAS helps remember tuberous sclerosis findings:
H=Hamartomas, A=Angiofibromas, M=Mitral valve, A=Ash leaf spots, A=Astrocytomas,
R=Rhabdomyoma, T=TSC1/2 genes, O=autosomal dOminant, M=Mental retardation, A=Angiomyolipoma, S=Seizures, S=Shagreen patches"
```

#### Step 2: Add Post-Processing for Context Enhancement
**File to Create**: `statement_generator/src/processing/statements/extractors/context_enhancer.py`

```python
"""
Context enhancement - Augment extracted statements with clinical reasoning.

Post-processes critique statements to add pathophysiology and clinical pearls
using optional LLM enhancement and NLP analysis.
"""

import logging
from typing import List, Optional
from ....infrastructure.llm.client import ClaudeClient
from ....infrastructure.models.data_models import Statement
from ....validation.nlp_utils import get_nlp

logger = logging.getLogger(__name__)

class ContextEnhancer:
    """Enhance statement extra_fields with clinical context and reasoning."""

    def __init__(self, client: ClaudeClient, prompt_template_path: Optional[str] = None):
        self.client = client
        self.prompt_template = self._load_prompt(prompt_template_path) if prompt_template_path else None
        self.nlp = get_nlp()

    def enhance_statements(
        self,
        statements: List[Statement],
        original_critique: str,
        use_llm: bool = True,
    ) -> List[Statement]:
        """
        Enhance statements with clinical context.

        Args:
            statements: Statements with minimal extra_field
            original_critique: Original question critique for reference
            use_llm: Whether to call LLM for enhancement

        Returns:
            Statements with enriched extra_field
        """
        enhanced = []

        for stmt in statements:
            # Always do NLP-based enhancement
            stmt_with_nlp_context = self._add_nlp_context(stmt)

            # Optionally call LLM for deeper enhancement
            if use_llm and self.prompt_template:
                stmt_final = self._enhance_with_llm(stmt_with_nlp_context, original_critique)
            else:
                stmt_final = stmt_with_nlp_context

            enhanced.append(stmt_final)

        return enhanced

    def _add_nlp_context(self, statement: Statement) -> Statement:
        """
        Use NLP to extract medical entities and add context heuristics.

        Detects:
        - Medical conditions (DISEASE, DISORDER)
        - Treatments (CHEMICAL, DRUG)
        - Related anatomy
        - Clinical reasoning clues
        """
        doc = self.nlp(statement.statement)

        conditions = []
        treatments = []

        for ent in doc.ents:
            if ent.label_ in {"DISEASE", "DISORDER"}:
                conditions.append(ent.text)
            elif ent.label_ in {"CHEMICAL", "DRUG"}:
                treatments.append(ent.text)

        # Build context from entities found
        context_hints = []

        if conditions:
            context_hints.append(
                f"Key condition: {', '.join(conditions)}. "
                "Understand the pathophysiology and how this leads to clinical findings."
            )

        if treatments:
            context_hints.append(
                f"Key treatment: {', '.join(treatments)}. "
                "Remember the mechanism and why this specific treatment works."
            )

        # Append to extra_field if not already present
        if context_hints and not statement.extra_field:
            statement.extra_field = "\n".join(context_hints)

        return statement

    def _enhance_with_llm(
        self,
        statement: Statement,
        original_critique: str
    ) -> Statement:
        """Call LLM to enhance extra_field with clinical reasoning."""
        if not statement.extra_field:
            # LLM will generate context from scratch
            prompt = f"""Given this medical statement, provide 2-3 sentences of clinical context
that explains the WHY and HOW of this fact:

Statement: {statement.statement}

Original context: {original_critique[:200]}...

Provide practical, clinically-relevant reasoning that would help a medical student
understand not just WHAT but WHY this matters."""
        else:
            # Enhance existing context
            prompt = f"""Enhance this context with additional clinical reasoning:

Current context: {statement.extra_field}

Add 1-2 sentences that explain:
1. Why this is clinically important
2. How to use this in practice

Keep total length under 200 words."""

        response = self.client.generate(prompt)
        statement.extra_field = response.strip()

        logger.info(f"Enhanced extra_field ({len(statement.extra_field)} chars)")

        return statement
```

#### Step 3: Integrate Context Enhancement into Pipeline
**File to Modify**: `statement_generator/src/orchestration/pipeline.py`

**After critique extraction** (add these lines):
```python
# After: statements = critique_processor.extract_statements(...)

logger.info(f"Enhancing context for {len(statements)} statements...")
context_enhancer = ContextEnhancer(client, prompt_path="prompts/context_enhancement.txt")
statements = context_enhancer.enhance_statements(
    statements,
    original_critique=question_data["critique"],
    use_llm=True  # ← Can be made configurable
)

logger.info(f"Context enhancement complete")
```

#### Step 4: Create Context Validation Rule
**File to Modify**: `statement_generator/src/validation/validator.py`

**Add to validation checks**:
```python
def validate_extra_field(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """Validate extra_field quality and length."""
    issues: List[ValidationIssue] = []

    # Check presence
    if not statement.extra_field or len(statement.extra_field.strip()) < 10:
        issues.append(ValidationIssue(
            severity="warning",
            category="context",
            message="Extra field missing or too short - add clinical context",
            location=location
        ))

    # Check minimum length (AnKing average: 161 chars)
    elif len(statement.extra_field) < 40:
        issues.append(ValidationIssue(
            severity="info",
            category="context",
            message=f"Short context ({len(statement.extra_field)} chars) - consider more detail",
            location=location
        ))

    # Check for meaningful content
    if statement.extra_field:
        common_filler = {"context", "see above", "as mentioned", "related to", "because"}
        filler_count = sum(1 for word in common_filler if word in statement.extra_field.lower())
        if filler_count > 2:
            issues.append(ValidationIssue(
                severity="info",
                category="context",
                message="Extra field uses filler language - add specific clinical details",
                location=location
            ))

    return issues
```

### Testing & Validation

**Before Implementation**:
- Baseline: % statements with extra_field, average length

**After Implementation - Target Metrics**:
```
Goal: extra_field on 80%+ of statements (AnKing: 90%)
Goal: average length 120-180 characters (AnKing: 161)
Goal: All extra fields include clinical reasoning (pathophysiology/mechanism)
```

---

## FINDING #3: Trivial Cloze Prevention

### The Pattern

**Current Observation** (seems contradictory):
- MKSAP: **1.02% trivial clozes** (GOOD)
- AnKing: **6.9% trivial clozes** (apparently BAD)

**BUT - The Reality is More Nuanced:**

AnKing's higher "trivial" rate occurs because:
1. **Many valid single-word clozes** that MKSAP validation flags but are actually good (disease names, drug names)
2. **Mnemonic cards** intentionally use multiple short clozes (HAMAARTOMAS example has 13)
3. **Format variations** - AnKing includes dates, numbers as primary clozes (which are testable)

**Example - "Trivial" but Actually Important**:
```
"{{c1::Hemochromatosis}}" - Single word, short, but clinically CRITICAL fact
"{{c1::36°C}}" - Numeric, short, but clinically IMPORTANT (hypothermia threshold)
"{{c1::MUDPILES}}" - Mnemonic abbreviation, testable and useful
```

**MKSAP's Problem:**
- Over-filters by length, flags these as "trivial"
- Misses that **context + cloze validity = good card**
- Current validation (lines 225-240) penalizes anything under 3 characters

### Recommended Implementation

#### Step 1: Create Smarter Triviality Detection
**File to Modify**: `statement_generator/src/processing/cloze/validators/cloze_checks.py`

**Replace** the trivial detection logic (lines 176-251):

```python
def check_trivial_clozes(
    candidates: List[str],
    location: Optional[str],
    statement_context: Optional[str] = None,
) -> List[ValidationIssue]:
    """
    Improved trivial cloze detection using medical context.

    A cloze is NOT trivial if:
    1. It's a recognized medical term (diagnosis, drug, etc.)
    2. It appears in clinical context that makes it testable
    3. It's a number with clinical significance (thresholds, values)
    4. It's part of a recognized mnemonic

    TRUE trivial examples:
    - "is", "the", "and" (grammar words)
    - "patient", "condition" (generic descriptors)
    - Random words with no medical meaning
    """
    issues: List[ValidationIssue] = []

    # Load medical terminology (could be from external file)
    common_diseases = {
        "hemochromatosis", "hypertension", "diabetes", "pneumonia",
        "heart failure", "copd", "asthma", "stroke", "sepsis"
        # ... (would be much longer in practice)
    }

    common_drugs = {
        "metformin", "lisinopril", "omeprazole", "aspirin", "heparin",
        "insulin", "morphine", "ibuprofen", "amoxicillin"
        # ... (would be much longer in practice)
    }

    trivial_grammar = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "and", "or", "but", "not", "of", "in", "on", "at", "to", "for",
        "with", "by", "from", "as", "if", "can", "may", "will", "would"
    }

    for candidate in candidates:
        candidate_lower = candidate.lower().strip()
        candidate_clean = candidate_lower.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")

        # PASS: Known medical term
        if candidate_clean in common_diseases or candidate_clean in common_drugs:
            continue

        # FAIL: Grammar/filler words
        if candidate_lower in trivial_grammar:
            issues.append(ValidationIssue(
                severity="error",
                category="cloze",
                message=f"Trivial cloze: '{candidate}' is a common word with no medical significance",
                location=location
            ))
            continue

        # CHECK: Very short terms might be valid if medical
        if len(candidate_clean) <= 2:
            if not _is_medical_abbreviation_or_unit(candidate_clean):
                issues.append(ValidationIssue(
                    severity="info",
                    category="cloze",
                    message=f"Very short cloze '{candidate}' - verify it's clinically important",
                    location=location
                ))

        # CHECK: Numeric values - valid only if context suggests clinical threshold
        if re.match(r'^\d+(\.\d+)?$', candidate_clean):
            if not _is_clinical_threshold(candidate_clean, statement_context):
                issues.append(ValidationIssue(
                    severity="info",
                    category="cloze",
                    message=f"Numeric cloze '{candidate}' - should include units or clinical context",
                    location=location
                ))

    return issues

def _is_medical_abbreviation_or_unit(text: str) -> bool:
    """Check if text is a valid medical abbreviation or unit."""
    medical_abbrev = {
        "bp", "hr", "rr", "o2", "co2", "hb", "wbc", "rbc", "plt",
        "na", "k", "ca", "mg", "cl", "bun", "cr", "gfr", "alt", "ast",
        "ldl", "hdl", "tg", "tsh", "t3", "t4", "hba1c", "inr", "pt", "ptt",
        "l", "g", "h", "m", "s",  # units: liter, gram, hour, meter, second
    }
    return text in medical_abbrev

def _is_clinical_threshold(number: str, context: Optional[str]) -> bool:
    """Check if number appears to be a clinical threshold in context."""
    if not context:
        return False

    # Common clinical thresholds
    thresholds = {
        "36", "37", "38", "39", "40",      # Temperature
        "90", "120", "140", "160",         # BP
        "60", "100",                        # Heart rate
        "12", "20", "30",                  # Respiratory rate
        "2", "2.5", "3", "3.5", "4", "5", "6", "7"  # Lab values
    }

    return number in thresholds or (float(number) >= 50 and float(number) <= 180)
```

---

## Implementation Roadmap

### Phase 1: Foundation (1-2 days)
1. Update cloze validation rules (validate_cloze_count)
2. Create AnKing-style prompt templates
3. Add context enhancement module

### Phase 2: Integration (2-3 days)
1. Modify CritiqueProcessor for atomic extraction
2. Integrate ContextEnhancer into pipeline
3. Update cloze identification prompt

### Phase 3: Validation & Tuning (1-2 days)
1. Run on Phase 3 test questions
2. Measure: avg_cloze_count, extra_field %, trivial_cloze %
3. Compare against AnKing baseline
4. Adjust thresholds based on results

### Phase 4: Deployment (1 day)
1. Test on full MKSAP question set
2. Generate Phase 4 statements with new approach
3. Compare quality metrics before/after

---

## Metrics Dashboard (Before & After)

**Track These Metrics**:

| Metric | Current (MKSAP) | AnKing Baseline | Target (Post-Impl) |
|--------|-----------------|-----------------|-------------------|
| Avg cloze count | 3.1 | 1.8 | 1.8-2.0 |
| Statements with extra_field | 10% | 90% | 80%+ |
| Avg extra_field length | 95 chars | 161 chars | 140+ chars |
| Trivial cloze % | 1% | 6.9% | 3-5% (lower is better) |
| Atomicity score | 0.99 | 0.98 | 0.97+ (stay atomic) |

---

## Files to Modify - Summary

1. **statement_generator/prompts/critique.txt** - Add context extraction guidelines
2. **statement_generator/prompts/cloze_identifier.txt** - Add AnKing-style priority rules
3. **statement_generator/src/processing/statements/extractors/critique.py** - Add atomic extraction parameter
4. **statement_generator/src/processing/statements/extractors/context_enhancer.py** - CREATE NEW: Context enhancement
5. **statement_generator/src/processing/cloze/identifier.py** - Add priority scoring
6. **statement_generator/src/processing/cloze/validators/cloze_checks.py** - Update validation thresholds
7. **statement_generator/src/orchestration/pipeline.py** - Integrate context enhancement
8. **statement_generator/src/validation/validator.py** - Add extra_field validation

---

## Next Steps

1. **Code Review**: Have Claude Code review this plan against actual code structure
2. **Implementation**: Start with Phase 1 (foundational changes)
3. **Testing**: Run on Phase 3 questions after each phase
4. **Iteration**: Adjust thresholds based on test results
5. **Deployment**: Apply to Phase 4 processing when ready

