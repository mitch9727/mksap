"""
Source fidelity validation to detect potential hallucinations.

Uses keyword-based matching to verify statement facts appear in source text.
"""

import re
from typing import List, Optional, Set
from ....infrastructure.models.data_models import Statement
from ....validation.validator import ValidationIssue


# Common medical stopwords to ignore
MEDICAL_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
    'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
    'not', 'no', 'yes', 'if', 'than', 'also', 'other', 'more', 'most',
    'patient', 'patients', 'treatment', 'therapy', 'diagnosis', 'management'
}


def validate_statement_fidelity(
    statement: Statement,
    source_text: str,
    location: Optional[str],
    *,
    statement_doc=None,
    source_doc=None,
) -> List[ValidationIssue]:
    """
    Validate that statement facts are present in source text.

    Args:
        statement: Statement to validate
        source_text: Source text (critique, key_point, or table)
        location: Location string for error reporting

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    if not source_text.strip():
        # Can't validate without source
        issues.append(ValidationIssue(
            severity="info",
            category="hallucination",
            message="Cannot validate fidelity - source text is empty",
            location=location
        ))
        return issues

    # Detect potential hallucination
    issue = detect_potential_hallucination(
        statement.statement,
        source_text,
        location,
        statement_doc=statement_doc,
        source_doc=source_doc,
    )
    if issue:
        issues.append(issue)

    return issues


def detect_potential_hallucination(
    statement: str,
    source_text: str,
    location: Optional[str],
    threshold: float = 0.3,
    *,
    statement_doc=None,
    source_doc=None,
) -> Optional[ValidationIssue]:
    """
    Detect potential hallucination by checking keyword overlap.

    Extracts medical terms from statement and checks how many appear in source.
    Flags if <30% match (default threshold).

    Args:
        statement: Statement text to check
        source_text: Source text that should contain the facts
        location: Location string for error reporting
        threshold: Minimum overlap ratio (default 0.3 = 30%)

    Returns:
        ValidationIssue if potential hallucination, None otherwise
    """
    if statement_doc is not None and source_doc is not None:
        statement_terms = extract_terms_from_doc(statement_doc)
        source_terms = extract_terms_from_doc(source_doc)

        if not statement_terms:
            return None

        matched_terms = statement_terms & source_terms
        missing_terms = statement_terms - source_terms
    else:
        # Normalize both texts
        statement_lower = statement.lower()
        source_lower = source_text.lower()

        # Extract key terms from statement (nouns, medical terms)
        statement_terms = extract_key_terms(statement_lower)

        if not statement_terms:
            # No terms to check
            return None

        # Count how many terms appear in source
        matched_terms = set()
        missing_terms = set()

        for term in statement_terms:
            # Use word boundaries to avoid partial matches
            if re.search(rf'\b{re.escape(term)}\b', source_lower):
                matched_terms.add(term)
            else:
                # Check for partial matches or synonyms
                if fuzzy_match(term, source_lower):
                    matched_terms.add(term)
                else:
                    missing_terms.add(term)

    # Calculate match ratio
    match_ratio = len(matched_terms) / len(statement_terms) if statement_terms else 1.0

    if match_ratio < threshold:
        # Format missing terms for message
        missing_list = ', '.join(sorted(missing_terms)[:5])  # Show up to 5
        if len(missing_terms) > 5:
            missing_list += f", and {len(missing_terms) - 5} more"

        return ValidationIssue(
            severity="warning",
            category="hallucination",
            message=f"Potential hallucination - {int((1-match_ratio)*100)}% of key terms not in source: {missing_list}",
            location=location
        )

    return None


def extract_key_terms(text: str) -> Set[str]:
    """
    Extract key medical terms from text.

    Uses simple heuristics:
    - Words 3+ characters
    - Not in stopword list
    - Capitalized words (likely proper nouns/medications)
    - Medical patterns (drug names, conditions)

    Args:
        text: Text to extract terms from

    Returns:
        Set of key terms
    """
    # Split into words
    words = re.findall(r'\b[a-z]+\b', text.lower())

    key_terms = set()

    for word in words:
        # Skip short words and stopwords
        if len(word) < 3 or word in MEDICAL_STOPWORDS:
            continue

        # Add to key terms
        key_terms.add(word)

    # Also extract medical abbreviations (uppercase words in original text)
    abbreviations = re.findall(r'\b[A-Z]{2,}\b', text)
    for abbrev in abbreviations:
        key_terms.add(abbrev.lower())

    # Extract hyphenated terms (often medical)
    hyphenated = re.findall(r'\b[a-z]+-[a-z]+\b', text.lower())
    for term in hyphenated:
        key_terms.add(term)

    # Extract medical suffixes (-itis, -osis, -emia, etc.)
    medical_suffix_pattern = r'\b\w+(?:itis|osis|emia|pathy|plasia|trophy|sclerosis|stenosis)\b'
    medical_terms = re.findall(medical_suffix_pattern, text.lower())
    for term in medical_terms:
        key_terms.add(term)

    return key_terms


def extract_terms_from_doc(doc) -> Set[str]:
    """
    Extract key terms from a spaCy Doc using lemmas and entities.

    Uses lemma normalization to reduce ad-hoc word list matching.
    """
    if doc is None:
        return set()

    key_terms: Set[str] = set()

    for token in doc:
        if token.is_space or token.is_punct:
            continue

        token_lower = token.text.lower()
        if token.is_stop or token_lower in MEDICAL_STOPWORDS:
            continue

        if token.is_alpha and len(token_lower) >= 3:
            key_terms.add(token.lemma_.lower())
        elif "-" in token_lower and re.search(r"[a-zA-Z]", token_lower):
            key_terms.add(token_lower)

    for ent in doc.ents:
        ent_text = ent.text.strip().lower()
        if ent_text and ent_text not in MEDICAL_STOPWORDS:
            key_terms.add(ent_text)

    return key_terms


def fuzzy_match(term: str, source: str) -> bool:
    """
    Check for fuzzy matches (plurals, verb forms, etc.).

    Args:
        term: Term to search for
        source: Source text to search in

    Returns:
        True if fuzzy match found
    """
    # Check common variations
    variations = [
        term + 's',  # plural
        term + 'es',  # plural
        term + 'd',  # past tense
        term + 'ed',  # past tense
        term + 'ing',  # present participle
        term[:-1] if term.endswith('s') else None,  # singular
        term[:-1] if term.endswith('d') else None,  # base form
        term[:-2] if term.endswith('ed') else None,  # base form
        term[:-3] if term.endswith('ing') else None,  # base form
    ]

    for variation in variations:
        if variation and re.search(rf'\b{re.escape(variation)}\b', source):
            return True

    return False
