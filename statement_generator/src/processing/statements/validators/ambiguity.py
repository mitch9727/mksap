"""
Ambiguity detection for cloze deletion flashcards.

Detects statements where blanking a cloze candidate could result in multiple
valid answers, violating the "one correct answer" principle of effective flashcards.

Based on Week 1 user feedback: medication/drug statements lacking mechanism,
indication, or class context become ambiguous when the drug name is blanked.

Example ambiguity:
- ❌ "Reslizumab adverse effects include anaphylaxis, headache, and helminth infections"
  → Blanking "Reslizumab" → Multiple biologics cause same effects
- ✅ "Reslizumab, an anti-IL-5 monoclonal antibody, adverse effects include..."
  → Mechanism provides unique identification
"""

import re
from typing import Dict, List, Optional, Set
from ..models import Statement
from .validator import ValidationIssue


# Medication-related terms that require context
MEDICATION_INDICATORS = [
    # Drug classes
    r'\b(medication|drug|therapy|agent|antibiotic|antiviral|antifungal)\b',
    # Specific drug suffixes
    r'\b\w+(mab|mib|nib|tinib|zumab|lizumab|ximab|umab)\b',  # Biologics
    r'\b\w+(pril|sartan|olol|dipine|statin|gliptin|flozin)\b',  # Common drug classes
    # Generic medication patterns
    r'\b[A-Z][a-z]+\s+(is|are)\s+(a|an|the)\s+\w+\b',  # "Drug is a beta-blocker"
]

# Context providers that disambiguate medications
CONTEXT_PROVIDERS = {
    # Mechanisms
    'mechanism': [
        r'\bmechanism of action\b',
        r'\bacts by\b',
        r'\bworks by\b',
        r'\binhibits\b',
        r'\bblocks\b',
        r'\bagonist\b',
        r'\bantagonist\b',
        r'\bbinds to\b',
        r'\btargets\b',
        r'\banti-\w+\b',  # anti-IgE, anti-IL-5, etc.
    ],
    # Drug classes
    'class': [
        r'\bmonoclonal antibody\b',
        r'\bbeta-blocker\b',
        r'\bACE inhibitor\b',
        r'\bARB\b',
        r'\bcalcium channel blocker\b',
        r'\bstatin\b',
        r'\bbiologic\b',
        r'\bimmunosuppressant\b',
        r'\banticoagulant\b',
        r'\bantiplatelet\b',
        r'\bdiuretic\b',
        r'\bvasodilator\b',
    ],
    # Indications
    'indication': [
        r'\bindicated for\b',
        r'\bused for\b',
        r'\bused to treat\b',
        r'\bfirst-line for\b',
        r'\btreatment for\b',
        r'\bapproved for\b',
    ],
}

# Effect/adverse event terms that could apply to multiple drugs
SHARED_EFFECTS = [
    'anaphylaxis', 'headache', 'nausea', 'vomiting', 'diarrhea',
    'fatigue', 'dizziness', 'rash', 'pruritus', 'infection',
    'hypertension', 'hypotension', 'tachycardia', 'bradycardia',
    'hyperkalemia', 'hypokalemia', 'hyperglycemia', 'hypoglycemia',
]


def validate_statement_ambiguity(
    statement: Statement,
    location: Optional[str],
    *,
    statement_doc=None,
) -> List[ValidationIssue]:
    """
    Run all ambiguity checks on a statement.

    Args:
        statement: Statement to validate
        location: Location string for error reporting

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # New detection functions (Week 2 additions)
    issues.extend(detect_ambiguous_medication_clozes(statement, location, statement_doc=statement_doc))
    issues.extend(detect_overlapping_candidates(statement, location))
    issues.extend(detect_ambiguous_organism_clozes(statement, location, statement_doc=statement_doc))
    issues.extend(detect_ambiguous_procedure_clozes(statement, location, statement_doc=statement_doc))

    # General cloze ambiguity (pronouns, vague terms, similar pairs)
    issues.extend(check_cloze_ambiguity(statement, location))

    # Numeric ambiguity
    issues.extend(check_numeric_ambiguity(statement, location))

    return issues


def check_medication_ambiguity(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check if medication/drug statements have sufficient context.

    Detects statements mentioning medications without mechanism, class, or indication
    that would make the statement ambiguous when the drug name is blanked.

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []
    stmt_text = statement.statement

    # Check if statement mentions a medication
    is_medication_statement = any(
        re.search(pattern, stmt_text, re.IGNORECASE)
        for pattern in MEDICATION_INDICATORS
    )

    if not is_medication_statement:
        return issues

    # Check if any cloze candidate is a drug name
    # (Capitalized words often indicate drug names in medical text)
    potential_drug_names = [
        c for c in statement.cloze_candidates
        if re.match(r'^[A-Z][a-z]+', c) and len(c) > 4  # Capitalized, >4 chars
    ]

    if not potential_drug_names:
        return issues

    # Check if statement has context providers
    has_mechanism = any(
        re.search(pattern, stmt_text, re.IGNORECASE)
        for pattern in CONTEXT_PROVIDERS['mechanism']
    )
    has_class = any(
        re.search(pattern, stmt_text, re.IGNORECASE)
        for pattern in CONTEXT_PROVIDERS['class']
    )
    has_indication = any(
        re.search(pattern, stmt_text, re.IGNORECASE)
        for pattern in CONTEXT_PROVIDERS['indication']
    )

    has_context = has_mechanism or has_class or has_indication

    # Check if statement mentions shared effects without context
    mentions_shared_effects = any(
        effect in stmt_text.lower() for effect in SHARED_EFFECTS
    )

    if not has_context and mentions_shared_effects:
        # This is the problematic pattern identified in Week 1
        issues.append(ValidationIssue(
            severity="warning",
            category="ambiguity",
            message=(
                f"Medication statement lacks disambiguating context (mechanism/class/indication). "
                f"When '{potential_drug_names[0]}' is blanked, multiple drugs could fit. "
                f"Consider adding: mechanism of action, drug class, or specific indication."
            ),
            location=location
        ))
    elif not has_context:
        # Milder warning for medication statements without shared effects
        issues.append(ValidationIssue(
            severity="info",
            category="ambiguity",
            message=(
                f"Medication statement may benefit from context (mechanism/class/indication) "
                f"to uniquely identify '{potential_drug_names[0]}'."
            ),
            location=location
        ))

    return issues


def check_cloze_ambiguity(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for general cloze deletion ambiguity.

    Detects cases where multiple cloze candidates could be valid answers
    when blanked, or where the statement provides insufficient context
    to uniquely determine the answer.

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Check for multiple similar cloze candidates (e.g., "Drug A" and "Drug B")
    similar_pairs = find_similar_cloze_pairs(statement.cloze_candidates)
    if similar_pairs:
        issues.append(ValidationIssue(
            severity="info",
            category="ambiguity",
            message=(
                f"Multiple similar cloze candidates may cause confusion: "
                f"{', '.join([f'{a}/{b}' for a, b in similar_pairs])}. "
                f"Ensure each has unique context when blanked."
            ),
            location=location
        ))

    # Check for pronouns as cloze candidates (inherently ambiguous)
    pronouns = ['it', 'this', 'that', 'these', 'those', 'they', 'them', 'their']
    pronoun_candidates = [c for c in statement.cloze_candidates if c.lower() in pronouns]
    if pronoun_candidates:
        issues.append(ValidationIssue(
            severity="warning",
            category="ambiguity",
            message=(
                f"Pronoun cloze candidates are ambiguous: {', '.join(pronoun_candidates)}. "
                f"Replace with specific nouns."
            ),
            location=location
        ))

    # Check for vague cloze candidates
    vague_terms = ['thing', 'condition', 'disease', 'disorder', 'syndrome', 'sign', 'symptom']
    vague_candidates = [c for c in statement.cloze_candidates if c.lower() in vague_terms]
    if vague_candidates:
        issues.append(ValidationIssue(
            severity="info",
            category="ambiguity",
            message=(
                f"Vague cloze candidates detected: {', '.join(vague_candidates)}. "
                f"Consider using specific medical terms."
            ),
            location=location
        ))

    return issues


def check_numeric_ambiguity(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for numeric values without sufficient context.

    Numbers alone can be ambiguous without units, ranges, or clinical context.

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Check for numeric cloze candidates
    for candidate in statement.cloze_candidates:
        # Pure numbers without units
        if re.match(r'^\d+(\.\d+)?$', candidate):
            issues.append(ValidationIssue(
                severity="warning",
                category="ambiguity",
                message=(
                    f"Numeric cloze candidate '{candidate}' lacks units or context. "
                    f"Include units (mg, mL, mmHg) or range (>30, <50) for clarity."
                ),
                location=location
            ))

        # Numbers with units but potentially ambiguous
        elif re.match(r'^\d+(\.\d+)?\s*[a-zA-Z]+$', candidate):
            # Check if statement provides clinical context (threshold, target, etc.)
            context_terms = ['greater than', 'less than', 'at least', 'threshold', 'target', 'goal']
            has_context = any(term in statement.statement.lower() for term in context_terms)

            if not has_context:
                issues.append(ValidationIssue(
                    severity="info",
                    category="ambiguity",
                    message=(
                        f"Numeric cloze candidate '{candidate}' may benefit from context "
                        f"(threshold, target, goal) to clarify clinical significance."
                    ),
                    location=location
                ))

    return issues


def find_similar_cloze_pairs(candidates: List[str]) -> List[tuple]:
    """
    Find pairs of cloze candidates that are similar (same prefix/suffix).

    Examples:
    - ("Omalizumab", "Mepolizumab") → same suffix "-mab"
    - ("beta-blocker", "alpha-blocker") → similar pattern

    Args:
        candidates: List of cloze candidates

    Returns:
        List of (candidate1, candidate2) tuples that are similar
    """
    similar_pairs = []

    # Check for common suffixes (drug classes)
    common_suffixes = ['mab', 'mib', 'nib', 'pril', 'sartan', 'olol', 'dipine', 'statin']

    for i, c1 in enumerate(candidates):
        for c2 in candidates[i+1:]:
            # Same suffix check
            for suffix in common_suffixes:
                if c1.lower().endswith(suffix) and c2.lower().endswith(suffix):
                    similar_pairs.append((c1, c2))
                    break

            # Similar word pattern check (e.g., "Drug A", "Drug B")
            if len(c1.split()) > 1 and len(c2.split()) > 1:
                c1_words = c1.split()
                c2_words = c2.split()
                # If most words match except one, they're similar
                if len(c1_words) == len(c2_words):
                    matching_words = sum(1 for w1, w2 in zip(c1_words, c2_words) if w1 == w2)
                    if matching_words >= len(c1_words) - 1:
                        similar_pairs.append((c1, c2))

    return similar_pairs


def check_patient_specific_language(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for patient-specific language that reduces generalizability.

    Flashcards should focus on general medical facts, not case-specific details.

    Examples to flag:
    - "The patient's blood pressure was..."
    - "She was started on..."
    - "His symptoms improved..."

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []
    stmt_lower = statement.statement.lower()

    # Patient pronouns
    patient_pronouns = [
        r'\bthe patient\b',
        r'\bthis patient\b',
        r'\bthe woman\b',
        r'\bthe man\b',
        r'\bshe\b',
        r'\bhe\b',
        r'\bhis\b',
        r'\bher\b',
        r'\bhim\b',
    ]

    found_pronouns = []
    for pattern in patient_pronouns:
        if re.search(pattern, stmt_lower):
            found_pronouns.append(pattern.strip(r'\b'))
            break  # Only flag once

    if found_pronouns:
        issues.append(ValidationIssue(
            severity="warning",
            category="quality",
            message=(
                f"Patient-specific language detected: {found_pronouns[0]}. "
                f"Rephrase as general medical fact for better flashcard utility. "
                f"Example: 'The patient has HTN' → 'Hypertension is defined as...' or "
                f"'First-line treatment for hypertension includes...'"
            ),
            location=location
        ))

    return issues


# New detection functions for Week 2 validation framework

def detect_ambiguous_medication_clozes(
    statement: Statement,
    location: Optional[str],
    *,
    statement_doc=None,
) -> List[ValidationIssue]:
    """
    Detect medications lacking mechanism/indication/class context.

    This is the core function for the Week 1 Reslizumab issue.
    Medications without disambiguating context become ambiguous when blanked.

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []
    stmt_text = statement.statement

    # Detect medication suffixes in cloze candidates (fallback when NLP is unavailable)
    medication_suffixes = [
        'mab', 'lizumab', 'zumab', 'ximab', 'umab',  # Biologics
        'nib', 'tinib',  # Kinase inhibitors
        'pril',  # ACE inhibitors
        'sartan',  # ARBs
        'olol',  # Beta blockers
        'statin',  # Statins
        'mycin',  # Antibiotics
    ]

    potential_medications = []

    if statement_doc is not None:
        entity_index = _build_entity_index(statement_doc)
        for candidate in statement.cloze_candidates:
            label = _match_candidate_entity(candidate, entity_index)
            if label and label in MEDICATION_ENTITY_LABELS:
                potential_medications.append(candidate)

    if not potential_medications:
        for candidate in statement.cloze_candidates:
            # Check if candidate ends with medication suffix
            if any(candidate.lower().endswith(suffix) for suffix in medication_suffixes):
                potential_medications.append(candidate)
            # Also check capitalized drug names (common pattern)
            elif re.match(r'^[A-Z][a-z]+$', candidate) and len(candidate) > 4:
                # If statement mentions drug/medication/therapy, this is likely a drug
                if re.search(r'\b(drug|medication|therapy|agent|treatment|used for)\b', stmt_text, re.IGNORECASE):
                    potential_medications.append(candidate)

    if not potential_medications:
        return issues

    # Check for disambiguating context
    has_mechanism = any(
        re.search(pattern, stmt_text, re.IGNORECASE)
        for pattern in CONTEXT_PROVIDERS['mechanism']
    )
    has_class = any(
        re.search(pattern, stmt_text, re.IGNORECASE)
        for pattern in CONTEXT_PROVIDERS['class']
    )
    has_indication = any(
        re.search(pattern, stmt_text, re.IGNORECASE)
        for pattern in CONTEXT_PROVIDERS['indication']
    )

    has_context = has_mechanism or has_class or has_indication

    # Check if statement mentions shared effects (increases ambiguity)
    mentions_shared_effects = any(
        effect in stmt_text.lower() for effect in SHARED_EFFECTS
    )

    if not has_context and mentions_shared_effects:
        # Critical issue: medication with shared effects but no context
        issues.append(ValidationIssue(
            severity="warning",
            category="ambiguity",
            message=(
                f"Medication statement lacks disambiguating context (mechanism/class/indication). "
                f"When '{potential_medications[0]}' is blanked, multiple drugs could fit. "
                f"Consider adding: mechanism of action, drug class, or specific indication."
            ),
            location=location
        ))
    elif not has_context:
        # Milder issue: medication without context but no obvious shared effects
        issues.append(ValidationIssue(
            severity="info",
            category="ambiguity",
            message=(
                f"Medication '{potential_medications[0]}' may benefit from context "
                f"(mechanism/class/indication) for unique identification."
            ),
            location=location
        ))

    return issues


def detect_overlapping_candidates(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Find overlapping cloze candidates (e.g., "severe asthma" and "asthma").

    Overlapping candidates can cause confusion and ambiguity in flashcards.

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    overlapping_pairs = find_overlapping_pairs(statement.cloze_candidates)

    if overlapping_pairs:
        pair_strings = [f"'{a}' / '{b}'" for a, b in overlapping_pairs]
        issues.append(ValidationIssue(
            severity="warning",
            category="ambiguity",
            message=(
                f"Overlapping cloze candidates detected: {', '.join(pair_strings)}. "
                f"When one is blanked, the other may provide the answer. "
                f"Consider removing overlapping terms or adding distinguishing context."
            ),
            location=location
        ))

    return issues


def detect_ambiguous_organism_clozes(
    statement: Statement,
    location: Optional[str],
    *,
    statement_doc=None,
) -> List[ValidationIssue]:
    """
    Detect organisms without clinical context.

    Organism names alone don't provide enough context for unique identification.
    Need: most common cause, typical presentation, endemic region, etc.

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    potential_organisms = []

    if statement_doc is not None:
        entity_index = _build_entity_index(statement_doc)
        for candidate in statement.cloze_candidates:
            label = _match_candidate_entity(candidate, entity_index)
            if label and label in ORGANISM_ENTITY_LABELS:
                potential_organisms.append(candidate)

    if not potential_organisms:
        # Detect organism pattern: Capitalized Genus + lowercase species
        organism_pattern = r'\b[A-Z][a-z]+\s+[a-z]+\b'
        non_organism_first_words = {
            "Failed",
            "Stress",
            "Coronary",
            "Urgent",
            "Persistent",
            "Recurrent",
        }
        non_organism_second_words = {
            "testing",
            "angiography",
            "reperfusion",
            "infarction",
            "dysfunction",
            "therapy",
            "treatment",
            "score",
            "findings",
        }

        for candidate in statement.cloze_candidates:
            if re.match(organism_pattern, candidate):
                # Additional validation: check if it looks like a real organism name
                words = candidate.split()
                if len(words) == 2:  # Genus species
                    if words[0] in non_organism_first_words:
                        continue
                    if words[1].lower() in non_organism_second_words:
                        continue
                    potential_organisms.append(candidate)

    if not potential_organisms:
        return issues

    # Check for clinical context indicators
    context_indicators = [
        r'\bmost common\b',
        r'\btypical\b',
        r'\bfirst-line\b',
        r'\busually\b',
        r'\bfrequently\b',
        r'\bendemic\b',
        r'\bcause of\b',
        r'\bassociated with\b',
    ]

    has_context = any(
        re.search(pattern, statement.statement, re.IGNORECASE)
        for pattern in context_indicators
    )

    if not has_context:
        for organism in potential_organisms:
            issues.append(ValidationIssue(
                severity="warning",
                category="ambiguity",
                message=(
                    f"Organism '{organism}' lacks clinical context. "
                    f"Add context like: 'most common cause of X', 'typically causes Y', "
                    f"or 'endemic to Z' for unique identification."
                ),
                location=location
            ))

    return issues


def detect_ambiguous_procedure_clozes(
    statement: Statement,
    location: Optional[str],
    *,
    statement_doc=None,
) -> List[ValidationIssue]:
    """
    Detect procedures without indication/timing context.

    Procedure names alone don't specify when/why they're indicated.

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Common medical procedures (use word-boundary patterns to avoid substring false positives)
    procedure_patterns = [
        r'\bct\b',
        r'\bmri\b',
        r'\bct scan\b',
        r'\bmri scan\b',
        r'\bct angiography\b',
        r'\bultrasound\b',
        r'\bx-ray\b',
        r'\bpet scan\b',
        r'\bcolonoscopy\b',
        r'\bendoscopy\b',
        r'\bbronchoscopy\b',
        r'\bbiopsy\b',
        r'\bechocardiogram\b',
        r'\bangiography\b',
    ]

    potential_procedures = []

    if statement_doc is not None:
        entity_index = _build_entity_index(statement_doc)
        for candidate in statement.cloze_candidates:
            label = _match_candidate_entity(candidate, entity_index)
            if label and label in PROCEDURE_ENTITY_LABELS:
                potential_procedures.append(candidate)

    if not potential_procedures:
        for candidate in statement.cloze_candidates:
            # Case-insensitive check
            if any(re.search(pattern, candidate, re.IGNORECASE) for pattern in procedure_patterns):
                potential_procedures.append(candidate)

    if not potential_procedures:
        return issues

    # Check for indication/timing context
    context_indicators = [
        r'\bindicated for\b',
        r'\bused to diagnose\b',
        r'\bfirst-line for\b',
        r'\bgold standard for\b',
        r'\bwithin \d+\s+(hours|days|weeks)\b',
        r'\bafter\b',
        r'\bbefore\b',
        r'\bwhen\b.*\bsuspected\b',
    ]

    has_context = any(
        re.search(pattern, statement.statement, re.IGNORECASE)
        for pattern in context_indicators
    )

    if not has_context:
        for procedure in potential_procedures:
            issues.append(ValidationIssue(
                severity="warning",
                category="ambiguity",
                message=(
                    f"Procedure '{procedure}' lacks indication or timing context. "
                    f"Add context like: 'indicated for X', 'first-line for Y', "
                    f"or 'performed within Z hours' for clarity."
                ),
                location=location
            ))

    return issues


MEDICATION_ENTITY_LABELS = {
    "CHEMICAL",
    "DRUG",
    "PHARMACOLOGICAL_SUBSTANCE",
    "CHEMICAL_SUBSTANCE",
}


ORGANISM_ENTITY_LABELS = {
    "ORGANISM",
    "BACTERIA",
    "VIRUS",
    "PATHOGEN",
    "SPECIES",
}


PROCEDURE_ENTITY_LABELS = {
    "PROCEDURE",
    "TEST",
    "DIAGNOSTIC_PROCEDURE",
    "LAB_TEST",
}


def _normalize_entity_text(text: str) -> str:
    text = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _build_entity_index(doc) -> Dict[str, str]:
    """
    Build a normalized text -> label index for entities in a Doc.
    """
    index: Dict[str, str] = {}
    if doc is None:
        return index

    for ent in doc.ents:
        normalized = _normalize_entity_text(ent.text)
        if normalized:
            index[normalized] = ent.label_

    return index


def _match_candidate_entity(candidate: str, entity_index: Dict[str, str]) -> Optional[str]:
    """
    Match a cloze candidate against entity index, returning the entity label.
    """
    candidate_norm = _normalize_entity_text(candidate)
    if not candidate_norm:
        return None

    if candidate_norm in entity_index:
        return entity_index[candidate_norm]

    for ent_text, label in entity_index.items():
        if candidate_norm in ent_text or ent_text in candidate_norm:
            return label

    return None


def suggest_hint(candidate: str) -> str:
    """
    Recommend parenthetical hint for ambiguous cloze candidate.

    Returns suggested hint format: "(drug)", "(organism)", "(mechanism)", etc.

    Args:
        candidate: Cloze candidate to analyze

    Returns:
        Suggested hint string or empty string if no hint needed
    """
    candidate_lower = candidate.lower()

    # Medication suffixes
    medication_suffixes = ['mab', 'nib', 'pril', 'sartan', 'olol', 'statin', 'mycin']
    if any(candidate_lower.endswith(suffix) for suffix in medication_suffixes):
        return "(drug)"

    # Organism pattern: Capitalized Genus + lowercase species
    if re.match(r'^[A-Z][a-z]+\s+[a-z]+$', candidate):
        return "(organism)"

    # Procedure terms
    procedure_terms = ['CT', 'MRI', 'colonoscopy', 'endoscopy', 'biopsy', 'scan']
    if any(term.lower() in candidate_lower for term in procedure_terms):
        return "(procedure)"

    # Mechanism indicators
    mechanism_terms = ['inhibit', 'block', 'agonist', 'antagonist', 'bind']
    if any(term in candidate_lower for term in mechanism_terms):
        return "(mechanism)"

    return ""


def find_overlapping_pairs(candidates: List[str]) -> List[tuple]:
    """
    Helper to detect overlapping candidate pairs.

    Finds pairs where one candidate is a substring of another.
    Examples:
    - ("asthma", "severe asthma") → overlap
    - ("kidney injury", "acute kidney injury") → overlap

    Args:
        candidates: List of cloze candidates

    Returns:
        List of (candidate1, candidate2) tuples that overlap
    """
    overlapping_pairs = []

    for i, c1 in enumerate(candidates):
        for c2 in candidates[i+1:]:
            # Case-insensitive comparison
            c1_lower = c1.lower()
            c2_lower = c2.lower()

            # Check if one is substring of the other
            if c1_lower in c2_lower or c2_lower in c1_lower:
                # But not if they're identical
                if c1_lower != c2_lower:
                    overlapping_pairs.append((c1, c2))

    return overlapping_pairs
