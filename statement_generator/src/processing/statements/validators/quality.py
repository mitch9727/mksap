"""
Statement quality validation for flashcard best practices.

Checks for atomicity, vague language, board relevance, and appropriate length.
"""

import re
from typing import List, Optional
from ....infrastructure.models.data_models import Statement
from ....validation.validator import ValidationIssue


def validate_statement_quality(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Run all quality checks on a statement.

    Args:
        statement: Statement to validate
        location: Location string for error reporting

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    issues.extend(check_atomicity(statement.statement, location))
    issues.extend(check_vague_language(statement.statement, location))
    issues.extend(check_patient_specific_language(statement.statement, location))
    issues.extend(check_source_references(statement.statement, location))
    issue = check_board_relevance(statement.statement, location)
    if issue:
        issues.append(issue)
    issue = check_statement_length(statement.statement, location)
    if issue:
        issues.append(issue)

    return issues


def check_atomicity(statement: str, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check if statement contains multiple concepts.

    Flags statements with semicolons, multiple "and" conjunctions, or multi-clause conditionals.

    Args:
        statement: Statement text
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Check for semicolons (always suggests compound sentence)
    if ';' in statement:
        issues.append(ValidationIssue(
            severity="warning",
            category="quality",
            message="Semicolon suggests compound sentence - consider splitting",
            location=location
        ))
        return issues  # Don't check other patterns if semicolon found

    # Check for multiple "and" conjunctions (3+ instances)
    and_count = len(re.findall(r'\band\b', statement, re.IGNORECASE))
    if and_count >= 3:
        issues.append(ValidationIssue(
            severity="warning",
            category="quality",
            message=f"Multiple 'and' conjunctions ({and_count}) suggest compound statement - consider splitting",
            location=location
        ))
        return issues

    # Check for multi-clause conditionals
    # Pattern: if...then...and/or if...then (multiple conditional clauses)
    if re.search(r'\bif\b.*\bthen\b.*\b(and|or)\b.*\bif\b', statement, re.IGNORECASE):
        issues.append(ValidationIssue(
            severity="warning",
            category="quality",
            message="Multi-clause conditional detected - consider splitting",
            location=location
        ))
        return issues

    # Pattern for multi-concept indicators
    # Look for "and" or "or" connecting two clauses with verbs
    multi_concept_patterns = [
        r'\b(and|or)\b.*\b(is|are|causes|include|require|has|have|should)\b',
        r'\balso\b',
    ]

    for pattern in multi_concept_patterns:
        if re.search(pattern, statement, re.IGNORECASE):
            issues.append(ValidationIssue(
                severity="warning",
                category="quality",
                message="Possible multi-concept statement (contains compound structure)",
                location=location
            ))
            break  # Only flag once

    return issues


def check_vague_language(statement: str, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for vague qualifiers that reduce testability.

    Flags: "often", "usually", "may", "sometimes", "rarely", "commonly", "typically"

    Args:
        statement: Statement text
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    vague_terms = [
        "often", "usually", "may", "sometimes", "rarely",
        "commonly", "typically", "generally", "frequently",
        "occasionally", "possibly", "potentially"
    ]

    found_vague = []
    statement_lower = statement.lower()

    for term in vague_terms:
        # Use word boundaries to avoid false positives
        if re.search(rf'\b{term}\b', statement_lower):
            found_vague.append(term)

    if found_vague:
        issues.append(ValidationIssue(
            severity="info",
            category="quality",
            message=f"Vague language detected: {', '.join(found_vague)}",
            location=location
        ))

    return issues


def check_board_relevance(statement: str, location: Optional[str]) -> Optional[ValidationIssue]:
    """
    Check if statement is clinically relevant for board exams.

    Flags pure trivia without clinical context.

    Args:
        statement: Statement text
        location: Location string

    Returns:
        ValidationIssue if trivia detected, None otherwise
    """
    # Patterns that suggest pure trivia
    trivia_patterns = [
        r'is located in',
        r'is a type of',
        r'is also known as',
        r'is derived from',
        r'was discovered',
        r'is named after',
    ]

    for pattern in trivia_patterns:
        if re.search(pattern, statement, re.IGNORECASE):
            # Check if there's clinical context (treatment, diagnosis, prognosis)
            clinical_terms = [
                'treatment', 'therapy', 'diagnosis', 'management', 'prognosis',
                'indication', 'contraindication', 'complication', 'side effect',
                'symptom', 'sign', 'test', 'screening', 'prevention'
            ]

            has_clinical_context = any(
                re.search(rf'\b{term}\b', statement, re.IGNORECASE)
                for term in clinical_terms
            )

            if not has_clinical_context:
                return ValidationIssue(
                    severity="warning",
                    category="quality",
                    message="Possible trivia without clinical context",
                    location=location
                )
            break

    return None


def check_patient_specific_language(statement: str, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for patient-specific language that reduces reusability.

    Flags: "this patient", "this case", "the patient", "in this patient"

    Args:
        statement: Statement text
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    patient_specific_patterns = [
        r'\bthis patient\b',
        r'\bthis case\b',
        r'\bthe patient\b',
        r'\bin this patient\b',
    ]

    found_patterns = []
    statement_lower = statement.lower()

    for pattern in patient_specific_patterns:
        if re.search(pattern, statement_lower):
            # Extract the actual matched text for reporting
            match = re.search(pattern, statement_lower)
            if match:
                found_patterns.append(match.group(0))

    if found_patterns:
        issues.append(ValidationIssue(
            severity="info",
            category="quality",
            message=f"Patient-specific language detected: {', '.join(set(found_patterns))} - consider generalizing",
            location=location
        ))

    return issues


def check_source_references(statement: str, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for source-referential phrasing that should be expressed as general facts.

    Flags references like "this critique", "this question", "the vignette".

    Args:
        statement: Statement text
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    source_patterns = [
        r'\bthis critique\b',
        r'\bthe critique\b',
        r'\bthis question\b',
        r'\bthe question\b',
        r'\bthis vignette\b',
        r'\bthe vignette\b',
        r'\bbased on this critique\b',
        r'\bbased on the critique\b',
        r'\bbased on this question\b',
        r'\bbased on the question\b',
        r'\bin this critique\b',
        r'\bin this question\b',
        r'\bin this vignette\b',
        r'\bthis setting\b',
        r'\bthis scenario\b',
        r'\bthis presentation\b',
        r'\bthese findings\b',
        r'\bthis context\b',
    ]

    found_patterns = []
    statement_lower = statement.lower()

    for pattern in source_patterns:
        match = re.search(pattern, statement_lower)
        if match:
            found_patterns.append(match.group(0))

    if found_patterns:
        issues.append(ValidationIssue(
            severity="info",
            category="quality",
            message=(
                "Source-reference language detected: "
                f"{', '.join(set(found_patterns))} - rewrite as a general clinical fact"
            ),
            location=location
        ))

    return issues


def check_statement_length(statement: str, location: Optional[str]) -> Optional[ValidationIssue]:
    """
    Check if statement is too long for effective flashcard use.

    Warns if >200 characters (slows reviews and reduces retention).

    Args:
        statement: Statement text
        location: Location string

    Returns:
        ValidationIssue if too long, None otherwise
    """
    if len(statement) > 200:
        return ValidationIssue(
            severity="warning",
            category="quality",
            message=f"Long statements slow reviews and reduce retention ({len(statement)} chars) - consider splitting",
            location=location
        )

    return None
